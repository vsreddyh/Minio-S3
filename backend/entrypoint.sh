#!/usr/bin/env bash
set -euo pipefail

# cron does not inherit the container environment. Persist the variables the
# nightly sync needs so cronjob.sh / add_minio_s3_aliases.sh can source them.
ENV_FILE=/etc/minio-sync.env
: >"${ENV_FILE}"
for var in \
	REDIS_HOST REDIS_PORT REDIS_PASSWORD \
	MINIO_ALIAS MINIO_ENDPOINT1 MINIO_ACCESS_KEY MINIO_SECRET_KEY \
	S3_ALIAS AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION \
	AWS_REGION MINIO_BUCKET AWS_S3_BUCKET MC_PATH_STYLE; do
	value="${!var:-}"
	if [[ -n "${value}" ]]; then
		printf 'export %s=%q\n' "${var}" "${value}" >>"${ENV_FILE}"
	fi
done
chmod 600 "${ENV_FILE}"

# Start the cron daemon and configure the mc aliases used by the foreground
# process. Alias setup is best-effort: the API can still start (and report
# degraded health) when MinIO/S3 are unreachable.
/usr/sbin/cron
if [[ -n "${AWS_ACCESS_KEY_ID:-}" && -n "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
	/usr/local/bin/add_minio_s3_aliases.sh || echo "WARNING: could not configure mc aliases"
else
	echo "WARNING: AWS credentials are not set; skipping mc alias setup"
fi

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
