# ADR-005: MinIO SDK over boto3 for S3-compatible Storage

## status
Accepted

## context
The S3 adapter (`adapters/s3_sync.py`) uses boto3 for 6 operations: upload_file, download_file, list_objects_v2, head_object, put_object, and client construction. boto3 + botocore is ~15MB of dependencies designed for the full AWS SDK surface area — IAM, CloudFormation, EC2, and hundreds of other services. loretools only needs S3-compatible object storage.

`SyncConfig.endpoint` already signals the design intent: S3-compatible backends (self-hosted MinIO, Cloudflare R2, Backblaze B2) are the primary target, not AWS S3 specifically. boto3 was chosen for convenience in the initial implementation, not for any feature it uniquely provides.

## decision
Replace boto3/botocore with the MinIO Python SDK (`minio`). The MinIO SDK supports any S3-compatible endpoint (including AWS S3) and covers all 6 operations in the adapter with a cleaner, leaner API.

httpx alone was considered but rejected: S3 authentication requires AWS SigV4 request signing. httpx provides no signing support, so a separate signing library would be needed — trading one large dependency for two smaller ones of lower maturity.

## alternatives considered

**httpx + SigV4 signing library** (e.g., `aws-request-signer`, `httpx-aws-auth`): Replaces boto3 but adds an untested signing dependency. SigV4 is non-trivial to implement correctly (canonical headers, SHA-256 body hash, URL encoding edge cases). No advantage over MinIO SDK in size or simplicity. Rejected.

**boto3 with extras isolation** (keep but gate behind optional import): Already done, but does not solve the weight problem for users who want sync — boto3 still pulls in botocore, s3transfer, jmespath, python-dateutil. Rejected.

**Staying with boto3**: Viable but contradicts MVP mindset — 15MB for 6 operations is a resource waste, and the existing unit test failures (8 tests fail without boto3 installed) confirm it does not fit naturally in the dev environment. Rejected.

## consequences
Positive:
- Dependency weight: `minio` is ~500KB; boto3 + botocore + s3transfer is ~15MB
- All 6 existing adapter operations have direct MinIO SDK equivalents
- boto3 removed from optional deps entirely — sync extra becomes lighter
- Dev environment no longer has 8 conditional boto3 test failures
- MinIO SDK supports AWS S3, MinIO, Cloudflare R2, Backblaze B2, and any S3-compatible endpoint — same coverage as before

Negative:
- Any users already using boto3 AWS credential chain (env vars, `~/.aws/credentials`, instance roles) will need explicit `access_key`/`secret_key` in `SyncConfig` — MinIO SDK does not auto-discover AWS credentials
- MinIO SDK raises `minio.error.S3Error` rather than `botocore.exceptions.ClientError` — the `exists()` adapter must catch the new type

Neutral:
- `SyncConfig.endpoint` remains the discriminator for non-AWS backends — no model changes needed
- MinIO SDK is sync; the adapter is already sync; no async surface change
