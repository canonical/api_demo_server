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
from typing import Dict
from typing import Optional

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
from ops.model import MaintenanceStatus
from ops.model import WaitingStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class FastAPIDemoCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args) -> None:
        super().__init__(*args)

        logger.info("Charm is initialized with port %s", self.config["server-port"])

        self.container = self.unit.get_container("demo-server")  # see 'containers' in metadata.yaml
        self.pebble_service_name = "fastapi-service"

        # Patch the juju created Kubernetes service to contain the right ports
        port = ServicePort(int(self.config["server-port"]), name=f"{self.app.name}")
        self.service_patcher = KubernetesServicePatch(
            self, [port], refresh_event=self.on.config_changed
        )

        # Provide ability for prometheus to be scraped by Prometheus using prometheus_scrape
        self._prometheus_scraping = MetricsEndpointProvider(
            self,
            relation_name="metrics-endpoint",
            jobs=[{"static_configs": [{"targets": [f"*:{self.config['server-port']}"]}]}],
            refresh_event=self.on.config_changed,
        )

        # Enable log forwarding for Loki and other charms that implement loki_push_api
        self._logging = LogProxyConsumer(
            self, relation_name="logging", log_files=["demo_server.log"]
        )

        # Provide grafana dashboards over a relation interface
        self._grafana_dashboards = GrafanaDashboardProvider(self, relation_name="grafana-dashboard")

        # Charm events defined in the database requires charm library.
        self.database = DatabaseRequires(self, relation_name="database", database_name="names_db")
        self.framework.observe(self.database.on.database_created, self._on_database_created)
        self.framework.observe(self.database.on.endpoints_changed, self._on_database_created)
        self.framework.observe(self.on.database_relation_broken, self._on_database_relation_removed)

        self.framework.observe(self.on.demo_server_pebble_ready, self._update_layer_and_restart)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        # events on custom actions that are run via 'juju run-action'
        self.framework.observe(self.on.drop_table_action, self._on_drop_table_action)
        self.framework.observe(self.on.get_db_info_action, self._on_get_db_info_action)

        self._stored.set_default(db_host=None, db_port=None, db_user=None, db_password=None)

    @property
    def app_environment(self) -> Dict[str, Optional[str]]:
        if not all(
            [
                self._stored.db_host,
                self._stored.db_port,
                self._stored.db_user,
                self._stored.db_password,
            ]
        ):
            self.get_db_relation_data()

        env_vars = {
            "DEMO_SERVER_DB_HOST": self._stored.db_host,
            "DEMO_SERVER_DB_PORT": self._stored.db_port,
            "DEMO_SERVER_DB_USER": self._stored.db_user,
            "DEMO_SERVER_DB_PASSWORD": self._stored.db_password,
        }
        return env_vars

    def get_db_relation_data(self) -> None:
        data = self.database.fetch_relation_data()
        logger.warning("Got following database data: %s", data)
        for key, val in data.items():
            if not val:
                continue
            host, port = val["endpoints"].split(":")
            self._stored.db_host = host
            self._stored.db_port = port
            self._stored.db_user = val["username"]
            self._stored.db_password = val["password"]
            break
        else:
            self.unit.status = WaitingStatus("Waiting for database relation")
            exit(0)  # todo replace with proper exit status

    @property
    def _pebble_layer(self) -> Layer:
        logger.debug(f"Add following environment to the layer: {(env := self.app_environment)}")
        command = " ".join(
            [
                "uvicorn",
                "api_demo_server.app:app",
                "--host=0.0.0.0",
                f"--port={self.config['server-port']}",
            ]
        )
        pebble_layer = {
            "summary": "FastAPI demo layer",
            "description": "pebble config layer for FastAPI demo server",
            "services": {
                self.pebble_service_name: {
                    "override": "replace",
                    "summary": "fastapi demo",
                    "command": command,
                    "startup": "enabled",
                    "environment": env,
                }
            },
        }
        return Layer(pebble_layer)

    def _update_layer_and_restart(self, event) -> None:
        """Define and start a workload using the Pebble API.

        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """

        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = MaintenanceStatus("Assembling pod spec")
        if self.container.can_connect():
            new_layer = self._pebble_layer.to_dict()
            # Get the current pebble layer config
            services = self.container.get_plan().to_dict().get("services", {})
            if services != new_layer["services"]:
                # Changes were made, add the new layer
                self.container.add_layer("fastapi_demo", self._pebble_layer, combine=True)
                logger.info("Added updated layer 'fastapi_demo' to Pebble plan")

                self.container.restart(self.pebble_service_name)
                logger.info(f"Restarted '{self.pebble_service_name}' service")

            # add workload version in juju status
            self.unit.set_workload_version(self.version)
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble in workload container")

    def _on_database_created(self, event: DatabaseCreatedEvent) -> None:
        """Set stored states for database info and update pebble layer.

        Event is fired when postgres database was created.
        """
        logger.info("New PSQL database endpoint is %s", event.endpoints)
        host, port = event.endpoints.split(":")
        self._stored.db_host = host
        self._stored.db_port = port
        self._stored.db_user = event.username
        self._stored.db_password = event.password

        self._update_layer_and_restart(None)

    def _on_database_relation_removed(self, event) -> None:
        """Set stored states for database info to None and put charm into waiting status.

        Event is fired when relation with postgres is broken.
        """
        self._stored.db_host = None
        self._stored.db_port = None
        self._stored.db_user = None
        self._stored.db_password = None

        self.unit.status = WaitingStatus("Waiting for database relation")

    def _on_config_changed(self, _) -> None:
        """Update the port on which application is served.

        Just an example to show how to deal with changed configuration.

        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.yaml file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        port = self.config["server-port"]  # see config.yaml
        logger.debug("New application port is requested: %s", port)
        self._update_layer_and_restart(None)

    def _on_get_db_info_action(self, event) -> None:
        """Show information about database access points.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        event.set_results(
            {
                "db-username": self._stored.db_user,
                "db-password": self._stored.db_password,
                "db-host": self._stored.db_host,
                "db-port": self._stored.db_port,
            }
        )

    def _on_drop_table_action(self, event) -> None:
        """Call an API to remove (clean-up) a table in database.

        Update status of the action to fail if something goes wrong, otherwise pass a
        success message to the user.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        timeout = event.params["timeout"]  # see actions.yaml
        try:
            resp = requests.post(
                f"http://localhost:{self.config['server-port']}/deletetable", timeout=int(timeout)
            )
            if resp.status_code == 200:
                event.set_results({"success": "Database was dropped successfully."})
            else:
                event.fail(f"Request status code is: {resp.status_code}")
        except Exception as e:
            event.fail(f"Request failed: {e}")

    @property
    def version(self) -> str:
        """Reports the current workload (FastAPI app) version."""
        if self.container.can_connect() and self.container.get_services(self.pebble_service_name):
            try:
                return self._request_version()
            # Catching Exception is not ideal, but we don't care much for the error here, and just
            # default to setting a blank version since there isn't much the admin can do!
            except Exception as e:
                logger.warning("unable to get version from API: %s", str(e))
                logger.exception(e)
        return ""

    def _request_version(self) -> str:
        """Helper for fetching the version from the running workload using the API."""
        resp = requests.get(f"http://localhost:{self.config['server-port']}/version", timeout=10)
        return resp.json()["version"]


if __name__ == "__main__":
    main(FastAPIDemoCharm)
