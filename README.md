<p align="center">
  <a href="https://mathefragen.de">
    <picture>
      <img src="https://github.com/user-attachments/assets/d7a8c81b-4ff0-4093-a979-a0028110bb00" height="80" alt="Logo of mathefragen.de">
    </picture>
    <div align="center">Die Lernplattform von Mathe by Daniel Jung</div>
  </a>
</p>

<div style="display: flex; justify-content: space-between;" align="center">
    <a href="https://www.paypal.com/donate/?hosted_button_id=5H4ZXE6GFWDC6">
      <picture>
        <img src="https://github.com/user-attachments/assets/d0372ef1-cbec-4404-a7f6-4e3b8d074e1f" height="40" alt="PayPal Donate Button">
      </picture>
    </a>
</div>

<img width="1348" alt="Screenshot of mathefragen.de" src="https://github.com/user-attachments/assets/ddf2fc7d-c3c9-4fa0-b63e-2b5d8498015e">

# mathefragen.de

This is the official repository of the mathefragen.de and affiliated projects. We are constantly working on improving the platform and adding
new features. Please feel free to contribute to the project by opening issues or pull requests.

Find the project at https://mathefragen.de

## Support this project

This software is maintained and run on the infrastructure of the [Daniel Jung Media GmbH](https://danieljung.io). If you
like the project and want to support us, please consider donating to us. This pays the infrastructure and new features
for this project.

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
