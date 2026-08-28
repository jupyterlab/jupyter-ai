/*
 * Copyright (c) Jupyter Development Team.
 * Distributed under the terms of the Modified BSD License.
 */

import { expect, galata, test } from '@jupyterlab/galata';
import { Page } from '@playwright/test';
import { UUID } from '@lumino/coreutils';

/**
 * End-to-end test for live content updates (``jupyter-live-content``).
 *
 * A plain-text file is opened in a FileEditor, then its bytes are changed
 * out-of-band -- via a separate contents-API request the open editor never made
 * -- and the editor's UI must pick up the new content on its own:
 *
 *   - default (RTC-free): ``jupyter-live-content`` watches the file's directory
 *     and reverts the clean editor when the on-disk content changes.
 *   - rtc / rtc-jsd: the RTC provider owns live document sync, so
 *     ``jupyter-live-content`` disables itself server-side. We assert both that
 *     the editor still updates (now driven by the provider) AND that
 *     ``jupyter-live-content`` reports that it disabled itself.
 *
 * The transport is selected by the ``e2e_live_content`` nox session, which sets
 * ``E2E_RTC=1`` for the rtc/rtc-jsd legs.
 */

const RTC = process.env.E2E_RTC === '1';
const TIMEOUT = 30000;

const TEST_DIR = 'live-content';
const INITIAL = 'first line\n';
const UPDATED = 'first line\nsecond line (out-of-band)\n';

// PageConfig key the server extension sets to `true` when it disabled itself
// because an RTC provider is active. Mirrors PAGE_CONFIG_DISABLED_KEY in
// jupyter_live_content/extension.py.
const DISABLED_KEY = 'liveContentServerDisabled';

/** Source text of the open document at `path`, or null if it is not open. */
function editorText(page: Page, docPath: string): Promise<string | null> {
  return page.evaluate((p: string) => {
    const app = (window as any).jupyterapp;
    for (const w of app.shell.widgets('main')) {
      const ctx = (w as any).context;
      if (ctx && ctx.path === p) {
        // YFile shared model; works for both the plain and collaborative model.
        return ctx.model.sharedModel.getSource();
      }
    }
    return null;
  }, docPath);
}

/**
 * Whether jupyter-live-content advertised (via PageConfig) that it disabled
 * itself. Read straight from the `jupyter-config-data` script the server
 * renders into the page.
 */
function liveContentDisabled(page: Page): Promise<boolean> {
  return page.evaluate((key: string) => {
    const el = document.getElementById('jupyter-config-data');
    if (!el || !el.textContent) {
      return false;
    }
    return String(JSON.parse(el.textContent)[key]) === 'true';
  }, DISABLED_KEY);
}

test.describe('live-content out-of-band updates', () => {
  test('an out-of-band disk edit updates the open file editor', async ({
    page,
    request,
    baseURL
  }) => {
    test.setTimeout(120_000);

    const filepath = `${TEST_DIR}/live-${UUID.uuid4()}.txt`;
    // A contents helper backed by the test's own request context: writes here
    // go straight to the server (and thus to disk), never through the open
    // editor -- exactly the out-of-band edit we want to exercise.
    const contents = galata.newContentsHelper(request);

    // Create the file, then open it in a FileEditor from a fresh workspace so
    // nothing else is restored into the shell.
    await contents.uploadContent(INITIAL, 'text', filepath);
    await page.goto(`${baseURL}/lab?reset`);
    await page.waitForSelector('#jupyterlab-splash', { state: 'detached' });
    await page.evaluate(async (p: string) => {
      await (window as any).jupyterapp.commands.execute('docmanager:open', {
        path: p,
        factory: 'Editor'
      });
    }, filepath);

    // The editor is open and shows the initial content.
    await expect
      .poll(() => editorText(page, filepath), { timeout: TIMEOUT })
      .toBe(INITIAL);

    // jupyter-live-content disables itself when an RTC provider owns live sync,
    // and is active otherwise.
    expect(await liveContentDisabled(page)).toBe(RTC);

    // Let the server establish its file watch (jupyter-live-content's awatch on
    // the open doc's directory, or the RTC provider's file loader) before we
    // change the file, so the modify event is not missed.
    await page.waitForTimeout(2000);

    // Change the bytes on disk out-of-band. The clean editor must reload on its
    // own -- via jupyter-live-content (default) or the RTC provider (rtc/rtc-jsd).
    await contents.uploadContent(UPDATED, 'text', filepath);

    await expect
      .poll(() => editorText(page, filepath), { timeout: TIMEOUT })
      .toBe(UPDATED);
  });
});
