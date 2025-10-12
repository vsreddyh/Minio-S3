#!/bin/bash
mc mirror --overwrite --remove=false minio/newbucket aws/minioands3

for obj in $(mc ls --recursive minio/newbucket | awk '{print $6}'); do
  if mc stat aws/minioands3/minio/newbucket/$obj > /dev/null 2>&1; then
    mc rm minio/newbucket/$obj --force
  fi
done