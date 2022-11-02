#!/usr/bin/env python3
# Copyright 2022 Dylan Stephano-Shachter
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

from charms.tls_certificates_interface.v1.tls_certificates import CertificateRevocationRequestEvent

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]


class CertbotCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.httpbin_pebble_ready, self._on_httpbin_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.certs = TLSCertificatesProvidesV1(self, "certificates")
        self.framework.observe(self.certs.on.certificate_request, self._on_cert_request)

    def _on_cert_request(self, event):
        csr = event.certificate_signing_request
        container = self.model.get_container("certbot")
        if container.can_connect():
            if not container.exists("/root/google-creds.json"):
                event.defer()
                return
            container.push("/tmp/csr", csr)
            process = self.model.exec(["certbot", "--test-cert", "--csr", "/tmp/csr", "--dns-google-credencials", google_creds, "--dns-google"])
            process.wait_output()
            cert = /etc/letsencrypt/staging/<domain>/
        else event.defer()


    def _pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        Change this example to suit your needs. You'll need to specify the right entrypoint and
        environment configuration for your specific workload.

        Learn more about interacting with Pebble at at https://juju.is/docs/sdk/pebble.
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("httpbin", self._pebble_layer, combine=True)
        # Make Pebble reevaluate its plan, ensuring any services are started if enabled.
        container.replan()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event):
        """Handle changed configuration.

        Change this example to suit your needs. If you don't need to handle config, you can remove
        this method.

        Learn more about config at https://juju.is/docs/sdk/config
        """

        # The config is good, so update the configuration of the workload
        container = self.unit.get_container("certbot")
        # Verify that we can connect to the Pebble API in the workload container
        if container.can_connect():
            google_creds_json = self.model.config.get("google-creds-json")
            if google_creds_json is not None:
                container.push("/root/google-creds.json", google_creds_json)
            # Push an updated layer with the new config
            self.unit.status = ActiveStatus()
        else:
            # We were unable to connect to the Pebble API, so we defer this event
            event.defer()
            self.unit.status = WaitingStatus("waiting for Pebble API")



if __name__ == "__main__":  # pragma: nocover
    main(CertbotCharm)
