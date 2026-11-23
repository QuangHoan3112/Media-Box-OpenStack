from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.db import get_connection


router = APIRouter(
    prefix="/api/media",
    tags=["Media Permissions"],
)


class PermissionRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    can_view: bool = True
    can_download: bool = False


def require_manager(cur, media_id, user):
    cur.execute(
        """
        SELECT id, owner_id
        FROM media_files
        WHERE id = %s
        """,
        (media_id,),
    )

    media = cur.fetchone()

    if not media:
        raise HTTPException(
            status_code=404,
            detail="Media not found",
        )

    if (
        media["owner_id"] != user["id"]
        and user["role"] != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only owner or admin can manage permissions",
        )

    return media


@router.get("/{media_id}/permissions")
def list_permissions(
    media_id: UUID,
    user=Depends(get_current_user),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            require_manager(cur, media_id, user)

            cur.execute(
                """
                SELECT
                    u.username,
                    p.can_view,
                    p.can_download,
                    p.created_at
                FROM media_permissions p
                JOIN app_users u ON u.id = p.user_id
                WHERE p.media_id = %s
                ORDER BY u.username
                """,
                (media_id,),
            )

            permissions = cur.fetchall()

    return {
        "media_id": media_id,
        "permissions": permissions,
    }


@router.post("/{media_id}/permissions")
def grant_permission(
    media_id: UUID,
    data: PermissionRequest,
    user=Depends(get_current_user),
):
    if data.can_download and not data.can_view:
        raise HTTPException(
            status_code=400,
            detail="Download permission requires view permission",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            media = require_manager(cur, media_id, user)

            cur.execute(
                """
                SELECT id, username
                FROM app_users
                WHERE username = %s AND is_active = TRUE
                """,
                (data.username,),
            )

            target = cur.fetchone()

            if not target:
                raise HTTPException(
                    status_code=404,
                    detail="Active user not found",
                )

            if target["id"] == media["owner_id"]:
                raise HTTPException(
                    status_code=400,
                    detail="Owner already has full access",
                )

            cur.execute(
                """
                INSERT INTO media_permissions
                    (media_id, user_id, can_view, can_download)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (media_id, user_id)
                DO UPDATE SET
                    can_view = EXCLUDED.can_view,
                    can_download = EXCLUDED.can_download
                RETURNING can_view, can_download
                """,
                (
                    media_id,
                    target["id"],
                    data.can_view,
                    data.can_download,
                ),
            )

            result = cur.fetchone()

    return {
        "message": "Permission saved",
        "media_id": media_id,
        "username": data.username,
        **result,
    }


@router.delete("/{media_id}/permissions/{username}")
def revoke_permission(
    media_id: UUID,
    username: str,
    user=Depends(get_current_user),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            require_manager(cur, media_id, user)

            cur.execute(
                """
                DELETE FROM media_permissions p
                USING app_users u
                WHERE p.user_id = u.id
                  AND p.media_id = %s
                  AND u.username = %s
                RETURNING p.user_id
                """,
                (media_id, username),
            )

            deleted = cur.fetchone()

            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Permission not found",
                )

    return {
        "message": "Permission revoked",
        "media_id": media_id,
        "username": username,
    }
