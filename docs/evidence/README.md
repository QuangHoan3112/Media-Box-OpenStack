# MediaBox Evidence Guide

This directory is intended for sanitized screenshots
and evidence captured during the project.

## Suggested Categories

1. OpenStack dashboard and running services
2. Nova application and database VMs
3. Neutron networks, subnets and router
4. Security Groups
5. Swift container and upload demonstration
6. Cinder volume and database attachment
7. Octavia load balancer and healthy members
8. Heat stack, templates and scale-out events
9. Gnocchi resources and metrics
10. Aodh alarms and history
11. MediaBox login, upload, listing and playback
12. Permissions and access-control demonstration

## Screenshot Rules

Before committing screenshots:

- Remove passwords and authentication tokens
- Remove private keys and application credentials
- Remove signed Heat action URLs
- Remove confidential user or project data
- Hide unrelated personal filenames in Swift
- Review terminals for sensitive environment values
- Remove irrelevant browser tabs or account details

## Recommended Naming

Use consistent names, for example:

- 01-openstack-dashboard.png
- 02-nova-instances.png
- 03-neutron-networks.png
- 04-swift-container.png
- 05-cinder-volume.png
- 06-octavia-members.png
- 07-heat-stack.png
- 08-aodh-alarms.png
- 09-mediabox-interface.png

Do not fabricate screenshots. Use only actual
observations from the completed lab.
