#!/usr/bin/env zsh

NAME=sensor_env
REGISTRY=registry.green-rabbit.net/library

git push
docker build --platform linux/arm64 . -t ${NAME}
docker tag ${NAME} ${REGISTRY}/${NAME}
docker push ${REGISTRY}/${NAME}
