#!/usr/bin/env python3
"""Run the pinned native Shinka viewer with concurrent browser connections.

The pinned viewer uses a single-connection TCPServer. A browser's idle preopened
socket can therefore block every HTTP request. Change only its HTTP transport;
the native pages, request handlers and actual database remain unchanged.
"""
import socketserver
from types import SimpleNamespace

from shinka.webui import visualization


class BrowserTCPServer(socketserver.ThreadingTCPServer):
    daemon_threads = True


if __name__ == "__main__":
    # Limit the substitution to the viewer module; do not change stdlib bases.
    visualization.socketserver = SimpleNamespace(TCPServer=BrowserTCPServer)
    visualization.main()
