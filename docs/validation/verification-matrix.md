# MediaBox Verification Matrix

Evidence is based on the original lab inventory
and demonstrations as of 2026-11-22.

| Component | Verification | Status |
|---|---|---|
| FastAPI application | HTTP / and /health response | Verified |
| Frontend | /app SHA256 matched source | Verified |
| Neutron | Network, subnet, router inventory | Verified |
| Octavia | Four pool members ONLINE | Verified |
| Swift | Container and objects listed | Verified |
| Cinder | 5 GiB DB volume attached | Verified |
| PostgreSQL | Three tables referenced in source | Partially verified |
| Keystone | Service and role inventory | Verified |
| Heat | Stack UPDATE_COMPLETE | Verified |
| Manual scale-out | Demonstrated during the lab | Demonstrated |
| Gnocchi | 21 resources returned | Verified |
| Aodh | Alarm configuration inspected | Verified |
| Automatic scaling | End-to-end trigger and effect | Not fully verified |
| Fresh-cloud redeploy | Full deployment from repository | Not tested |
| Repository security | Pattern scan, no matches | Manual review pending |

## Important Notes

The database schema is incomplete because a
matching SSH private key for the database VM was
not found on the Controller during the audit.

The Cinder attachment is verified through OpenStack,
but the PostgreSQL data directory inside the VM
has not been verified.

Aodh alarm state does not independently prove
that automatic Heat scaling occurred.

No production-readiness claim is made.
