import getpass
import json
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4

from app.db import get_connection


BASE = "http://127.0.0.1:18000"


def api(method, path, token=None, body=None):
    headers = {}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def login(username):
    password = getpass.getpass(f"Password for {username}: ")

    data = urllib.parse.urlencode({
        "username": username,
        "password": password,
    }).encode()

    req = urllib.request.Request(
        BASE + "/api/auth/login",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as res:
        return json.load(res)["access_token"]


# Check database permissions before creating test data.
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                has_table_privilege(
                    'media_files', 'INSERT'
                ) AS media_insert,
                has_table_privilege(
                    'media_files', 'DELETE'
                ) AS media_delete,
                has_table_privilege(
                    'media_permissions', 'INSERT'
                ) AS permission_insert,
                has_table_privilege(
                    'media_permissions', 'UPDATE'
                ) AS permission_update,
                has_table_privilege(
                    'media_permissions', 'DELETE'
                ) AS permission_delete
        """)
        privileges = cur.fetchone()

        if not all(privileges.values()):
            raise SystemExit(
                f"Missing database privileges: {privileges}"
            )

        cur.execute(
            """
            SELECT id
            FROM app_users
            WHERE username = %s AND is_active = TRUE
            """,
            ("demo_owner",),
        )
        owner = cur.fetchone()

        if owner is None:
            raise SystemExit("Active demo_owner not found")

        owner_id = owner["id"]


owner_token = login("demo_owner")
viewer_token = login("demo_viewer")
print("\n[1] LOGIN SUCCESS")

test_id = uuid4()
object_key = f"__tests__/permissions/{test_id}"
path = f"/api/media/{test_id}"
perm_path = path + "/permissions"

try:
    # Metadata only: no file is uploaded to Swift.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO media_files (
                    id,
                    owner_id,
                    title,
                    original_filename,
                    media_type,
                    content_type,
                    size_bytes,
                    swift_object_key,
                    is_public
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                """,
                (
                    test_id,
                    owner_id,
                    "Permission smoke test",
                    "permission-test.txt",
                    "document",
                    "text/plain",
                    0,
                    object_key,
                ),
            )

    print("[2] TEMPORARY MEDIA CREATED")

    code, result = api("GET", path, viewer_token)
    assert code == 404, (code, result)
    print("[3] VIEWER BEFORE GRANT: 404")

    code, result = api(
        "POST",
        perm_path,
        owner_token,
        {
            "username": "demo_viewer",
            "can_view": True,
            "can_download": False,
        },
    )
    assert code == 200, (code, result)
    print("[4] GRANT VIEW: 200")

    code, result = api("GET", path, viewer_token)
    assert code == 200, (code, result)
    assert result["can_download"] is False
    print("[5] VIEWER CAN VIEW: 200")

    # Viewer must not be allowed to manage permissions.
    code, result = api(
        "POST",
        perm_path,
        viewer_token,
        {
            "username": "demo_owner",
            "can_view": True,
            "can_download": True,
        },
    )
    assert code == 403, (code, result)
    print("[6] VIEWER CANNOT GRANT: 403")

    code, result = api(
        "POST",
        perm_path,
        owner_token,
        {
            "username": "demo_viewer",
            "can_view": True,
            "can_download": True,
        },
    )
    assert code == 200, (code, result)

    code, result = api("GET", path, viewer_token)
    assert code == 200, (code, result)
    assert result["can_download"] is True
    print("[7] DOWNLOAD PERMISSION: True")

    code, result = api(
        "DELETE",
        perm_path + "/demo_viewer",
        owner_token,
    )
    assert code == 200, (code, result)
    print("[8] REVOKE PERMISSION: 200")

    code, result = api("GET", path, viewer_token)
    assert code == 404, (code, result)
    print("[9] VIEWER AFTER REVOKE: 404")

    print("\nMEDIABOX PERMISSION TEST SUCCESS")

finally:
    # Remove only the exact metadata record created by this test.
    # Related test permissions are removed via ON DELETE CASCADE.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM media_files
                WHERE id = %s
                  AND owner_id = %s
                  AND swift_object_key = %s
                RETURNING id
                """,
                (test_id, owner_id, object_key),
            )
            deleted = cur.fetchone()

    if deleted:
        print("TEST DATA CLEANUP SUCCESS")
    else:
        print("NO TEST DATA REQUIRED CLEANUP")
