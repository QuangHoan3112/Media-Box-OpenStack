import logging
import mimetypes
import tempfile
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.auth import get_current_user
from app.db import get_connection
from app.swift_storage import (
    SWIFT_CONTAINER,
    get_swift_connection,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/media",
    tags=["Media Upload"],
)

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp4": "video",
    ".webm": "video",
    ".mov": "video",
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".m4a": "audio",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".webp": "image",
    ".pdf": "document",
    ".txt": "document",
    ".docx": "document",
}


def clean_filename(filename):
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    name = filename.replace("\\", "/").split("/")[-1]
    name = "".join(
        c for c in name
        if c.isprintable() and c not in "/\\"
    ).strip()

    if not name or name in (".", ".."):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    # PostgreSQL original_filename is varchar(255).
    if len(name) > 255:
        raise HTTPException(
            status_code=400,
            detail="Filename is too long",
        )

    return name


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_media(
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=255),
    description: str = Form(default=""),
    is_public: bool = Form(default=False),
    user=Depends(get_current_user),
):
    filename = clean_filename(file.filename)

    extension = PurePosixPath(filename).suffix.lower()

    media_type = ALLOWED_EXTENSIONS.get(extension)

    if not media_type:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file extension",
        )

    content_type = (
        mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    media_id = uuid4()

    object_key = (
        f"uploads/{user['id']}/"
        f"{media_id.hex}/{filename}"
    )

    size = 0

    # Stage the file on disk with a strict application limit.
    with tempfile.TemporaryFile(mode="w+b") as temp:
        while True:
            chunk = file.file.read(1024 * 1024)

            if not chunk:
                break

            size += len(chunk)

            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="File exceeds 100 MB limit",
                )

            temp.write(chunk)

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file is not allowed",
            )

        temp.seek(0)

        try:
            swift = get_swift_connection()

            swift.put_object(
                SWIFT_CONTAINER,
                object_key,
                contents=temp,
                content_length=size,
                content_type=content_type,
            )

        except Exception as exc:
            logger.exception("Swift upload failed")

            # Best-effort cleanup in case the PUT partially succeeded.
            if "swift" in locals():
                try:
                    swift.delete_object(
                        SWIFT_CONTAINER,
                        object_key,
                    )
                except Exception:
                    logger.warning(
                        "Swift upload cleanup could not be confirmed"
                    )

            raise HTTPException(
                status_code=502,
                detail="Swift upload failed",
            ) from exc

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO media_files (
                        id,
                        owner_id,
                        title,
                        description,
                        original_filename,
                        media_type,
                        content_type,
                        size_bytes,
                        swift_container,
                        swift_object_key,
                        is_public
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING
                        id,
                        owner_id,
                        title,
                        media_type,
                        size_bytes,
                        is_public,
                        created_at
                    """,
                    (
                        media_id,
                        user["id"],
                        title,
                        description,
                        filename,
                        media_type,
                        content_type,
                        size,
                        SWIFT_CONTAINER,
                        object_key,
                        is_public,
                    ),
                )

                result = cur.fetchone()

        return {
            "message": "Media uploaded successfully",
            "media": result,
        }

    except Exception as exc:
        logger.exception("Database metadata insertion failed")

        # Compensating action: remove uploaded object if DB fails.
        try:
            swift.delete_object(
                SWIFT_CONTAINER,
                object_key,
            )

        except Exception:
            logger.exception(
                "Orphaned Swift object may require cleanup: %s",
                object_key,
            )

        raise HTTPException(
            status_code=500,
            detail="Could not save media metadata",
        ) from exc
