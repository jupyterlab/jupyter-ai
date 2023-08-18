import { expect, test } from '@jupyterlab/galata';
import { AIHelper } from './helpers/AIHelper';

enum FILENAMES {
  SIDEBAR = 'sidebar.png',
  CHAT = 'chat.png'
}

/**
 * Don't load JupyterLab webpage before running the tests.
 * This is required to ensure we capture all log messages.
 */
test.use({ autoGoto: false });

test.describe('Jupyter AI', () => {
  let ai: AIHelper;
  test.beforeEach(async ({ page }) => {
    ai = new AIHelper(page);
    await page.goto();
  });

  test('shows sidebar chat icon', async () => {
    await ai.assertSnapshot(FILENAMES.SIDEBAR, { locator: ai.sidebar});
  });

  test('opens chat sidepanel', async () => {
    await ai.assertSnapshot(FILENAMES.CHAT);
  });
});
