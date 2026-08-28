/*
 * Copyright (c) Jupyter Development Team.
 * Distributed under the terms of the Modified BSD License.
 */

import {
  expect,
  galata,
  IJupyterLabPageFixture,
  test as galataTest
} from '@jupyterlab/galata';
import { APIRequestContext, Page } from '@playwright/test';
import { UUID } from '@lumino/coreutils';
import * as fs from 'fs';
import * as path from 'path';

// Disable galata's kernel/session mocking. The routed command opens a real
// notebook, which starts a kernel session; galata's mock intercepts
// `/api/sessions` through its APIRequestContext, and that proxy is disposed at
// test teardown while the session request is still in flight — surfacing as
// "apiRequestContext.fetch: Request context disposed" under the RTC/JSD
// providers. Talking to the real server directly avoids the racing proxy.
const test = galataTest.extend({
  kernels: null,
  sessions: null
});

/**
 * End-to-end test for web-client command routing (jupyterlab/jupyter-ai#1650).
 *
 * Two separate web clients each run the same AI persona in their own chat and
 * send a different message describing a notebook to build. The persona (see
 * fixtures/personas/mcp-notebook_persona.py) asks the built-in Jupyter MCP
 * server to run the `e2e:build-notebook` frontend command, which must be routed
 * to only the web client that sent the triggering message.
 *
 * We assert the end state differs per client: client 1 has only its notebook
 * (with exactly the cells it asked for) and client 2 has only its own. Without
 * routing the command broadcasts and both clients build both notebooks — the
 * original bug this guards against.
 *
 * NOTE: this passes only against jupyter-server-mcp and jupyter-ai-persona-manager
 * builds that include the routing changes; against released builds without them
 * the command broadcasts and the test fails (reproducing the bug).
 */

const TEST_DIR = 'mcp-routing';
const PERSONA_FILE = 'mcp-notebook_persona.py';
const PERSONAS_SRC = path.resolve(__dirname, '..', 'fixtures', 'personas');

const INPUT = '.jp-chat-input-container';
const SEND = `${INPUT} .jp-chat-send-button`;
const MESSAGE = '.jp-chat-rendered-message';
const TIMEOUT = 30000;

// Each client's request: a notebook name and its code cells.
const CLIENT1 = { notebook: 'client1.ipynb', cells: ['a = 1\nprint(a)'] };
const CLIENT2 = { notebook: 'client2.ipynb', cells: ['b = 2\nprint(b)', 'c = 3'] };

/** Wait until a JupyterLab page has finished loading. */
async function waitForApplication(page: Page): Promise<void> {
  await page.waitForSelector('#jupyterlab-splash', { state: 'detached' });
}

async function installPersona(request: APIRequestContext): Promise<void> {
  const contents = galata.newContentsHelper(request);
  const src = fs.readFileSync(path.join(PERSONAS_SRC, PERSONA_FILE), 'utf-8');
  const ok = await contents.uploadContent(
    src,
    'text',
    `${TEST_DIR}/.jupyter/personas/${PERSONA_FILE}`
  );
  if (!ok) {
    throw new Error('Failed to install the MCP Notebook fixture persona');
  }
}

/**
 * Register the `e2e:build-notebook` command in a browser: create the notebook
 * with the given code cells, open it, and run all cells. Registered in *both*
 * clients so the toolkit's routing guard — not the command's absence — decides
 * which browser actually runs it.
 */
async function registerBuildCommand(
  page: IJupyterLabPageFixture
): Promise<void> {
  await page.evaluate(() => {
    const app = (window as any).jupyterapp;
    if (app.commands.hasCommand('e2e:build-notebook')) {
      return;
    }
    app.commands.addCommand('e2e:build-notebook', {
      label: 'E2E: build notebook',
      execute: async (args: any) => {
        const nbPath = args.path as string;
        const cells = (args.cells as string[]) || [];
        const content = {
          cells: cells.map(source => ({
            cell_type: 'code',
            source,
            metadata: {},
            outputs: [],
            execution_count: null
          })),
          metadata: { kernelspec: { name: 'python3', display_name: 'Python 3' } },
          nbformat: 4,
          nbformat_minor: 5
        };
        await app.serviceManager.contents.save(nbPath, {
          type: 'notebook',
          format: 'json',
          content
        });
        await app.commands.execute('docmanager:open', { path: nbPath });
        // Intentionally do not run the notebook: the test asserts routing and
        // the notebook's cell contents, not execution. Running all cells starts
        // a kernel session whose async lifecycle races test teardown under the
        // JSD provider ("Request context disposed").
      }
    });
  });
}

/** Open a fresh chat under TEST_DIR (the fixture persona is the default). */
async function openChat(page: IJupyterLabPageFixture): Promise<void> {
  const filepath = `${TEST_DIR}/chat-${UUID.uuid4()}.chat`;
  await page.filebrowser.contents.uploadContent('{}', 'text', filepath);
  await page.evaluate(async (name: string) => {
    await (window as any).jupyterapp.commands.execute('jupyterlab-chat:open', {
      filepath: name
    });
  }, filepath);
  // Only one chat is open per page, so page-scoped locators are unambiguous.
  await expect(page.locator(INPUT)).toBeVisible({ timeout: TIMEOUT });
}

