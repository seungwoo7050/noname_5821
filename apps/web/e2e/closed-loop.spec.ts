import { mkdir } from "node:fs/promises";
import path from "node:path";

import { expect, test } from "@playwright/test";

const evidenceDir = path.resolve(process.cwd(), "../../output/playwright");

test.beforeAll(async () => {
  await mkdir(evidenceDir, { recursive: true });
});

test("Korean alias closes the published aggregate loop", async ({ page }) => {
  const search = await page.goto("/?query=샘플 게임");
  expect(search?.status()).toBe(200);
  await expect(page.getByRole("heading", { name: /검색 결과 1건/ })).toBeVisible();
  await page.getByRole("link", { name: /샘플 게임/ }).click();

  await expect(page).toHaveURL(/\/games\/11111111-1111-4111-8111-111111111111$/);
  await expect(page.getByRole("heading", { level: 1, name: "샘플 게임" })).toBeVisible();
  await expect(page.getByText("12시간", { exact: true })).toBeVisible();
  await expect(page.getByText("승인된 표본 3개 중앙값")).toBeVisible();
  await expect(page.getByText(/규칙 median-v1 · revision 1/)).toBeVisible();
  await expect(page.locator("body")).not.toContainText("20시간");
  await expect(page.locator("body")).not.toContainText("30분");
  await page.screenshot({ path: path.join(evidenceDir, "synthetic-detail.png"), fullPage: true });
});

test("original title resolves the same stable game identity", async ({ page }) => {
  await page.goto("/?query=Sample Game");
  const result = page.getByRole("link", { name: /샘플 게임/ });
  await expect(result).toHaveAttribute(
    "href",
    "/games/11111111-1111-4111-8111-111111111111",
  );
});

test("oversized search is rejected without a playtime claim", async ({ page }) => {
  const response = await page.goto(`/?query=${"x".repeat(101)}`);
  expect(response?.status()).toBe(400);
  await expect(page.getByRole("heading", { name: "검색어를 확인해 주세요" })).toBeVisible();
  await expect(page.locator(".duration")).toHaveCount(0);
});

test("backend unavailability is a controlled 503 with no guessed duration", async ({ page }) => {
  const response = await page.goto("http://127.0.0.1:4322/?query=샘플 게임");
  expect(response?.status()).toBe(503);
  await expect(page.getByRole("heading", { name: "데이터를 불러올 수 없습니다" })).toBeVisible();
  await expect(page.getByText(/참조 코드:/)).toBeVisible();
  await expect(page.locator("body")).not.toContainText("12시간");
  await page.screenshot({ path: path.join(evidenceDir, "backend-unavailable.png"), fullPage: true });
});

test("public and unauthenticated actors have no canonical write authority", async ({ page, request }) => {
  const mutation = await request.post("http://127.0.0.1:8000/api/v1/games", {
    data: { query: "샘플 게임" },
  });
  expect([403, 405]).toContain(mutation.status());

  await page.goto("http://127.0.0.1:8000/ops/catalog/playtimeobservation/");
  await expect(page).toHaveURL(/\/ops\/login\/\?next=/);
});
