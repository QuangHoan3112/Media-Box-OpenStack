# MediaBox Redeployment Guide

## Status

This is a technical redeployment guide.

The scripts were checked in dry-run mode on the
original lab. A fresh-cloud end-to-end deployment
has not yet been demonstrated.

## 1. Prerequisites

A working OpenStack environment with the necessary
services, permissions, images, flavors, networking,
and storage capacity.

Required services may include:

- Keystone
- Nova
- Neutron
- Glance
- Cinder
- Swift
- Heat
- Octavia
- Gnocchi and Aodh, for monitoring

Kolla-Ansible installation and the original
multi-node configuration are not reproduced by
the scripts in this repository.

## 2. Configure OpenStackClient

Install the OpenStackClient packages appropriate
for the target cloud.

Keep clouds.yaml outside the repository.

Verify your cloud context:

```bash
openstack token issue
openstack service list
```

Never commit the resulting token or credentials.

## 3. Prepare Networking

Review:

`infrastructure/neutron/network.env.example`

Provider networks and physical network mappings
must be configured by the cloud administrator.

Preview network deployment:

```bash
bash infrastructure/neutron/create_network.sh --dry-run
```

Preview security groups:

```bash
bash infrastructure/neutron/create_security_groups.sh --dry-run
```

The scripts do not provision Octavia's internal
management network.

## 4. Prepare Storage

Review:

`infrastructure/storage/storage.env.example`

Preview:

```bash
bash infrastructure/storage/create_storage.sh --dry-run
```

This step covers a Swift container and Cinder volume.

It does not:

- Create the database VM
- Attach a volume
- Partition or format a filesystem
- Install PostgreSQL
- Initialize database tables
- Restore existing data

These procedures require separate verification.

## 5. Prepare the Application Bundle

The only canonical application tree is:

`app/mediabox/`

Build:

```bash
python3 scripts/deployment/build_app_bundle.py
```

Generated output:

`infrastructure/heat/app-bundle.b64`

Before using the Heat templates on a new cloud:

- Review template parameters and image/flavor names
- Review bootstrap.sh guest filesystem paths
- Verify access to PostgreSQL and Swift
- Confirm security group and subnet references
- Validate the templates in the target cloud

The present repository is not claimed to offer
one-command end-to-end deployment.

## 6. Prepare Octavia

Preview:

```bash
bash infrastructure/octavia/create_loadbalancer.sh --dry-run
```

Fixed application members can be previewed with:

```bash
APP01_IP=10.20.0.89 APP02_IP=10.20.0.212 \
bash infrastructure/octavia/register_members.sh --dry-run
```

The example addresses are from the original lab.

Heat-managed member addresses can change when
scaling occurs. Their lifecycle must be integrated
with the scaling deployment workflow.

## 7. Database and Identity

Use environment-specific PostgreSQL credentials
and Keystone application credentials.

The complete PostgreSQL schema and initialization
procedure have not yet been recovered.

Do not treat the documented table references as a
verified SQL migration.

## 8. Monitoring

The original lab used Gnocchi and Aodh.

Observed Aodh parameters are documented in:

`docs/architecture/aodh-verified-parameters.md`

Do not assume automatic alarm-triggered scaling has
been verified merely because alarm actions exist.

## 9. Security Warnings

The deployment scripts contain a basic protection
mechanism against accidental application to the
original cloud context.

That guard is not a security boundary.

Do not run --apply unless the target cloud, all
parameters, dependencies and existing resources
have been manually reviewed.

## 10. Verification

Suggested checks:

- VM state and application health
- Private network connectivity
- Load balancer operating status
- Pool member health
- Swift container access
- Cinder attachment and persistence
- Authentication and permissions
- Heat stack state and events
- Gnocchi metric availability
- Aodh alarm history

Record all results in:

`docs/validation/verification-matrix.md`
