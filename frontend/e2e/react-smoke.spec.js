import { expect, test } from "@playwright/test";

const backendUrl = process.env.ECOLOGIST_BACKEND_URL || "http://127.0.0.1:8000";
const managerCredentials = {
  username: process.env.ECOLOGIST_MANAGER_USERNAME || "manager_demo",
  password: process.env.ECOLOGIST_MANAGER_PASSWORD || "Manager12345!"
};
const adminCredentials = {
  username: process.env.ECOLOGIST_ADMIN_USERNAME || "admin_demo",
  password: process.env.ECOLOGIST_ADMIN_PASSWORD || "Admin12345!"
};

async function assertBackendReady(request) {
  const health = await request.get(`${backendUrl}/healthz/`);
  expect(
    health.ok(),
    `Django backend must be running at ${backendUrl}. Start runserver before E2E.`
  ).toBeTruthy();

  for (const credentials of [managerCredentials, adminCredentials]) {
    const response = await request.post(`${backendUrl}/api/v1/auth/token/`, {
      data: credentials
    });
    expect(
      response.status(),
      `Demo user ${credentials.username} must exist. Run: .venv\\Scripts\\python.exe manage.py seed_demo`
    ).toBe(200);
  }
}

async function login(page, credentials, expectedPath) {
  await page.goto("/login");
  await page.locator('input[autocomplete="username"]').fill(credentials.username);
  await page.locator('input[autocomplete="current-password"]').fill(credentials.password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(new RegExp(`${expectedPath.replace("/", "\\/")}$`));
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem("ecologist.refreshToken")))
    .not.toBeNull();
}

async function expectSpaPageLoaded(page, path, options = {}) {
  const { reload = false, navigate = true } = options;
  if (reload) {
    await page.goto(path);
  } else if (navigate) {
    const link = page.locator(`a[href="${path}"]`).first();
    if (await link.count()) {
      await link.click();
    } else {
      await page.evaluate((nextPath) => {
        window.history.pushState({}, "", nextPath);
        window.dispatchEvent(new PopStateEvent("popstate"));
      }, path);
    }
  }
  await expect(page).toHaveURL(new RegExp(`${path.replaceAll("/", "\\/")}$`));
  await expect(page.locator("main, .workspace, .admin-main").first()).toBeVisible();
  await expect(page.locator(".not-found-page")).toHaveCount(0);
  await expect(page.locator(".alert-danger")).toHaveCount(0);
}

test.describe("React manager smoke", () => {
  test.beforeAll(async ({ request }) => {
    await assertBackendReady(request);
  });

  test("anonymous dashboard request redirects to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("manager can open core pages and cannot open admin dashboard", async ({ page }) => {
    await login(page, managerCredentials, "/dashboard");
    await expectSpaPageLoaded(page, "/orders", { reload: true });

    for (const path of [
      "/dashboard",
      "/orders/create",
      "/trips",
      "/reports/emissions",
      "/archive",
      "/profile"
    ]) {
      await expectSpaPageLoaded(page, path);
    }

    await page.goto("/admin/dashboard");
    await expect(page.locator("body")).toContainText("Доступ ограничен");
  });
});

test.describe("React admin smoke", () => {
  test.beforeAll(async ({ request }) => {
    await assertBackendReady(request);
  });

  test("admin can open admin pages", async ({ page }) => {
    await login(page, adminCredentials, "/admin/dashboard");
    await expectSpaPageLoaded(page, "/admin/users", { reload: true });

    for (const path of [
      "/admin/dashboard",
      "/admin/archive",
      "/admin/transports",
      "/admin/locations",
      "/admin/eco-standards",
      "/admin/calculation-settings",
      "/admin/profile"
    ]) {
      await expectSpaPageLoaded(page, path);
    }
  });

  test("Django Admin remains reachable on backend", async ({ request }) => {
    const response = await request.get(`${backendUrl}/admin/`, {
      maxRedirects: 0
    });
    expect([200, 302]).toContain(response.status());
  });
});
