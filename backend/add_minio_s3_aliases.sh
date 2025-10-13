#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   MINIO_ALIAS=minio \
#   MINIO_ENDPOINT=http://localhost:9000 \
#   MINIO_ACCESS_KEY=minioadmin \
#   MINIO_SECRET_KEY=minioadmin \
#   S3_ALIAS=aws \
#   AWS_ACCESS_KEY_ID=AKIA... \
#   AWS_SECRET_ACCESS_KEY=... \
#   AWS_DEFAULT_REGION=us-east-1 \
# Requires: mc (MinIO client) and redis-cli in PATH

# -------- MinIO / S3 config --------
MINIO_ALIAS="${MINIO_ALIAS:-minio}"
: "${MINIO_ENDPOINT1:=http://localhost:9000}"
: "${MINIO_ACCESS_KEY:=minioadmin}"
: "${MINIO_SECRET_KEY:=minioadmin}"

: "${S3_ALIAS:=aws}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_DEFAULT_REGION:=us-west-2}"

# Optional: path-style for some endpoints (mc defaults to auto)
: "${MC_PATH_STYLE:=auto}" # values: auto|on|off

# Skip MinIO if SKIP_MINIO is set to true
if [[ "${SKIP_MINIO:-false}" != "true" ]]; then
	echo "Configuring mc alias for MinIO: ${MINIO_ALIAS} -> ${MINIO_ENDPOINT1}"
	if mc alias set --path "${MC_PATH_STYLE}" "${MINIO_ALIAS}" "${MINIO_ENDPOINT1}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" 1>/dev/null; then
		echo "OK: ${MINIO_ALIAS}"
	else
		echo "WARNING: Could not configure MinIO alias (MinIO server may be unavailable)"
	fi
else
	echo "Skipping MinIO configuration (SKIP_MINIO=true)"
fi

# AWS S3 endpoint for mc is 'https://s3.amazonaws.com' (Signature V4)
AWS_S3_ENDPOINT="https://s3.amazonaws.com"

echo "Configuring mc alias for AWS S3: ${S3_ALIAS} -> ${AWS_S3_ENDPOINT} (region ${AWS_DEFAULT_REGION})"
# mc doesn't store region on alias; region is used per-bucket ops, but alias set is enough.
mc alias set --api S3v4 --path "${MC_PATH_STYLE}" "${S3_ALIAS}" "${AWS_S3_ENDPOINT}" "${AWS_ACCESS_KEY_ID}" "${AWS_SECRET_ACCESS_KEY}" 1>/dev/null
echo "OK: ${S3_ALIAS}"

echo
echo "Aliases configured:"
mc alias list | sed -e 's/AccessKey.*/AccessKey: ****/g' -e 's/SecretKey.*/SecretKey: ****/g'
