# MediaBox Identity, Monitoring and Auto Scaling

## 1. Keystone

The OpenStack service catalog contains 12 services:

- Placement
- Gnocchi
- Cinder
- Neutron
- Nova
- Aodh
- Keystone
- Swift
- Heat CFN
- Octavia
- Glance
- Heat

There are 13 registered roles, including:

- admin
- member
- reader
- service
- heat_stack_owner
- heat_stack_user
- swiftoperator

No authentication tokens, passwords or application
credentials are stored in this repository.

## 2. Gnocchi

The resource inventory returned 21 records.

Observed resource types include:

- instance
- instance_disk
- instance_network_interface
- volume

The inventory confirms telemetry resources exist.
CPU metric values and retention policies have not
yet been independently verified.

## 3. Aodh

Two CPU alarms were verified on 2026-11-22.

### mediabox-cpu-high

- Type: gnocchi_aggregation_by_resources_threshold
- State: ok
- Enabled: false
- Repeat actions: false
- Alarm action count: 1

### mediabox-cpu-low

- Type: gnocchi_aggregation_by_resources_threshold
- State: alarm
- Enabled: true
- Repeat actions: false
- Alarm action count: 0

Thresholds, aggregation methods and resource
queries require additional inspection.

Actual alarm action URLs must never be committed.

## 4. Heat

Stack: mediabox-autoscale
Observed status: UPDATE_COMPLETE

Manual scale-out was previously demonstrated.

Fully automatic Aodh-triggered scale-out and
scale-in have not been verified end-to-end.

## 5. Deployment and Security Notes

Do not copy:

- Application credentials
- Keystone tokens
- Signed Heat signal URLs
- Aodh webhook URLs
- Heat private parameters
- Password and JWT secret files

## 6. Verification Status

Keystone catalog and roles: verified.
Gnocchi resource inventory: verified.
Aodh alarm states and action counts: verified.
Heat stack update status: verified.

Automatic scaling integration: partially verified.
