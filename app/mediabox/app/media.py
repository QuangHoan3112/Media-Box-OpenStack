from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user
from app.db import get_connection


router = APIRouter(prefix="/api/media", tags=["Media"])


MEDIA_QUERY = """
SELECT
    m.id,
    m.owner_id,
    m.title,
    m.description,
    m.original_filename,
    m.media_type,
    m.content_type,
    m.size_bytes,
    m.is_public,
    m.created_at,

    (m.owner_id = %(user_id)s) AS is_owner,

    (
        %(is_admin)s
        OR m.owner_id = %(user_id)s
        OR (
            COALESCE(p.can_view, FALSE)
            AND COALESCE(p.can_download, FALSE)
        )
    ) AS can_download

FROM media_files AS m

LEFT JOIN media_permissions AS p
    ON p.media_id = m.id
    AND p.user_id = %(user_id)s

WHERE (
    %(is_admin)s
    OR m.owner_id = %(user_id)s
    OR m.is_public = TRUE
    OR COALESCE(p.can_view, FALSE)
)
"""


def access_params(user):
    return {
        "user_id": user["id"],
        "is_admin": user["role"] == "admin",
    }


@router.get("")
def list_media(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
):
    params = access_params(user)
    params.update({"limit": limit, "offset": offset})

    query = MEDIA_QUERY + """
        ORDER BY m.created_at DESC, m.id
        LIMIT %(limit)s OFFSET %(offset)s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            files = cur.fetchall()

    return {
        "items": files,
        "limit": limit,
        "offset": offset,
        "returned": len(files),
    }


@router.get("/{media_id}")
def get_media(
    media_id: UUID,
    user=Depends(get_current_user),
):
    params = access_params(user)
    params["media_id"] = media_id

    query = MEDIA_QUERY + """
        AND m.id = %(media_id)s
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            media = cur.fetchone()

    if media is None:
        raise HTTPException(
            status_code=404,
            detail="Media not found",
        )

    return media
