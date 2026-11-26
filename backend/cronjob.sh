#!/usr/bin/env bash
set -euo pipefail

# cron does not inherit the container environment. The image entrypoint writes
# the variables this job needs to /etc/minio-sync.env.
if [[ -f /etc/minio-sync.env ]]; then
	# shellcheck disable=SC1091
	source /etc/minio-sync.env
fi

MINIO_BUCKET="${MINIO_BUCKET:-newbucket}"
AWS_S3_BUCKET="${AWS_S3_BUCKET:-minioands3}"
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# mc aliases live in the container filesystem, so recreate them on every run.
/usr/local/bin/add_minio_s3_aliases.sh

mc mirror --overwrite --remove=false "minio/${MINIO_BUCKET}" "aws/${AWS_S3_BUCKET}"

# Purge objects that made it to S3 and invalidate their cached signed URL.
while IFS= read -r obj; do
	if [[ -z "${obj}" ]]; then
		continue
	fi
	if mc stat "aws/${AWS_S3_BUCKET}/${obj}" >/dev/null 2>&1; then
		mc rm "minio/${MINIO_BUCKET}/${obj}" --force
		if [[ -n "${REDIS_PASSWORD}" ]]; then
			redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" --no-auth-warning del "signedurl:${obj}" >/dev/null
		else
			redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" del "signedurl:${obj}" >/dev/null
		fi
	fi
done < <(mc ls --recursive "minio/${MINIO_BUCKET}" | awk '{print $NF}')
