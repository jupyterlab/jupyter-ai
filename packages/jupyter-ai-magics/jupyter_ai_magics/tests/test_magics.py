from IPython import InteractiveShell
from traitlets.config.loader import Config


def test_aliases_config():
    ip = InteractiveShell()
    ip.config = Config()
    ip.config.AiMagics.aliases = {"my_custom_alias": "my_provider:my_model"}
    ip.extension_manager.load_extension("jupyter_ai_magics")
    providers_list = ip.run_line_magic("ai", "list").text
    assert "my_custom_alias" in providers_list
