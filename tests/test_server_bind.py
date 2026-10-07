import unittest
from unittest.mock import patch
from customchat.server import LocalHTTPServer
from http.server import BaseHTTPRequestHandler

class BindTests(unittest.TestCase):
    def test_bind_never_reverse_resolves(self):
        with patch("socket.getfqdn", side_effect=AssertionError("reverse DNS must not be needed")):
            server = LocalHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
            try:
                self.assertEqual(server.server_name, "127.0.0.1")
                self.assertGreater(server.server_port, 0)
            finally:
                server.server_close()
