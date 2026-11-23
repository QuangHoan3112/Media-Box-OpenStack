#!/usr/bin/env python3
"""Rebuild MediaBox Heat bundle from canonical application source."""

from pathlib import Path
from io import BytesIO
import base64
import gzip
import hashlib
import os
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "app/mediabox"
OUTPUT = ROOT / "infrastructure/heat/app-bundle.b64"

FILES = [
    "app/__init__.py",
    "app/auth.py",
    "app/db.py",
    "app/main.py",
    "app/media.py",
    "app/permissions.py",
    "app/playback.py",
    "app/static/index.html",
    "app/swift_storage.py",
    "app/upload.py",
    "requirements.txt",
]

print("===== PORTABLE HEAT BUNDLE BUILD =====")
print("REPOSITORY:", ROOT)

source_files = {}

for name in FILES:
    path = SOURCE / name

    if not path.is_file() or path.is_symlink():
        raise SystemExit("MISSING_OR_UNSAFE_SOURCE: " + name)

    source_files[name] = path.read_bytes()

print("SOURCE_FILES:", len(source_files))

tar_buffer = BytesIO()

with tarfile.open(
    fileobj=tar_buffer,
    mode="w",
    format=tarfile.GNU_FORMAT
) as archive:
    for name, content in source_files.items():
        info = tarfile.TarInfo(name)
        info.size = len(content)
        info.mode = 0o644
        info.uid = 0
        info.gid = 0
        info.mtime = 0

        archive.addfile(info, BytesIO(content))

gzip_buffer = BytesIO()

with gzip.GzipFile(
    filename="",
    fileobj=gzip_buffer,
    mode="wb",
    mtime=0,
    compresslevel=9
) as compressed:
    compressed.write(tar_buffer.getvalue())

bundle_data = gzip_buffer.getvalue()

# Verify every generated archive member.
with tarfile.open(
    fileobj=BytesIO(bundle_data),
    mode="r:gz"
) as archive:
    members = archive.getmembers()
    recovered = {}

    for member in members:
        if not member.isfile():
            raise SystemExit("UNEXPECTED_ARCHIVE_ENTRY")

        if member.name in recovered:
            raise SystemExit("DUPLICATE_ARCHIVE_MEMBER")

        stream = archive.extractfile(member)

        if stream is None:
            raise SystemExit("UNREADABLE_ARCHIVE_MEMBER")

        recovered[member.name] = stream.read()

if recovered != source_files:
    raise SystemExit("BUNDLE_CONTENT_MISMATCH")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
encoded = base64.b64encode(bundle_data) + b"\n"

fd, temporary = tempfile.mkstemp(
    prefix=".mediabox-bundle-",
    dir=str(OUTPUT.parent)
)

try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)

    os.chmod(temporary, 0o600)
    os.replace(temporary, OUTPUT)

finally:
    if os.path.exists(temporary):
        os.unlink(temporary)

print("BUNDLE_FORMAT: TAR.GZ + BASE64")
print("CONTENT_VERIFIED: YES")
print("OUTPUT:", OUTPUT)
print("SHA256:", hashlib.sha256(encoded).hexdigest())
print("===== PORTABLE BUILD COMPLETE =====")
