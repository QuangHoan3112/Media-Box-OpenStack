import json
import os
from pathlib import Path

from keystoneauth1.identity import v3
from keystoneauth1 import session
from swiftclient.client import Connection


PROJECT_ID = os.getenv(
    "MEDIABOX_SWIFT_PROJECT_ID",
    "f9fabf9d5476459ca91cf76bc0614004",
)

SWIFT_CONTAINER = "mediabox-media"

SWIFT_URL = os.getenv(
    "MEDIABOX_SWIFT_URL",
    f"http://192.168.56.10:8081/v1/AUTH_{PROJECT_ID}",
)

KEYSTONE_URL = os.getenv(
    "MEDIABOX_KEYSTONE_URL",
    "http://192.168.56.20:5000/v3",
)


def get_swift_connection():
    credential_file = Path(
        os.getenv(
            "MEDIABOX_SWIFT_CREDENTIAL_FILE",
            str(
                Path.home()
                / ".config/mediabox/swift_appcred.json"
            ),
        )
    )

    with credential_file.open() as f:
        raw = json.load(f)

    cred = {
        str(key).lower(): value
        for key, value in raw.items()
    }

    auth = v3.ApplicationCredential(
        auth_url=KEYSTONE_URL,
        application_credential_id=cred["id"],
        application_credential_secret=cred["secret"],
    )

    auth_session = session.Session(auth=auth)
    token = auth_session.get_token()

    return Connection(
        preauthurl=SWIFT_URL,
        preauthtoken=token,
        retries=1,
        timeout=15,
    )
