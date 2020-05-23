#!/usr/bin/env python3
"""Prueba que esta imagen de prueba prueba pruebas bien."""
import logging
import sys
import os
import unittest

from os.path import dirname, isfile, join
from shutil import rmtree

import docker


logging.root.setLevel(logging.INFO)
IMAGE = os.environ.get("IMAGE_NAME", "dued/andamio-qa:latest")
SCAFFOLDINGS_DIR = join(dirname(__file__), "scaffoldings")
BASE_ENVIRON = {
    "ARTIFACTS_UID": os.getuid(),
    "ARTIFACTS_GID": os.getgid(),
    "DB_VERSION": os.environ.get("DB_VERSION", "11"),
    "ODOO_MINOR": os.environ.get("ODOO_MINOR", "12.0"),
    "VERBOSE": os.environ.get("VERBOSE", "0"),
}


class TestException(Exception):
    pass


class AndamioQAScaffoldingCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.fulldir = join(SCAFFOLDINGS_DIR, self.directory)
        self.client = docker.from_env()
        self.environment = {}
        self.addCleanup(self.client.close)

    def tearDown(self):
        self.run_qa("shutdown")
        return super().tearDown()

    def run_qa(self, *args, **kwargs):
        """Atajo para ejecutar QA y asegurarse de que funciona.

        :param list args:
            Comandos para ejecutarse en el contenedor de QA.

        :param dict kwargs:
            Configuraciones adicionales para el cliente Docker.
        """
        env = dict(BASE_ENVIRON, **self.environment)
        scaffolding = join(SCAFFOLDINGS_DIR, self.directory)
        params = {
            "command": args,
            "detach": True,
            "stdout": True,
            "stderr": True,
            "environment": env,
            "image": IMAGE,
            "mounts": [
                docker.types.Mount(
                    target=scaffolding,
                    source=scaffolding,
                    type="bind",
                    read_only=False,
                ),
                docker.types.Mount(
                    target="/var/run/docker.sock",
                    source="/var/run/docker.sock",
                    type="bind",
                    read_only=True,
                ),
            ],
            "privileged": True,
            "tty": True,
            "working_dir": scaffolding,
        }
        params.update(kwargs)
        logging.info(
            "Executing %s in %s with environment %s",
            args, scaffolding, env,
        )
        container = self.client.containers.run(**params)
        self.addCleanup(container.remove)
        self.addCleanup(
            rmtree,
            join(scaffolding, env.get("ARTIFACTS_DIR", "artifacts")),
            ignore_errors=True,
        )
        # Stream logs 
        with os.fdopen(sys.stderr.fileno(), "wb", closefd=False) as stderr:
            for part in container.logs(stream=True):
                stderr.write(part)
                stderr.flush()
        result = container.wait()
        if result["StatusCode"]:
            raise TestException(result)
        return result


class Scaffolding0Case(AndamioQAScaffoldingCase):
    directory = "0"

    def setUp(self):
        super().setUp()
        self.environment["COMPOSE_FILE"] = "test.yaml"

    def test_100_networks_autocreate(self):
        """Creación automática de redes externas requeridas."""
        with self.assertRaises(docker.errors.NotFound):
            self.client.networks.get("some_external_network")
        self.run_qa("networks-autocreate")
        self.client.networks.get("some_external_network")

    def test_200_build(self):
        """Prueba de construcción de imágenes."""
        self.environment["BUILD_FLAGS"] = "--pull"
        self.run_qa("build")

    def test_400_addons_install(self):
        """Instalar dependencias de prueba."""
        self.environment["ADDON_CATEGORIES"] = "-edp"
        self.run_qa("addons-install")

    def test_500_coverage(self):
        """Prueba de cobertura funciona bien."""
        self.environment["ARTIFACTS_DIR"] = "other_dir"
        self.run_qa("coverage")
        self.assertTrue(isfile(join(
            SCAFFOLDINGS_DIR,
            self.directory,
            "other_dir",
            "coverage",
            "index.html",
        )))

    def test_500_coverage_wrong_categories(self):
        """Prueba de cobertura falla si se envían categorías incorrectas."""
        self.environment["ADDON_CATEGORIES"] = "this is wrong"
        with self.assertRaises(TestException):
            self.run_qa("coverage")

    def test_500_curl(self):
        """Asegúrese de que curl esté instalado y funcionando."""
        self.run_qa("curl", "--version")

    def test_500_flake8(self):
        """comprueba que las pruebas de flake8 funcionan bien."""
        # por defecto a private addons, donde hay errores de linter
        with self.assertRaises(TestException):
            self.run_qa("flake8")
        self.environment["ADDON_CATEGORIES"] = "-e"
        self.run_qa("flake8")

    def test_500_jq(self):
        """La herramienta de CLI ``jq`` deberia funcionar."""
        self.run_qa("jq", "--version")

    def test_500_pre_commit(self):
        """La herramienta de CLI ``pre-commit`` deberia funcionar."""
        self.run_qa("pre-commit", "--version")

    def test_500_pylint(self):
        """comprueba que las pruebas de pylint funcionan bien"""
        with self.assertRaises(TestException):
            self.run_qa("pylint")
        self.environment["ADDON_CATEGORIES"] = "-e"
        self.run_qa("pylint")

    def test_500_secrets_setup_defaults(self):
        """Verifica que secrets-setup funciona bien con los valores predeterminados."""
        self.run_qa("secrets-setup")
        values = {
            "backup": "",
            "db-access": "PGPASSWORD=odoopassword",
            "db-creation": "POSTGRES_PASSWORD=odoopassword",
            "odoo": "ADMIN_PASSWORD=admin",
            "smtp": "",
        }
        for key, value in values.items():
            with open(join(self.fulldir, ".docker", f"{key}.env")) as env_file:
                self.assertEqual(value, env_file.read())

    def test_500_secrets_setup_altered(self):
        """Verifica que secrets-setup funciona bien con los valores alterados."""
        self.environment["PGPASSWORD"] = "pgother"
        self.environment["ADMIN_PASSWORD"] = "adminother"
        self.run_qa("secrets-setup")
        values = {
            "backup": "",
            "db-access": "PGPASSWORD=pgother",
            "db-creation": "POSTGRES_PASSWORD=pgother",
            "odoo": "ADMIN_PASSWORD=adminother",
            "smtp": "",
        }
        for key, value in values.items():
            with open(join(self.fulldir, ".docker", f"{key}.env")) as env_file:
                self.assertEqual(value, env_file.read())

    def test_500_yq(self):
        """La herramienta de CLI ``pre-commit`` deberia funcionar"""
        self.run_qa("yq", "--version")

    def test_999_destroy(self):
        """Destruye todo lo relacionado con este caso de prueba."""
        self.run_qa("destroy")
        self.client.networks.get("some_external_network").remove()


if __name__ == "__main__":
    unittest.main()
