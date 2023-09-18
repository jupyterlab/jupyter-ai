import { expect, IJupyterLabPageFixture } from '@jupyterlab/galata';
import type { Locator } from '@playwright/test';

enum SELECTORS {
  SIDEBAR = '.jp-SideBar.jp-mod-left[aria-label="main sidebar"]',
  CHAT_PANEL = '#jupyter-ai\\:\\:chat',
  CHAT_ICON = '[title="Jupyter AI Chat"]'
}

type SnapshotOptions = {
  /**
   * Crops the screenshot to a locator. Uses the chat sidepanel
   * locator by default.
   */
  locator?: Locator;
};

/**
 *  Helper class for Jupyter AI testing in JupyterLab
 */
export class AIHelper {
  constructor(readonly page: IJupyterLabPageFixture) {}

  /**
   *  Locates left sidebar
   */
  get sidebar() {
    return this.page.locator(SELECTORS.SIDEBAR);
  }

  /**
   *  Locates Jupyter AI chat panel
   */
  get chat() {
    return this.page.locator(SELECTORS.CHAT_PANEL);
  }

  /**
   *  Locates Jupyter AI chat icon
   */
  get chatIcon() {
    return this.page.locator(SELECTORS.CHAT_ICON);
  }

  /**
   *  Opens Jupyter AI chat sidepanel if it is closed
   */
  async openChatPanel() {
    if (!(await this.chat.isVisible())) {
      await this.chatIcon.click();
    }
  }

  /**
   * Asserts a screenshot against the snapshot at `filename`. By default,
   * crops the screenshot to the chat sidepanel. See `SnapshotOptions` for
   * more configuration options.
   */
  async assertSnapshot(
    filename: string,
    customOpts?: Partial<SnapshotOptions>
  ) {
    const opts: SnapshotOptions = { ...customOpts };
    const target = opts.locator ?? (this.openChatPanel(), this.chat);
    await target.waitFor({ state: 'visible' });
    expect(await target.screenshot()).toMatchSnapshot(filename);
  }
}
