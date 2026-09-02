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
const { resolveTestPort } = require('./resolve-test-port');

// Random HTTP port so a run doesn't collide with a dev server, skipping the
// ports Chromium refuses to navigate to (net::ERR_UNSAFE_PORT). The resolver
// pins the choice into the env so every Playwright worker reuses it.
const PORT = resolveTestPort('JAI_TEST_PORT', 8989, 900);

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
