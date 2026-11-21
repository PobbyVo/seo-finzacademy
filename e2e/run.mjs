import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, rm } from 'node:fs/promises';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const python = process.env.FINZ_PYTHON ?? join(root, 'services/api/.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const next = join(root, 'apps/web/node_modules/next/dist/bin/next');
const playwright = join(root, 'e2e/node_modules/@playwright/test/cli.js');
const apiPort = Number(process.env.E2E_API_PORT ?? 18000);
const webPort = Number(process.env.E2E_WEB_PORT ?? 13000);
const apiURL = `http://127.0.0.1:${apiPort}`;
const webURL = `http://127.0.0.1:${webPort}`;
const children = [];
let temporaryDirectory;
let stopping = false;

function start(command, args, env, name, inherit = false) {
  const child = spawn(command, args, {
    cwd: root,
    env,
    detached: process.platform !== 'win32',
    stdio: inherit ? 'inherit' : ['ignore', 'pipe', 'pipe'],
  });
  const entry = { child, name, output: '' };
  children.push(entry);
  if (!inherit) {
    for (const stream of [child.stdout, child.stderr]) {
      stream.on('data', data => { entry.output = (entry.output + data).slice(-20_000); });
    }
  }
  entry.finished = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', (code, signal) => resolve({ code, signal }));
  });
  // Retain rejection for the awaited startup/readiness step without unhandled events.
  entry.finished.catch(() => {});
  return entry;
}

async function assertPortAvailable(port) {
  const server = createServer();
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', resolve);
  });
  await new Promise(resolve => server.close(resolve));
}

async function waitForURL(url, entry) {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    if (entry.child.exitCode !== null || entry.child.signalCode) {
      throw new Error(`${entry.name} đã dừng trước khi sẵn sàng.\n${entry.output}`);
    }
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1_000) });
      if (response.ok) return;
    } catch { /* Server is still starting. */ }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Hết thời gian chờ ${url}.\n${entry.output}`);
}

async function cleanup() {
  if (stopping) return;
  stopping = true;
  for (const { child } of children.toReversed()) {
    if (!child.pid || child.exitCode !== null || child.signalCode) continue;
    try {
      if (process.platform === 'win32') child.kill('SIGTERM');
      else process.kill(-child.pid, 'SIGTERM');
    } catch { /* Process already exited. */ }
  }
  await Promise.all(children.map(async ({ child, finished }) => {
    if (child.exitCode !== null || child.signalCode) return;
    await Promise.race([finished.catch(() => {}), new Promise(resolve => setTimeout(resolve, 2_000))]);
    if (child.exitCode === null && !child.signalCode && child.pid) {
      try {
        if (process.platform === 'win32') child.kill('SIGKILL');
        else process.kill(-child.pid, 'SIGKILL');
      } catch { /* Process already exited. */ }
    }
  }));
  if (temporaryDirectory) await rm(temporaryDirectory, { recursive: true, force: true });
}

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.once(signal, async () => { await cleanup(); process.exit(130); });
}

try {
  for (const file of [python, next, playwright]) {
    if (!existsSync(file)) throw new Error(`Thiếu dependency: ${file}. Hãy chạy bước cài đặt trong README.`);
  }
  if (apiPort === webPort) throw new Error('E2E_API_PORT và E2E_WEB_PORT phải khác nhau.');
  await assertPortAvailable(apiPort);
  await assertPortAvailable(webPort);
  temporaryDirectory = await mkdtemp(join(tmpdir(), 'finz-m0-e2e-'));
  const args = process.argv.slice(2).filter(argument => argument !== '--chrome');
  const chromeAvailable = existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
  const env = {
    ...process.env,
    LLM_PROVIDER: 'mock',
    AI_GATEWAY_MODE: 'mock',
    DATABASE_URL: `sqlite:///${join(temporaryDirectory, 'e2e.sqlite3')}`,
    API_BASE_URL: apiURL,
    NEXT_DIST_DIR: '.next-e2e',
    NEXT_TELEMETRY_DISABLED: '1',
    E2E_BASE_URL: webURL,
    E2E_EXPECT_EMPTY: '1',
    PLAYWRIGHT_CHANNEL: process.env.PLAYWRIGHT_CHANNEL || (process.argv.includes('--chrome') || chromeAvailable ? 'chrome' : ''),
  };
  console.log('M0 E2E: SQLite tạm riêng; API', apiURL, '; Web', webURL);
  const migration = start(python, ['-m', 'alembic', '-c', 'services/api/alembic.ini', 'upgrade', 'head'], env, 'Alembic');
  const migrated = await migration.finished;
  if (migrated.code !== 0) throw new Error(`Migration thất bại.\n${migration.output}`);
  const api = start(python, ['-m', 'uvicorn', 'finz_api.main:app', '--app-dir', 'services/api', '--host', '127.0.0.1', '--port', String(apiPort)], env, 'FastAPI');
  await waitForURL(`${apiURL}/health`, api);
  const web = start(process.execPath, [next, 'dev', 'apps/web', '--hostname', '127.0.0.1', '--port', String(webPort)], env, 'Next.js');
  await waitForURL(`${webURL}/projects`, web);
  const tests = start(process.execPath, [playwright, 'test', '--config', 'e2e/playwright.config.ts', ...args], env, 'Playwright', true);
  const result = await tests.finished;
  if (result.code !== 0) {
    console.error('FastAPI output:\n' + api.output);
    console.error('Next.js output:\n' + web.output);
  }
  process.exitCode = result.code ?? 1;
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
} finally {
  await cleanup();
}
