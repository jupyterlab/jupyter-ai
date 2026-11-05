__version__ = "3.2.0"


def _jupyter_server_extension_points():
    return [{"module": "jupyter_ai_core"}]


def _load_jupyter_server_extension(serverapp):
    """
    Show hidden files by default, so that agent files such as `.claude/` are visible.

    Jupyter Server reads `jupyter_server_config.d` only to enable extensions, so
    this default cannot ship as a config file. Explicit user config wins.
    """
    manager = serverapp.contents_manager
    configured = any(
        "allow_hidden" in serverapp.config.get(cls.__name__, {})
        for cls in type(manager).mro()
    )
    if not configured:
        manager.allow_hidden = True
        serverapp.log.info("jupyter_ai_core | ContentsManager.allow_hidden = True")
