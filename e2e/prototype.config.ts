import { defineConfig } from '@playwright/test';
export default defineConfig({
 testDir:'./prototype', workers:1, fullyParallel:false,
 use:{baseURL:'http://127.0.0.1:5193',channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'},
 webServer:{command:'../services/api/.venv/bin/python ../prototype/tests/_browser_server.py',url:'http://127.0.0.1:5193/api/health',reuseExistingServer:false},
 timeout:30000,
});
