/*
 * Playwright configuration for the jupyter-ai live-content E2E suite, based on
 * the default from @jupyterlab/galata.
 *
 * A single stock galata server serves the suite (see
 * jupyter_server_test_config_live_content.py). jupyter-live-content and the
 * transport packages installed by the `e2e_live_content` nox session auto-enable
 * themselves, so no extra server flags are needed.
 */
const baseConfig = require('@jupyterlab/galata/lib/playwright-config');
const { resolveTestPort } = require('./resolve-test-port');

// Random HTTP port so a run doesn't collide with a dev server, skipping the
// ports Chromium refuses to navigate to (net::ERR_UNSAFE_PORT) -- notably
// 10080, which sits inside this suite's range. The resolver pins the choice
// into the env so every Playwright worker reuses it.
const PORT = resolveTestPort('JAI_LIVE_CONTENT_TEST_PORT', 9889, 900);

module.exports = {
  ...baseConfig,
  testDir: 'live-content',
  // Retry to capture a trace of any transient failure, but still fail the run
  // if a test only passes on retry: flakiness must surface as a red build, not
  // be masked by the retry.
  retries: 2,
  failOnFlakyTests: true,
  use: { ...(baseConfig.use || {}), baseURL: `http://localhost:${PORT}` },
  webServer: {
    command: `jlpm start:live-content --ServerApp.port=${PORT}`,
    url: `http://localhost:${PORT}/lab`,
    timeout: 120 * 1000,
    reuseExistingServer: false
  }
};
