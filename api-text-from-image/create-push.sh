#!/bin/bash
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/j3u8l7c0 && \
docker buildx build --platform linux/amd64,linux/arm64 -t public.ecr.aws/j3u8l7c0/extract-question-from-image:1.0 --push .