# mathefragen.de

## Development

### Via Docker

There is a docker-compose.yml-file which can be used to start the development environment. It will start a postgres
database, a redis server and the django app. The django app will be started with the `runserver` command and will reload
on code changes.

```sh
docker compose up
```

### Create a superuser

Create your first admin user:

```shell
docker compose exec django python manage.py createsuperuser
```

### Via poetry

You can also start the development environment via poetry. First you need to install the dependencies:

```sh
poetry install
```

Start a database:

```sh
docker compose up -d postgres
```

Then you can start the development server:

```sh
poetry run python manage.py runserver
```

### Compressor

On the first start, you might need to execute compressor manually:

```sh
python manage.py compress

# or
docker compose exec django python manage.py compress
```

## Deployment

Deployment process is done via gitlab CI/CD. All you need to do is pushing your changes and then create a git tag of the
commit you want to deploy containing a semantic versioning scheme:

MajorRelease.MinorRelease.HotFixes (e.g. 1.2.25)

### Updating .env files

If you want to update the .env files that the main server uses, you need to update them on the main production servers
on the directory:
`/var/www/aiedn/apps/mathefragen.de/`.

### Updating NGINX configs

To update the NGINX configs you need make your changes on the https://gitlab.com/new-learning/aiedn-group/configs/nginx
and then pull the changes on the server from the directory `/var/www/aiedn/setup`.
