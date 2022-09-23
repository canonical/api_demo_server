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
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class FastAPIDemoCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(
            self.on.demo_server_image_pebble_ready, self._on_demo_server_image_pebble_ready
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.drop_db_action, self._on_drop_db_action)
        self._stored.set_default(things=[])

    def _on_demo_server_image_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("fastapi_demo", self._pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()

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
                    "command": "uvicorn api_demo_server.app:app --reload --host=0.0.0.0",
                    "startup": "enabled",
                    "environment": {"DEMO_SERVER_DB_HOST": self.model.config["postgresip"]},
                }
            },
        }
        return Layer(pebble_layer)

    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.py file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        current = self.config["thing"]
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
        try:
            resp = requests.post("http://localhost:8000/dropdb", timeout=10)
            if resp.status_code == 200:
                event.set_results({"success": "Database was dropped successfully."})
            else:
                event.fail(f"Request status code is: {resp.status_code}")
        except Exception as e:
            event.fail(f"Request failed: {e}")

    @property
    def version(self) -> str:
        """Reports the current workload (FastAPI app) version."""
        container = self.unit.get_container("demo-server-image")
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
