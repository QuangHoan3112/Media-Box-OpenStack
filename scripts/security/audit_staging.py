#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
from io import BytesIO
import base64
import re
import tarfile

ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_DIRS = {
    ".git", ".venv", "venv",
    "__pycache__", "node_modules",
    ".pytest_cache"
}

PATTERNS = {
    "PRIVATE_KEY_MATERIAL": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        re.I
    ),
    "POSSIBLE_ACCESS_TOKEN": re.compile(
        r"\b(?:ghp_|gho_|ghu_|ghs_|github_pat_|"
        r"AKIA|ASIA|xoxb-)[A-Za-z0-9_-]{12,}"
    ),
    "EMBEDDED_URL_CREDENTIALS": re.compile(
        r"https?://[^\s/'\"]+:[^\s@/'\"]+@",
        re.I
    ),
    "POTENTIAL_LITERAL_SECRET": re.compile(
        r"""(?i)\b(?:password|passwd|client_secret|
        jwt_secret|api_key|access_token|auth_token)
        \s*[:=]\s*
        (?:"[^"\n]{4,}"|'[^'\n]{4,}')""",
        re.X
    ),
    "POSSIBLE_SIGNED_URL": re.compile(
        r"https?://[^\s'\"<>]{0,600}"
        r"[?&](?:token|signature|auth|key)=",
        re.I
    )
}

findings = []
scanned = 0
bundle_status = "NOT_FOUND"

def audit_bytes(label, raw):
    global scanned
    scanned += 1

    text = raw.decode("utf-8", errors="replace")
    for category, pattern in PATTERNS.items():
        if pattern.search(text):
            findings.append((label, category))

def audit_bundle(bundle):
    global bundle_status

    try:
        encoded = b"".join(bundle.read_bytes().split())
        raw = base64.b64decode(encoded, validate=True)

        with tarfile.open(fileobj=BytesIO(raw), mode="r:*") as tf:
            members = tf.getmembers()
            names = set()

            for member in members:
                name = member.name
                parts = Path(name).parts

                if (
                    name in names
                    or name.startswith("/")
                    or ".." in parts
                    or member.issym()
                    or member.islnk()
                ):
                    findings.append((
                        "infrastructure/heat/app-bundle.b64",
                        "UNSAFE_ARCHIVE_ENTRY"
                    ))
                    continue

                names.add(name)

                if not member.isfile():
                    continue

                if member.size > 2_000_000:
                    findings.append((
                        name,
                        "OVERSIZED_BUNDLE_MEMBER"
                    ))
                    continue

                stream = tf.extractfile(member)
                if stream is None:
                    continue

                data = stream.read()

                audit_bytes(
                    "BUNDLE:" + name,
                    data
                )

                source = ROOT / "app/mediabox" / name

                if not source.is_file():
                    findings.append((
                        "BUNDLE:" + name,
                        "SOURCE_FILE_MISSING"
                    ))
                elif source.read_bytes() != data:
                    findings.append((
                        "BUNDLE:" + name,
                        "SOURCE_CONTENT_MISMATCH"
                    ))

        bundle_status = "DECODED_AND_SCANNED"

    except Exception:
        bundle_status = "INVALID_OR_UNREADABLE"
        findings.append((
            "infrastructure/heat/app-bundle.b64",
            "BUNDLE_DECODE_FAILED"
        ))

print("===== 1. STAGING FILE AUDIT =====")

for path in sorted(ROOT.rglob("*")):
    if any(p in EXCLUDED_DIRS for p in path.parts):
        continue

    if path.is_symlink():
        findings.append((
            str(path.relative_to(ROOT)),
            "SYMLINK_REQUIRES_REVIEW"
        ))
        continue

    if not path.is_file():
        continue

    rel = str(path.relative_to(ROOT))

    if rel == "scripts/security/audit_staging.py":
        continue

    if rel == "infrastructure/heat/app-bundle.b64":
        continue

    if rel.startswith("scripts/diagnostics/"):
        findings.append((
            rel,
            "DIAGNOSTIC_SCRIPT_REQUIRES_REVIEW"
        ))

    try:
        if path.stat().st_size > 2_000_000:
            findings.append((rel, "LARGE_FILE_REQUIRES_REVIEW"))
            continue

        if path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".gif",
            ".pdf", ".gz", ".zip", ".sqlite"
        }:
            continue

        audit_bytes(rel, path.read_bytes())
    except OSError:
        findings.append((rel, "UNREADABLE_FILE"))

print("FILES_SCANNED:", scanned)

print("\n===== 2. HEAT BUNDLE AUDIT =====")

bundle = ROOT / "infrastructure/heat/app-bundle.b64"

if bundle.is_file():
    audit_bundle(bundle)

print("BUNDLE_STATUS:", bundle_status)

print("\n===== 3. FINDINGS =====")

for path, category in findings:
    print(f"{category}: {path}")

print("\n===== 4. SUMMARY =====")

counts = Counter(
    category for _, category in findings
)

for category, count in sorted(counts.items()):
    print(f"{category}: {count}")

print("TOTAL_FINDINGS:", len(findings))

if findings:
    print("SECURITY_STATUS: REVIEW_REQUIRED")
else:
    print("SECURITY_STATUS: NO_PATTERN_MATCHES")
    print("NOTE: manual security review still required")

print("\n===== SECURITY AUDIT COMPLETE =====")
print("SECRET_VALUES_PRINTED: NO")
print("FILES_MODIFIED_BY_AUDIT: NO")
