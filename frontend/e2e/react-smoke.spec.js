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

async function expectNoMojibake(page) {
  const text = await page.locator("body").innerText();
  expect(text).not.toContain("Рџ");
  expect(text).not.toContain("Р”");
  expect(text).not.toContain("С‚");
}

test.describe("React auth smoke", () => {
  test.beforeAll(async ({ request }) => {
    await assertBackendReady(request);
  });

  test("login and registration screens match Russian auth flow", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Войти" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Регистрация" })).toBeVisible();
    await expect(page.getByPlaceholder("Имя пользователя или email")).toBeVisible();
    await expectNoMojibake(page);

    await page.getByRole("link", { name: "Зарегистрироваться" }).click();
    await expect(page).toHaveURL(/\/register$/);
    await expect(page.getByRole("heading", { name: "Регистрация менеджера" })).toBeVisible();
    await expect(page.getByLabel("Уникальный никнейм")).toBeVisible();
    await expect(page.getByPlaceholder("+7 (999) 123-45-67")).toBeVisible();
    await expectNoMojibake(page);

    await page.getByLabel("Уникальный никнейм").fill(managerCredentials.username);
    await page.getByLabel("Email").fill("manager@example.com");
    await page.locator('input[name="password1"]').fill("Manager12345!");
    await page.locator('input[name="password2"]').fill("Manager12345!");
    await page.getByRole("button", { name: "Зарегистрироваться" }).click();
    await expect(page.getByRole("button", { name: "Зарегистрироваться" })).toBeEnabled();
    await expect(page.getByText("Пользователь с таким никнеймом уже зарегистрирован")).toBeVisible();
    await expect(page.getByText("Пользователь с таким email уже зарегистрирован")).toBeVisible();
    await expectNoMojibake(page);
  });
});

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
      "/analytics",
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
