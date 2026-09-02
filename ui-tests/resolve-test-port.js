/*
 * Resolve a random localhost port for a galata test server, skipping the ports
 * Chromium refuses to navigate to (net::ERR_UNSAFE_PORT).
 *
 * Playwright re-`require`s each config file in every worker process, so the
 * resolved port is pinned into `envVar` on the first call and reused verbatim
 * thereafter. That guarantees the web server and all workers agree on one port.
 */

// Ports Chromium blocks outright: navigating to one fails with
// net::ERR_UNSAFE_PORT. Mirrors the `kRestrictedPorts` table in Chromium's
// net/base/port_util.cc. A test server that binds one of these (e.g. 10080,
// which sits inside the live-content suite's random range) is reachable by
// curl but unreachable by the browser, so the whole suite fails.
const UNSAFE_PORTS = new Set([
  1, 7, 9, 11, 13, 15, 17, 19, 20, 21, 22, 23, 25, 37, 42, 43, 53, 69, 77, 79,
  87, 95, 101, 102, 103, 104, 109, 110, 111, 113, 115, 117, 119, 123, 135, 137,
  139, 143, 161, 179, 389, 427, 465, 512, 513, 514, 515, 526, 530, 531, 532,
  540, 548, 554, 556, 563, 587, 601, 636, 989, 990, 993, 995, 1719, 1720, 1723,
  2049, 3659, 4045, 5060, 5061, 6000, 6566, 6665, 6666, 6667, 6668, 6669, 6697,
  10080
]);

/**
 * Return the port for the test server, resolving and pinning it once.
 *
 * @param {string} envVar - env var the port is pinned into (shared across workers)
 * @param {number} base - lowest port the range may produce
 * @param {number} span - size of the range; ports are picked from [base, base+span)
 * @returns {number} a port in [base, base+span) that is not in UNSAFE_PORTS
 */
function resolveTestPort(envVar, base, span) {
  if (!process.env[envVar]) {
    let port;
    do {
      port = base + Math.floor(Math.random() * span);
    } while (UNSAFE_PORTS.has(port));
    process.env[envVar] = String(port);
  }
  return Number(process.env[envVar]);
}

module.exports = { resolveTestPort, UNSAFE_PORTS };
