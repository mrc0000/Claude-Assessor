#!/usr/bin/env python3
"""Local development server for the Research Findings Explorer."""
import http.server
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), "webapp"))
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
print(f"Serving webapp at http://localhost:{port}")
http.server.test(http.server.SimpleHTTPRequestHandler, port=port)
