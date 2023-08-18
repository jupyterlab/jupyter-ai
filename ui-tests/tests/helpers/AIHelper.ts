import { expect, IJupyterLabPageFixture } from '@jupyterlab/galata';


enum SELECTORS {
  SIDEBAR = '.jp-SideBar.jp-mod-left[aria-label="main sidebar"]'
}

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
}