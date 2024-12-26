import { test } from '@jupyterlab/galata';

enum FILENAMES {
  SIDEBAR = 'sidebar.png',
  CHAT_WELCOME_MESSAGE = 'chat-welcome-message.png'
}

/**
 * Don't load JupyterLab webpage before running the tests.
 * This is required to ensure we capture all log messages.
 */
test.use({ autoGoto: false });

test.describe('Jupyter AI', () => {
  test('Should be tested', () => {
    // no-op
  });
});
