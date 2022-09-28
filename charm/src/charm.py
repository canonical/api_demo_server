#!/usr/bin/env python3
# Copyright 2022 maksim
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""
import logging

import requests
from charms.data_platform_libs.v0.database_requires import DatabaseCreatedEvent
from charms.data_platform_libs.v0.database_requires import DatabaseRequires
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.observability_libs.v1.kubernetes_service_patch import KubernetesServicePatch
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from lightkube.models.core_v1 import ServicePort
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
from ops.model import WaitingStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class FastAPIDemoCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        self.app_environment = {"DEMO_SERVER_DB_HOST": self.model.config["postgresip"]}
        self.container = self.unit.get_container("demo-server")

        # Patch the juju created Kubernetes service to contain the right ports
        port = ServicePort(8000, name=f"{self.app.name}")
        self.service_patcher = KubernetesServicePatch(self, [port])

        # Provide ability for prometheus to be scraped by Prometheus using prometheus_scrape
        self._prometheus_scraping = MetricsEndpointProvider(
            self,
            relation_name="metrics-endpoint",
            jobs=[{"static_configs": [{"targets": ["*:8000"]}]}],
        )

        # Enable log forwarding for Loki and other charms that implement loki_push_api
        self._logging = LogProxyConsumer(
            self, relation_name="logging", log_files=["demo_server.log"]
        )

        # Provide grafana dashboards over a relation interface
        self._grafana_dashboards = GrafanaDashboardProvider(self, relation_name="grafana-dashboard")

        self.framework.observe(
            self.on.demo_server_pebble_ready, self._on_demo_server_image_pebble_ready
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.drop_db_action, self._on_drop_db_action)
        self.framework.observe(self.on.fetch_db_action, self._on_fetch_db_action)

        # Charm events defined in the database requires charm library.
        self.database = DatabaseRequires(self, relation_name="database", database_name="names_db")
        self.framework.observe(self.database.on.database_created, self._on_database_created)
        self.framework.observe(self.database.on.endpoints_changed, self._on_database_created)

        self._stored.set_default(things=[])

    def _on_demo_server_image_pebble_ready(self, _):
        """Define and start a workload using the Pebble API.

        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Add initial Pebble config layer using the Pebble API
        self.container.add_layer("fastapi_demo", self._pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        self.container.autostart()
        self.container.replan()

        # add workload version in juju status
        self.unit.set_workload_version(self.version)

        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    @property
    def _pebble_layer(self):
        pebble_layer = {
            "summary": "FastAPI demo layer",
            "description": "pebble config layer for FastAPI demo server",
            "services": {
                "fastapi": {
                    "override": "replace",
                    "summary": "fastapi demo",
                    "command": "uvicorn api_demo_server.app:app --host=0.0.0.0",
                    "startup": "enabled",
                    "environment": self.app_environment,
                }
            },
        }
        return Layer(pebble_layer)

    def _on_database_created(self, event: DatabaseCreatedEvent) -> None:
        logger.info("New endpoint is %s", event.endpoints)
        # Handle the created database
        self.app_environment = {
            "DEMO_SERVER_DB_HOST": event.endpoints,
            "DEMO_SERVER_DB_USER": event.username,
            "DEMO_SERVER_DB_PASSWORD": event.password,
        }

        self._on_demo_server_image_pebble_ready(None)

        # Set active status
        self.unit.status = ActiveStatus("received database credentials")

    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.py file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        current = self.config["postgresip"]  # see config.yaml
        if current not in self._stored.things:
            logger.debug("found a new thing: %r", current)
            self._stored.things.append(current)

    def _on_drop_db_action(self, event):
        """Example of a custom action that could be defined.

        In this case the action will call an API to remove (clean-up) a database.
        Update status of the action to fail if something goes wrong, otherwise pass a
        success message to the user.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        timeout = event.params["timeout"]  # see actions.yaml
        try:
            resp = requests.post("http://localhost:8000/dropdb", timeout=int(timeout))
            if resp.status_code == 200:
                event.set_results({"success": "Database was dropped successfully."})
            else:
                event.fail(f"Request status code is: {resp.status_code}")
        except Exception as e:
            event.fail(f"Request failed: {e}")

    def _update_layer_and_restart(self):
        if self.container.can_connect():
            layer = self._pebble_layer.to_dict()
            # Get the current config
            services = self.container.get_plan().to_dict().get("services", {})
            # Check if there are any changes to services
            if services != layer["services"]:
                # Changes were made, add the new layer
                self.container.add_layer("fastapi_demo", self._pebble_layer, combine=True)
                logging.info("Added updated layer 'fastapi_demo' to Pebble plan")
                # Restart it and report a new status to Juju
                self.container.restart("fastapi")
                logging.info("Restarted 'fastapi' service")
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

    def _on_fetch_db_action(self, event):
        """Example of a custom action that could be defined.

        In this case the action will call an API to remove (clean-up) a database.
        Update status of the action to fail if something goes wrong, otherwise pass a
        success message to the user.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        data = self.database.fetch_relation_data()
        for key, val in data.items():
            if val["database"] == "names_db":
                event.set_results(
                    {
                        "db-username": val["user"],
                        "db-password": val["password"],
                        "db-host": val["host"],
                        "db-port": val["port"],
                    }
                )
                self.app_environment = {
                    "DEMO_SERVER_DB_HOST": val["host"],
                    "DEMO_SERVER_DB_PORT": val["port"],
                    "DEMO_SERVER_DB_USER": val["user"],
                    "DEMO_SERVER_DB_PASSWORD": val["password"],
                }
                self._update_layer_and_restart()
                break

    @property
    def version(self) -> str:
        """Reports the current workload (FastAPI app) version."""
        container = self.unit.get_container("demo-server")
        if container.can_connect() and container.get_services("fastapi"):
            try:
                return self._request_version()
            # Catching Exception is not ideal, but we don't care much for the error here, and just
            # default to setting a blank version since there isn't much the admin can do!
            except Exception as e:
                logger.warning("unable to get version from API: %s", str(e))
                logger.exception(e)
                return ""
        return ""

    def _request_version(self) -> str:
        """Helper for fetching the version from the running workload using the API."""
        resp = requests.get("http://localhost:8000/version", timeout=10)
        return resp.json()["version"]


if __name__ == "__main__":
    main(FastAPIDemoCharm)
