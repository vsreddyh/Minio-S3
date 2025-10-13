#!/bin/bash

# Redis configuration
: "${REDIS_HOST:=127.0.0.1}"
: "${REDIS_PORT:=6379}"
: "${REDIS_PASSWORD:=redispassword123}"

mc mirror --overwrite --remove=false minio/newbucket aws/minioands3

for obj in $(mc ls --recursive minio/newbucket | awk '{print $6}'); do
	if mc stat aws/minioands3/$obj >/dev/null 2>&1; then
		mc rm minio/newbucket/$obj --force
		redis-cli -h redis -p "${REDIS_PORT:-6379}" -a "${REDIS_PASSWORD}" del signedurl:$obj >/dev/null
	fi
done
