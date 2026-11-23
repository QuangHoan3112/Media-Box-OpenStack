# MediaBox System Architecture

## Application Layer

The MediaBox backend is based on FastAPI.

The canonical source is located in:

`app/mediabox/app/`

Main modules:

| Module | Responsibility |
|---|---|
| main.py | API entry point |
| auth.py | User authentication |
| db.py | PostgreSQL connectivity |
| media.py | Media metadata operations |
| upload.py | Media uploads |
| playback.py | Media playback endpoints |
| permissions.py | Media authorization |
| swift_storage.py | Swift integration |

The web interface is stored in:

`app/mediabox/app/static/index.html`

The verified web route is `/app`.

## Infrastructure Layer

### Nova

The observed environment included two fixed
application instances, one database instance and
two application instances created through Heat.

### Neutron

- External network: public
- External subnet: 192.168.57.0/24
- Private network: private
- Private subnet: 10.20.0.0/24
- Router: mediabox-router
- SNAT: enabled

### Octavia

- Load balancer: mediabox-lb
- VIP: 10.20.0.90
- Listener: HTTP 8000
- Pool: mediabox-app-pool
- Algorithm: ROUND_ROBIN
- Health check: GET /health

Four members reported ONLINE on 2026-11-22.

### Swift

Object container: mediabox-media.

The container held uploaded objects during testing.
Actual user objects are excluded from the repository.

### Cinder and PostgreSQL

Database VM: mediabox-db.

Database private IP: 10.20.0.11.

Cinder volume: mediabox-db-data, 5 GiB.

OpenStack reported the volume attached at /dev/vdb.
The guest filesystem mount and PostgreSQL data
directory have not been independently verified.

### Keystone

Provides OpenStack identity and service catalog
functionality. Credentials are excluded from Git.

### Heat

The stack mediabox-autoscale was reported as
UPDATE_COMPLETE.

A manual scale-out demonstration was performed.
The template and source bundle are documented in
infrastructure/heat/.

### Gnocchi and Aodh

Telemetry resources and CPU alarms were observed.

CPU HIGH was disabled, while CPU LOW was enabled
at the time of the final inventory.

Aodh-to-Heat automatic scaling is not fully verified.

## Architecture Limitations

The original lab contains environment-specific
network addresses, storage devices and credentials.

The repository preserves verified source and
configuration examples, but is not a complete
machine image or full disaster-recovery backup.
