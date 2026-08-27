/**
 * Playwright configuration for the jupyter-ai MCP web-client-routing E2E suite,
 * based on the default from @jupyterlab/galata.
 *
 * A single test server serves the suite. The built-in Jupyter MCP server
 * (jupyter-server-mcp) runs on `MCPExtensionApp.mcp_port`; persona-manager
 * auto-points its built-in MCP server entry at that port, so the fixture
 * persona reaches the real jupyter-server-mcp.
 */
const baseConfig = require('@jupyterlab/galata/lib/playwright-config');

// Random HTTP port so a run doesn't collide with a dev server. Playwright
// re-`require`s this config in each worker, so pin it once into the env.
if (!process.env.JAI_TEST_PORT) {
  process.env.JAI_TEST_PORT = String(8989 + Math.floor(Math.random() * 900));
}
const PORT = Number(process.env.JAI_TEST_PORT);

module.exports = {
  ...baseConfig,
  testDir: 'mcp',
  // Retry to capture a trace of any transient failure, but still fail the run
  // if a test only passes on retry: flakiness must surface as a red build, not
  // be masked by the retry. A genuinely-broken test fails all attempts either
  // way. All three matrix legs are required (fail-fast: false), so no leg can
  // silently pass.
  retries: 2,
  failOnFlakyTests: true,
  use: { ...(baseConfig.use || {}), baseURL: `http://localhost:${PORT}` },
  webServer: {
    // The MCP port is offset from the HTTP port so it doesn't collide with the
    // jupyter-server-mcp default (3001) or a dev server. persona-manager reads
    // MCPExtensionApp.mcp_port to build its built-in MCP server URL.
    command: `jlpm start --ServerApp.port=${PORT} --MCPExtensionApp.mcp_port=${PORT + 100}`,
    url: `http://localhost:${PORT}/lab`,
    timeout: 120 * 1000,
    reuseExistingServer: false
  }
};