/** Send a message and wait for the persona's reply to render. */
async function sendMessage(
  page: IJupyterLabPageFixture,
  text: string
): Promise<void> {
  const before = await page.locator(MESSAGE).count();
  const input = page.locator(INPUT).getByRole('combobox');
  // Focus the chat input before typing: a notebook opened by an earlier routed
  // command can hold focus, so the keystrokes would otherwise miss the input
  // and leave the send button disabled.
  await input.click();
  await input.pressSequentially(text);
  // The send button enables once the input has content and the model is ready;
  // wait for it rather than racing the click.
  await expect(page.locator(SEND)).toBeEnabled({ timeout: TIMEOUT });
  await page.locator(SEND).click();
  // Human echo + persona reply.
  await expect
    .poll(async () => page.locator(MESSAGE).count(), { timeout: TIMEOUT })
    .toBeGreaterThanOrEqual(before + 2);
}

/** The paths of the documents open in this browser's main area. */
function openDocPaths(page: IJupyterLabPageFixture): Promise<string[]> {
  return page.evaluate(() => {
    const app = (window as any).jupyterapp;
    const paths: string[] = [];
    for (const w of app.shell.widgets('main')) {
      const ctx = (w as any).context;
      if (ctx && ctx.path) {
        paths.push(ctx.path);
      }
    }
    return paths;
  });
}

/** The source of each cell in the open notebook at `nbPath`, or null. */
function notebookCells(
  page: IJupyterLabPageFixture,
  nbPath: string
): Promise<string[] | null> {
  return page.evaluate((p: string) => {
    const app = (window as any).jupyterapp;
    for (const w of app.shell.widgets('main')) {
      const ctx = (w as any).context;
      if (ctx && ctx.path === p) {
        const model = (w as any).content?.model;
        if (!model) {
          return null;
        }
        const out: string[] = [];
        for (let i = 0; i < model.cells.length; i++) {
          out.push(model.cells.get(i).sharedModel.getSource());
        }
        return out;
      }
    }
    return null;
  }, nbPath);
}

test.describe('mcp web-client routing', () => {
  test.beforeAll(async ({ request }) => {
    await installPersona(request);
  });

  test('a command runs only on the client whose message triggered it', async ({
    page,
    browser,
    baseURL
  }) => {
    test.setTimeout(120_000);

    // Client 1 is the galata page fixture; client 2 is a second galata page in
    // its own browser context (each fixture resets its own workspace).
    // mockKernels/mockSessions are disabled to match the fixture (kernels/
    // sessions: null): the routed command opens a real notebook that starts a
    // kernel session, and galata's in-memory session mock proxies /api/sessions
    // through an APIRequestContext that is disposed at teardown while the
    // request is in flight ("apiRequestContext.fetch: Request context
    // disposed"). Talking to the real server directly avoids that race.
    const { page: page2 } = await galata.newPage({
      baseURL: baseURL as string,
      browser,
      waitForApplication,
      mockKernels: false,
      mockSessions: false
    });

    // Give each client a fresh workspace. JupyterLab persists open-document
    // layout server-side, so a notebook opened by one client's routed command
    // can be restored into the other client on load and steal focus from its
    // chat input (leaving the send button disabled). Reset before registering
    // the command — a reload clears commands added via app.commands.addCommand.
    await page.goto(`${baseURL}/lab?reset`);
    await waitForApplication(page);
    await page2.goto(`${baseURL}/lab?reset`);
    await waitForApplication(page2);

    await registerBuildCommand(page);
    await registerBuildCommand(page2);

    await openChat(page);
    await openChat(page2);

    // Each client asks its own persona (in its own chat) to build its notebook.
    await sendMessage(page, JSON.stringify(CLIENT1));
    await sendMessage(page2, JSON.stringify(CLIENT2));

    // Client 1 has ONLY its notebook; client 2 has ONLY its own.
    await expect
      .poll(() => openDocPaths(page), { timeout: TIMEOUT })
      .toContain(CLIENT1.notebook);
    expect(await openDocPaths(page)).not.toContain(CLIENT2.notebook);

    await expect
      .poll(() => openDocPaths(page2), { timeout: TIMEOUT })
      .toContain(CLIENT2.notebook);
    expect(await openDocPaths(page2)).not.toContain(CLIENT1.notebook);

    // Each got exactly the cells it asked for. Poll rather than assert once:
    // under RTC the notebook content arrives asynchronously from the Yjs room
    // (the doc is open with its path before the room has synced its cells), so
    // a bare read can observe the initial single empty cell before sync.
    await expect
      .poll(() => notebookCells(page, CLIENT1.notebook), { timeout: TIMEOUT })
      .toEqual(CLIENT1.cells);
    await expect
      .poll(() => notebookCells(page2, CLIENT2.notebook), { timeout: TIMEOUT })
      .toEqual(CLIENT2.cells);

    await page2.context().close();
  });
});
