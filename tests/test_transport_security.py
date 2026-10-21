"""Security regressions for the public deployment's Host-validation incident."""

import json
import os
import subprocess
import sys
import unittest

from mcp.server.transport_security import TransportSecurityMiddleware
from starlette.requests import HTTPConnection

from server import security

PUBLIC = "web.01m5f5d50nb8hpd9peshkh4j5d.apps.springwinter.dev"
ALLOWLIST = ["localhost:*", "127.0.0.1:*", "[::1]:*", PUBLIC, PUBLIC + ":*"]


class SecurityConfigurationTests(unittest.TestCase):
    def test_validation_is_enabled(self):
        self.assertTrue(security.enable_dns_rebinding_protection)
        self.assertNotIn("*", security.allowed_hosts)
        self.assertNotIn("*", security.allowed_origins)

    def test_environment_allowlist_in_fresh_process(self):
        env = dict(
            os.environ, MCP_ALLOWED_HOSTS=", ".join(ALLOWLIST), MCP_ALLOWED_ORIGINS=""
        )
        code = "import json,server; print(json.dumps(server.security.model_dump()))"
        value = json.loads(
            subprocess.check_output([sys.executable, "-c", code], env=env, text=True)
        )
        self.assertEqual(value["allowed_hosts"], ALLOWLIST)
        self.assertEqual(value["allowed_origins"], [])
        self.assertTrue(value["enable_dns_rebinding_protection"])


class SecurityRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_host_origin_and_content_type(self):
        configured = security.model_copy(
            update={"allowed_hosts": ALLOWLIST, "allowed_origins": []}
        )
        middleware = TransportSecurityMiddleware(configured)
        for host, origin, content_type, expected in (
            (PUBLIC, None, "application/json", None),
            (PUBLIC + ":443", None, "application/json", None),
            ("localhost:8035", None, "application/json", None),
            ("127.0.0.1:8035", None, "application/json", None),
            ("[::1]:8035", None, "application/json", None),
            ("evil.example", None, "application/json", 421),
            (PUBLIC + ".evil.example", None, "application/json", 421),
            (PUBLIC, "https://evil.example", "application/json", 403),
            (PUBLIC, None, "text/plain", 400),
        ):
            with self.subTest(host=host, origin=origin, content_type=content_type):
                headers = [
                    (b"host", host.encode()),
                    (b"content-type", content_type.encode()),
                ]
                if origin:
                    headers.append((b"origin", origin.encode()))
                request = HTTPConnection({"type": "http", "headers": headers})
                response = await middleware.validate_request(request, is_post=True)
                self.assertEqual(response.status_code if response else None, expected)
