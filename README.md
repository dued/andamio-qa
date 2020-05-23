# Andamio Aseguramiento de Calidad

[![Build Status](https://travis-ci.org/dued/andamio-qa.svg?branch=master)](https://travis-ci.org/dued/andamio-qa)
[![Docker Pulls](https://img.shields.io/docker/pulls/dued/andamio-qa.svg)](https://hub.docker.com/r/dued/andamio-qa)
[![Layers](https://images.microbadger.com/badges/image/dued/andamio-qa.svg)](https://microbadger.com/images/dued/andamio-qa)
[![Commit](https://images.microbadger.com/badges/commit/dued/andamio-qa.svg)](https://microbadger.com/images/dued/andamio-qa)
[![License](https://images.microbadger.com/badges/license/dued/andamio-qa.svg)](https://microbadger.com/images/dued/andamio-qa)

¡CUIDADO !, este proyecto está en **etapa beta** . Las cosas están cambiando rápidamente.

## ¿Que hace QA?

QA es un conjunto de Herramientas para verificar que su proyecto [Andamio][]-base es cool.

## ¿Por qué?

Porque las [herramientas de control de calidad para mantenedores OCA][MQT] están centradas en los complementos (addons)
y necesitamos herramientas de control de calidad centradas en Andamio.

## ¿Cómo?

1. Monte la estructura de su proyecto, generalmente basada en el [andamiaje][andamiaje] provisto en `/proyecto` en el contenedor. Docker CLI ejemplo: `-v $(pwd):/proyecto`.

1. Dale acceso a un socket Docker (¡cuidado con las **implicaciones de seguridad!**) Con `--privileged -v /var/run/docker.sock` o con `-e DOCKER_HOST=tcp://dockerhost:2375`.

1. Configurar mediante [variables de entorno](#variables-de-entorno).

1. Ejecute cualquiera de los [scripts](#scripts) incluidos.

Comando de ejemplo para entorno de prueba, bueno para CI:

```bash
docker container run --rm -it --privileged -e COMPOSE_FILE=test.yaml -v "$PWD:/proyecto:z" -v /var/run/docker.sock:/var/run/docker.sock:z dued/andamio-qa pylint
```

Comando de ejemplo para el entorno de desarrollo, que solo contiene complementos privados:

```bash
docker container run --rm -it --privileged -v "$PWD:$PWD:z" -v /var/run/docker.sock:/var/run/docker.sock:z -w "$PWD" -e ADDON_CATEGORIES=-p dued/andamio-qa pylint
```

Lo más probable es que desee ejecutar esto en un entorno de CI, así que simplemente revise el directorio `ejemplos` y obtendrá una pista sobre cómo hacerlo.

## Variables de entorno

Puede usar cualquiera de las [Variables de entorno de Docker Compose](https://docs.docker.com/compose/reference/envvars/). Además, también tienes estas:

### `ADDON_CATEGORIES`

Por defecto `--private` para todos los `jobs` trabajos.

Puede cambiarlo por trabajo, usando cualquiera de estos `--private --extra --core` (o `-pec`)

Estas flags (banderas) se utilizan para el [scrpt `addons`](https://github.com/dued/andamio/docs#addons) disponible en todos los proyectos de andamio. Use este comando en la carpeta de su proyecto para comprender su uso:

```bash
docker-compose run --rm odoo addons --help
```

### `ADMIN_PASSWORD`

Por defecto es `admin`. Si se establece, se usa como la contraseña del administrador de base de datos

### `ARTIFACTS_DIR`

Directorio donde se extraerán todos los artefactos producidos por scripts internos.

### `ARTIFACTS_UID` and `ARTIFACTS_GID`

UID/GID se establecerá como propietario de los artefactos producidos por insider scripts (scrpits internos).

### `BUILD_FLAGS`

flags para agregar a `docker-compose build`. Por defecto es `--pull --no-cache`.

### `DESTROY_FLAGS`

Flags para agregar a `docker-compose down`. Por defecto es `-v --rmi local --remove-orphans`.

### `LINT_DISABLE`

Inhabilita mensajes específicos de linter. Su formato depende del linter subyacente.

El valor predeterminado es `manifest-required-author` , ya que se espera que solo desee alinear complementos privados, y esos no son OCA.

TODO: Haz que funcione con flake8.

### `LINT_ENABLE`

Habilita mensajes específicos de linter. Su formato depende del linter subyacente.

Vacío por defecto.

TODO: Haz que funcione con flake8.

### `LINT_MODE`

En este momento, solo es útil para [`pylint`](#pylint). Valores válidos:

- `loose` (predeterminado) usa el estándar cfg [MQT][].
- `strict` utiliza cfg pull request (solicitud de extracción o PR).
- `beta` usa cfg beta.

### `PGPASSWORD`

Se usa en [`secrets-setup`](#secrets-setup) cuando necesita una contraseña de base de datos específica.

Por defecto es `odoopassword`.

### `PYTHONOPTIMIZE`

Por defecto es `""` (deshabilitado) para permitir declaraciones `assert`, que si bien pueden ser utiles para PRUEBAS (tests), no lo son para producción o demos.

[Más detalles en la documentación de Python.](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONOPTIMIZE).

### `REPOS_FILE`

Path a archivo `repos.yaml` en el andamio actual (**no** dentro del contenedor)

## Scripts

Se puede utilizar comandos `sh`, `docker` y `docker-compose` commands con todas sus características.

Además, hay otros scripts incluidos, útiles para hacer una canalización de CI:

### `addons-install`

Instala complementos solicitados.

### `build`

Construye tu proyecto con `docker-compose` y comprueba los trabajos de odoo.

Usos [`BUILD_FLAGS`](#build_flags).

### `closed-prs`

Conozca si su definición `repos.yaml` incluye PRs (solicitudes de extracción) fusionadas o cerradas..

Utiliza las variables de entorno [`REPOS_FILE`](#repos-file) y [`GITHUB_TOKEN`][1].

### `coverage`

Ejecuta pruebas unitarias de complementos e informes de cobertura.

Por lo general, debes correr [`addons-install`](#addons-install) antes.

Encontrará los archivos de informe HTML en `./$ARTIFACTS_DIR/coverage`.

### `destroy`

Destruye todos los contenedores, volúmenes, imágenes locales y redes.

Usos [`DESTROY_FLAGS`](#destroy_flags).

### `flake8`

Lintea código con [flake8](https://pypi.python.org/pypi/flake8) usando [MQT][].

### `networks-autocreate`

Cree redes externas que faltan, que no son creadas automáticamente por docker compose porque espera que estén presentes al momento de iniciar un entorno.

Ejemplos comunes de tales redes son [`inverseproxy_shared`](https://github.com/dued/andamio#global-inverse-proxy) o [`globalwhitelist_shared`](https://github.com/dued/andamio/docs#global-whitelist)

Extrae las redes requeridas del archivo `docker-compose.yaml` elegido .

### `pylint`

Lintea código con [pylint-odoo](https://github.com/OCA/pylint-odoo/) usando [MQT][].

Algunas [variables de entorno](#variables-de-entorno) modifican el comportamiento de este script; échales un vistazo.

### `secrets-setup`

Crea todos los archivos de entorno necesarios para que funcione el entorno oficial `test.yaml`.

Usa [`ADMIN_PASSWORD`](#admin_password) y [`PGPASSWORD`](#pgpassword).

### `shutdown`

Como [`destroy`](#destroy), pero manteniendo volúmenes e imágenes.

## Otras utilidades

Estas herramientas no están estrictamente relacionadas con Andamio, pero son útiles y están incluidas:

- [`jq`](https://stedolan.github.io/jq/)
- [`yq`](https://kislyuk.github.io/yq/)

[1]: https://github.com/acsone/git-aggregator#show-closed-github-pull-requests
[Andamio]: https://github.com/dued/andamio
[MQT]: https://github.com/OCA/maintainer-quality-tools
[andamiaje]: https://github.com/dued/andamio-base