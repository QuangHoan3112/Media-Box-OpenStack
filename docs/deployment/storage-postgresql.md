# MediaBox Storage and PostgreSQL

## 1. Swift Object Storage

Verified container: `mediabox-media`.

The application stores uploaded media in Swift.

Actual uploaded user files are not included in this repository.

## 2. Cinder Block Storage

Verified database volume:

- Name: `mediabox-db-data`
- Size: 5 GiB
- Status: `in-use`
- VM: `mediabox-db`
- Reported device: `/dev/vdb`
- Compute host: `compute-b`

The database VM has private IP `10.20.0.11`.

Volume attachment has been verified through OpenStack.
Filesystem mount point and PostgreSQL data directory
still require verification inside the database VM.

## 3. PostgreSQL

The MediaBox application references these settings:

- MEDIABOX_DB_HOST
- MEDIABOX_DB_PORT
- MEDIABOX_DB_PASSWORD_FILE

The actual database password file must never be committed.

The following details require verification:

- PostgreSQL database name
- Database user name
- Tables and columns
- Migration or initialization scripts
- Database data directory
- Cinder filesystem mount point
- Persistence after application restart

## 4. Application Storage Configuration

The application also references:

- MEDIABOX_SWIFT_URL
- MEDIABOX_KEYSTONE_URL
- MEDIABOX_SWIFT_PROJECT_ID
- MEDIABOX_SWIFT_CREDENTIAL_FILE
- MEDIABOX_JWT_SECRET_FILE

Only environment variable names belong in documentation.
Actual credentials must remain outside the repository.

## 5. Security

Do not commit:

- PostgreSQL passwords
- Swift application credentials
- JWT signing secrets
- Real user records
- Database dumps
- Uploaded media belonging to users

## 6. Deployment Status

Swift container: verified.
Cinder database volume attachment: verified.
PostgreSQL internal schema: pending verification.

The storage creation script does not attach, format,
mount or migrate database volumes.
