"""HTTP routing checks that do not need to load the catalog."""

import unittest

import httpx

from server import app


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_standalone_get_is_not_a_stream(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url='http://127.0.0.1'
        ) as client:
            for accept in ('text/event-stream', 'application/json', '*/*'):
                with self.subTest(accept=accept):
                    response = await client.get('/mcp', headers={'Accept': accept})
                    self.assertEqual(response.status_code, 405)
                    self.assertNotIn(
                        'text/event-stream', response.headers.get('content-type', '')
                    )
