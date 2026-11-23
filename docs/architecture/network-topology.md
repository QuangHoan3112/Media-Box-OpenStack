# MediaBox Network and Load Balancing

## Neutron

The deployment uses:

| Component | Configuration |
|---|---|
| Provider network | public, flat, physnet1 |
| Public subnet | 192.168.57.0/24 |
| Private network | private, VXLAN |
| Private subnet | 10.20.0.0/24 |
| Router | mediabox-router |
| Application security group | mediabox-app-sg |
| Database security group | mediabox-db-sg |

The Octavia management network (`lb-mgmt-net`,
10.1.0.0/24) is managed separately from the
MediaBox application network.

## Octavia

| Component | Value |
|---|---|
| Load balancer | mediabox-lb |
| VIP | 10.20.0.90 |
| Listener | mediabox-http-listener |
| Protocol / port | HTTP / 8000 |
| Pool | mediabox-app-pool |
| Algorithm | ROUND_ROBIN |
| Health monitor | mediabox-health-monitor |

Verified pool members at the time of inventory:

- App01: 10.20.0.89:8000
- App02: 10.20.0.212:8000
- App03: 10.20.0.15:8000
- App04: 10.20.0.252:8000

All four members reported ONLINE.

## Notes

- Application instances use private IP addresses.
- The VIP is on the private network.
- Direct external browser access requires a suitable
  route, proxy, tunnel or external-facing endpoint.
- The two Heat-created members must be managed
  consistently with the deployment's scaling policy.
- Do not recreate the Octavia management network
  as an ordinary MediaBox tenant resource.
- Security Group rules and detailed Health Monitor
  properties require a separate configuration audit.
