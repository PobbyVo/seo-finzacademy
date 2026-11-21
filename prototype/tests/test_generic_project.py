"""Compatibility entrypoint for the real HTTP/SQLite browser regression."""
from pathlib import Path
import subprocess

def run_browser_test():
    root = Path(__file__).resolve().parents[2]
    subprocess.run(['npm', '--prefix', 'e2e', 'exec', '--', 'playwright', 'test',
                    '--config', 'e2e/prototype.config.ts', '--grep', 'generic save'], cwd=root, check=True)

if __name__ == '__main__':
    run_browser_test()
