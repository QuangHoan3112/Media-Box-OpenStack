# MediaBox PostgreSQL Data Model

## Verification Status

This document describes database tables and columns
identified from the MediaBox application source code.

It is not a complete PostgreSQL schema dump.

## 1. app_users

Purpose: Application user management.

Referenced by:
- auth.py
- permissions.py

Column definitions:
- Not yet verified from the database.

## 2. media_files

Purpose: Media metadata stored in PostgreSQL.

Columns referenced by INSERT statements:
- id
- owner_id
- title
- description
- original_filename
- media_type
- content_type
- size_bytes
- swift_container
- swift_object_key
- is_public

Referenced by:
- media.py
- upload.py
- playback.py
- permissions.py

Media binary content is stored separately in Swift.

## 3. media_permissions

Purpose: Per-user media access permissions.

Columns referenced by INSERT statements:
- media_id
- user_id
- can_view
- can_download

Referenced by:
- permissions.py
- media.py
- playback.py

## Infrastructure

Database VM: mediabox-db
Observed private IP: 10.20.0.11

Cinder volume: mediabox-db-data
Volume size: 5 GiB
Reported attachment device: /dev/vdb

The actual PostgreSQL data directory and
filesystem mount point are not yet verified.

## Database Configuration

Application configuration variables:

- MEDIABOX_DB_HOST
- MEDIABOX_DB_PORT
- MEDIABOX_DB_PASSWORD_FILE

Never commit actual password files or user records.

## Pending Verification

- Complete table definitions
- Data types and default values
- Primary and foreign keys
- Indexes and constraints
- PostgreSQL initialization procedure
- Actual Cinder filesystem mount
- Database backup and restore procedure

No schema.sql is supplied until the real schema
can be verified or reliably reconstructed.
