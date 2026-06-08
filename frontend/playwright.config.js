import { defineConfig, devices } from "@playwright/test";

const frontendBaseUrl = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174";
const viteCommand = "node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174 --strictPort";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000
  },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: frontendBaseUrl,
    trace: "on-first-retry"
  },
  webServer: {
    command: viteCommand,
    url: frontendBaseUrl,
    reuseExistingServer: true,
    timeout: 120_000
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
