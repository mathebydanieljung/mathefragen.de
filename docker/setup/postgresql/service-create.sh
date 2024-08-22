docker service create --name postgresql --network nl-net --mount type=bind,source=/var/dockerfiles/postgres,target=/var/lib/postgresql/data nginx
