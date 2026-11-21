"""Isolated HTTP server for browser regression tests. Never opens the user's DB."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory(prefix='finz-workflow-') as directory:
    os.environ['FINZ_PROTOTYPE_DATA_DIR'] = directory
    os.environ['AI_PROVIDER'] = 'disabled'
    import server
    httpd = server.ThreadingHTTPServer(('127.0.0.1', 5193), server.Handler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
