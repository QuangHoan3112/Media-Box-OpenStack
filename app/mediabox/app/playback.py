import logging
import re
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from swiftclient.exceptions import ClientException

from app.auth import get_current_user
from app.db import get_connection
from app.swift_storage import get_swift_connection


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["Media Playback"])

CHUNK_SIZE = 64 * 1024


def get_authorized_media(media_id, user, require_download=False):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.id,
                    m.original_filename,
                    m.content_type,
                    m.size_bytes,
                    m.swift_container,
                    m.swift_object_key,
                    (
                        %(is_admin)s
                        OR m.owner_id = %(user_id)s
                        OR m.is_public
                        OR COALESCE(p.can_view, FALSE)
                    ) AS can_view,
                    (
                        %(is_admin)s
                        OR m.owner_id = %(user_id)s
                        OR (
                            COALESCE(p.can_view, FALSE)
                            AND COALESCE(p.can_download, FALSE)
                        )
                    ) AS can_download
                FROM media_files m
                LEFT JOIN media_permissions p
                    ON p.media_id = m.id
                    AND p.user_id = %(user_id)s
                WHERE m.id = %(media_id)s
                """,
                {
                    "media_id": media_id,
                    "user_id": user["id"],
                    "is_admin": user["role"] == "admin",
                },
            )
            media = cur.fetchone()

    if not media or not media["can_view"]:
        raise HTTPException(404, "Media not found")

    if require_download and not media["can_download"]:
        raise HTTPException(403, "Download permission denied")

    return media


def stream_from_swift(media, download=False, byte_range=None):
    if byte_range and not re.fullmatch(
        r"bytes=(?:[0-9]+-[0-9]*|-[0-9]+)",
        byte_range,
    ):
        raise HTTPException(416, "Invalid Range header")

    try:
        swift = get_swift_connection()

        request_headers = {}
        if byte_range:
            request_headers["Range"] = byte_range

        swift_headers, body = swift.get_object(
            media["swift_container"],
            media["swift_object_key"],
            resp_chunk_size=CHUNK_SIZE,
            headers=request_headers,
        )

    except ClientException as exc:
        if exc.http_status == 404:
            raise HTTPException(404, "Media object not found") from exc
        if exc.http_status == 416:
            raise HTTPException(416, "Range not satisfiable") from exc

        logger.exception("Swift read failed")
        raise HTTPException(502, "Storage service error") from exc

    except Exception as exc:
        logger.exception("Swift connection failed")
        raise HTTPException(502, "Storage service error") from exc

    def chunks():
        try:
            for chunk in body:
                yield chunk
        finally:
            close = getattr(body, "close", None)
            if callable(close):
                close()

    filename = quote(
        media["original_filename"],
        safe="",
    )

    disposition = "attachment" if download else "inline"

    response_headers = {
        "Content-Disposition": (
            f"{disposition}; filename=\"media\"; "
            f"filename*=UTF-8''{filename}"
        ),
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    }

    if "content-length" in swift_headers:
        response_headers["Content-Length"] = (
            swift_headers["content-length"]
        )

    if "content-range" in swift_headers:
        response_headers["Content-Range"] = (
            swift_headers["content-range"]
        )

    status_code = (
        206 if "content-range" in swift_headers else 200
    )

    return StreamingResponse(
        chunks(),
        status_code=status_code,
        media_type=media["content_type"],
        headers=response_headers,
    )


@router.get("/{media_id}/stream")
def stream_media(
    media_id: UUID,
    range_header: str | None = Header(
        default=None,
        alias="Range",
    ),
    user=Depends(get_current_user),
):
    media = get_authorized_media(media_id, user)

    return stream_from_swift(
        media,
        download=False,
        byte_range=range_header,
    )


@router.get("/{media_id}/download")
def download_media(
    media_id: UUID,
    user=Depends(get_current_user),
):
    media = get_authorized_media(
        media_id,
        user,
        require_download=True,
    )

    return stream_from_swift(media, download=True)
