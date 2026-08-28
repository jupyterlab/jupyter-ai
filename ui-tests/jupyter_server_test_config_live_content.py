"""Server configuration for the jupyter-ai live-content E2E suite.

!! Never use this configuration in production because it opens the server to the
world and provides access to JupyterLab JavaScript objects through the global
window variable.

The suite only needs a stock galata server. ``jupyter_live_content`` auto-enables
itself as a server extension (via its shipped ``jupyter_server_config.d`` entry),
and the transport packages (``jupyter_collaboration`` / ``jupyter_server_documents``)
installed by the ``e2e_live_content`` nox session likewise auto-enable, so nothing
transport-specific needs to be configured here.
"""

from jupyterlab.galata import configure_jupyter_server

configure_jupyter_server(c)  # noqa: F821
