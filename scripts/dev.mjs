import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import { dirname, join, resolve } from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const apiDirectory = join(root, 'services/api');
const webDirectory = join(root, 'apps/web');
const python = process.env.FINZ_PYTHON ?? join(apiDirectory, '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const next = join(webDirectory, 'node_modules/next/dist/bin/next');
const env = { ...process.env, NEXT_TELEMETRY_DISABLED: '1', API_BASE_URL: 'http://127.0.0.1:8000' };
const children = [];
let stopping = false;
let cleanupPromise;

function start(name, command, args, cwd) {
  const child = spawn(command, args, {
    cwd, env, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'],
  });
  const entry = { child, name };
  children.push(entry);
  for (const stream of [child.stdout, child.stderr]) {
    createInterface({ input: stream }).on('line', line => console.log(`[${name}] ${line}`));
  }
  entry.finished = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', (code, signal) => resolve({ code, signal }));
  });
  entry.finished.catch(() => {});
  return entry;
}

function signalGroup(entry, signal) {
  if (!entry.child.pid) return;
  try {
    if (process.platform === 'win32') entry.child.kill(signal);
    else process.kill(-entry.child.pid, signal);
  } catch (error) {
    if (error.code !== 'ESRCH') console.error(`[${entry.name}] ${error.message}`);
  }
}

function cleanup() {
  if (cleanupPromise) return cleanupPromise;
  stopping = true;
  cleanupPromise = (async () => {
    for (const entry of children.toReversed()) signalGroup(entry, 'SIGTERM');
    await Promise.race([
      Promise.allSettled(children.map(entry => entry.finished)),
      new Promise(resolve => setTimeout(resolve, 2000)),
    ]);
    for (const entry of children.toReversed()) signalGroup(entry, 'SIGKILL');
  })();
  return cleanupPromise;
}

async function assertPortAvailable(port) {
  const server = createServer();
  try {
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(port, '127.0.0.1', resolve);
    });
  } catch (error) {
    if (error.code === 'EADDRINUSE') {
      throw new Error(`Cổng ${port} đang được sử dụng. Dừng server cũ rồi chạy lại npm run dev.`);
    }
    throw error;
  }
  await new Promise(resolve => server.close(resolve));
}

async function waitForHealth(entry) {
  const deadline = Date.now() + 30_000;
  while (!stopping && Date.now() < deadline) {
    if (entry.child.exitCode !== null || entry.child.signalCode) {
      throw new Error('Backend đã dừng trước khi sẵn sàng; xem log BE ở trên.');
    }
    try {
      const response = await fetch('http://127.0.0.1:8000/health', {
        signal: AbortSignal.timeout(1000),
      });
      if (response.ok) return;
    } catch { /* Backend is starting. */ }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('Backend chưa sẵn sàng; xem log BE ở trên.');
}

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, async () => {
    if (stopping) return;
    console.log('\nĐang dừng frontend và backend…');
    await cleanup();
    process.exit(signal === 'SIGINT' ? 130 : 143);
  });
}

try {
  if (!existsSync(python) || !existsSync(next)) {
    throw new Error('Thiếu Python .venv hoặc thư viện Next.js. Cài dependencies theo README.md trước.');
  }
  await assertPortAvailable(8000);
  await assertPortAvailable(3000);
  const migration = start('DB', python, ['-m', 'alembic', 'upgrade', 'head'], apiDirectory);
  if ((await migration.finished).code !== 0) throw new Error('Migration thất bại; xem log DB ở trên.');
  const backend = start('BE', python, ['-m', 'uvicorn', 'finz_api.main:app',
    '--host', '127.0.0.1', '--port', '8000', '--reload'], apiDirectory);
  await waitForHealth(backend);
  const frontend = start('FE', process.execPath,
    [next, 'dev', '--hostname', '127.0.0.1', '--port', '3000'], webDirectory);
  console.log('\nFrontend: http://127.0.0.1:3000/projects');
  console.log('Backend:  http://127.0.0.1:8000/health');
  console.log('Nhấn Ctrl+C để dừng cả hai.\n');
  const result = await Promise.race([backend.finished, frontend.finished]);
  if (!stopping) {
    console.error('Một server đã dừng; đang dừng server còn lại.');
    process.exitCode = result.code || 1;
  }
} catch (error) {
  if (!stopping) console.error(error.message);
  process.exitCode = 1;
} finally {
  await cleanup();
}
