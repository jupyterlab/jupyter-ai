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

// Random HTTP port so a run doesn't collide with a dev server. Playwright
// re-`require`s this config in each worker, so pin it once into the env.
if (!process.env.JAI_LIVE_CONTENT_TEST_PORT) {
  process.env.JAI_LIVE_CONTENT_TEST_PORT = String(
    9889 + Math.floor(Math.random() * 900)
  );
}
const PORT = Number(process.env.JAI_LIVE_CONTENT_TEST_PORT);

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
