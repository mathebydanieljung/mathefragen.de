#!/bin/bash

printf "\n\nCurrent services use this image:\n\n"

docker service ls --format "{{.Image}} - {{.Name}}"| grep fragen

IMAGE=registry.gitlab.com/new-learning/mathefragen.de/app

printf "\n\n\n"

read  -p "What image version should be deployed? (eg. 1.0.0): " TAG

docker service update --image $IMAGE:$TAG --force bio_biofragen-server
docker service update --image $IMAGE:$TAG --force chemi_chemiefragen-server
docker service update --image $IMAGE:$TAG --force informatic_informatikfragen-server
docker service update --image $IMAGE:$TAG --force math_mathefragen-server
docker service update --image $IMAGE:$TAG --force meta_metafragen-server
docker service update --image $IMAGE:$TAG --force physik_physikfragen-server
