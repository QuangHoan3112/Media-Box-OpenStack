import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def get_connection():
    password_file = Path(
        os.getenv(
            "MEDIABOX_DB_PASSWORD_FILE",
            str(Path.home() / ".config/mediabox/pg_app_password"),
        )
    )

    password = password_file.read_text().rstrip("\r\n")

    return psycopg.connect(
        host=os.getenv("MEDIABOX_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("MEDIABOX_DB_PORT", "15432")),
        dbname="mediabox",
        user="mediabox_app",
        password=password,
        connect_timeout=5,
        row_factory=dict_row,
    )
