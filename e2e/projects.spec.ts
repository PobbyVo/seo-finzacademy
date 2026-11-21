import { expect, test, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const fixture = JSON.parse(
  readFileSync(resolve(__dirname, '../fixtures/taxonomy_multi_topic.demo.json'), 'utf8'),
) as {
  topics: Array<{ topic_code: string; topic_name: string }>;
  content_codes: Array<{ topic_code: string; content_code: string }>;
  source_keywords: Array<{
    topic_code: string;
    keyword: string;
    role: string;
    funnel: string;
  }>;
};

async function createProject(page: Page, name: string) {
  await page.getByLabel('Tên dự án', { exact: true }).fill(name);
  await page.getByRole('button', { name: 'Tạo dự án', exact: true }).click();
  await expect(page.getByRole('button', { name: `Mở dự án ${name}`, exact: true }))
    .toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByRole('heading', { name: 'Dự án chưa có dữ liệu chủ đề' }))
    .toBeVisible();
}

async function loadDemo(page: Page, code: string) {
  await expect(page.getByLabel('Chủ đề demo', { exact: true })).toHaveValue('');
  await page.getByLabel('Chủ đề demo', { exact: true }).selectOption(code);
  const loaded = page.waitForResponse(
    response => response.url().endsWith('/demo') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Nạp demo', exact: true }).click();
  expect((await loaded).ok()).toBe(true);
  const topic = fixture.topics.find(topic => topic.topic_code === code)!;
  await expect(page.getByRole('heading', { name: `${code} · ${topic.topic_name}` }))
    .toBeVisible();
}

test('explicit demo, independent SQLite projects, reload and mobile layout', async ({ page, request }) => {
  const pageErrors: string[] = [];
  const externalRequests: string[] = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('request', request => {
    const url = new URL(request.url());
    if (['http:', 'https:'].includes(url.protocol) && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) {
      externalRequests.push(request.url());
    }
  });

  if (process.env.E2E_EXPECT_EMPTY === '1') {
    const response = await request.get('/api/v1/projects');
    expect(response.ok()).toBe(true);
    const body: unknown = await response.json();
    expect(Array.isArray(body) ? body : (body as { projects: unknown[] }).projects).toEqual([]);
  }

  await page.goto('/');
  await expect(page).toHaveURL(/\/projects(?:\?.*)?$/);
  await expect(page.getByText('DEMO - CHƯA PHÂN TÍCH AI THỰC', { exact: true })).toBeVisible();

  const suffix = `${Date.now()}-${test.info().workerIndex}`;
  const firstName = `M0 P01 ${suffix}`;
  const secondName = `M0 P08 ${suffix}`;
  await createProject(page, firstName);
  await expect(page.getByRole('button', { name: 'Nạp demo', exact: true })).toBeDisabled();
  await loadDemo(page, 'P01');

  const table = page.getByRole('table', { name: 'Từ khóa nguồn demo' });
  await expect(table).toBeVisible();
  const sourceKeywords = fixture.source_keywords.filter(keyword => keyword.topic_code === 'P01');
  await expect(table.getByRole('row')).toHaveCount(sourceKeywords.length + 1);
  for (const keyword of sourceKeywords) {
    const row = table.getByRole('row').filter({ hasText: keyword.keyword });
    await expect(row).toContainText(keyword.role);
    await expect(row).toContainText(keyword.funnel);
    await expect(row.getByRole('cell', { name: 'Chưa có dữ liệu', exact: true })).toHaveCount(4);
  }
  for (const code of fixture.content_codes.filter(code => code.topic_code === 'P01')) {
    await expect(page.getByText(code.content_code, { exact: true }).first()).toBeVisible();
  }

  await createProject(page, secondName);
  await expect(page.getByRole('table', { name: 'Từ khóa nguồn demo' })).toHaveCount(0);
  await loadDemo(page, 'P08');
  await page.getByRole('button', { name: `Mở dự án ${firstName}`, exact: true }).click();
  await expect(table).toBeVisible();
  await expect(table.getByRole('row')).toHaveCount(sourceKeywords.length + 1);
  await page.reload();
  await page.getByRole('button', { name: `Mở dự án ${firstName}`, exact: true }).click();
  await expect(table).toBeVisible();
  await page.getByRole('button', { name: `Mở dự án ${secondName}`, exact: true }).click();
  const secondTopic = fixture.topics.find(topic => topic.topic_code === 'P08')!;
  await expect(page.getByRole('heading', { name: `P08 · ${secondTopic.topic_name}` })).toBeVisible();
  await page.getByRole('button', { name: `Mở dự án ${firstName}`, exact: true }).click();
  await expect(table).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('projects-desktop.png'), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByLabel('Tên dự án', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('projects-mobile.png'), fullPage: true });
  expect(pageErrors).toEqual([]);
  expect(externalRequests).toEqual([]);
});

test('API connection failure is visible and retry recovers', async ({ page }) => {
  await page.route('**/api/v1/**', route => route.abort('connectionfailed'));
  await page.goto('/projects');
  const applicationAlert = page.getByRole('main').getByRole('alert');
  await expect(applicationAlert).toBeVisible();
  const retry = page.getByRole('button', { name: 'Thử kết nối lại', exact: true });
  await expect(retry).toBeVisible();
  await page.unroute('**/api/v1/**');
  await retry.click();
  await expect(applicationAlert).toHaveCount(0);
  await expect(page.getByLabel('Tên dự án', { exact: true })).toBeEnabled();
});
