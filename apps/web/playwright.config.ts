import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "../../output/playwright/test-results",
  reporter: "line",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:4321",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "cd ../backend && DJANGO_SECRET_KEY=$(openssl rand -hex 32) DJANGO_DEBUG=1 UV_CACHE_DIR=../../.cache/uv uv run python manage.py runserver 127.0.0.1:8000 --noreload",
      url: "http://127.0.0.1:8000/api/v1/viability",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command:
        "HOST=127.0.0.1 PORT=4321 API_BASE_URL=http://127.0.0.1:8000 node ./dist/server/entry.mjs",
      url: "http://127.0.0.1:4321/",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command:
        "HOST=127.0.0.1 PORT=4322 API_BASE_URL=http://127.0.0.1:65530 node ./dist/server/entry.mjs",
      url: "http://127.0.0.1:4322/",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
