import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(frontendDir, '..');
const localPython = path.join(projectDir, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const python = process.env.PYTHON || (existsSync(localPython) ? localPython : 'python');
const apiPort = process.env.P2_E2E_API_PORT || '8000';
const webPort = process.env.P2_E2E_WEB_PORT || '5173';
const webOrigin = `http://localhost:${webPort}`;
const apiOrigin = `http://localhost:${apiPort}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: { ...devices['Desktop Chrome'], baseURL: webOrigin },
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
      cwd: path.join(projectDir, 'backend'),
      url: `${apiOrigin}/health/live`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { DATABASE_URL: process.env.P2_E2E_DATABASE_URL || 'sqlite:///./p2-e2e.db', MODEL_BACKEND: 'deterministic_test', CORS_ORIGINS: `${webOrigin},http://127.0.0.1:${webPort}` },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${webPort}`,
      cwd: frontendDir,
      url: webOrigin,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { VITE_API_URL: apiOrigin },
    },
  ],
});
