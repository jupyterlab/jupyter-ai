from jupyterlab_chat.models import Message

from .base import BaseChatHandler, SlashCommandRoutingType

MESSAGE_TO_ASK_SIGNIN = """
<div>Your Device Code is <b><code>{userCode}</code></b></div>
<div>Please go to <a href="{verificationUri}">{verificationUri}</a> and authorize using the above code.</div>
"""

MESSAGE_ALREADY_SIGNIN = """<div>You've already signed in as <b>{user}</b></div>"""


class GitHubCopilotChatHandler(BaseChatHandler):

    id = "github"
    name = "GitHub"
    help = "GitHub"
    routing_type = SlashCommandRoutingType(slash_id="github")

    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, message: Message):
        splitted_message = message.body.split(" ")
        if len(splitted_message) > 1:
            sub_command = splitted_message[1]

        lm_provider_class = self.config_manager.lm_provider
        lm_provider_params = self.config_manager.lm_provider_params
        lm_provider = lm_provider_class(**lm_provider_params)
        copilot_llm = lm_provider._llm
        copilot_llm.ensure_lsp_server_initialized()
        SUBCOMMANDS = ["signin", "signout"]

        if sub_command not in SUBCOMMANDS:
            self.reply(
                f"""
<div>Unknown subcommand. Available subcommands: {SUBCOMMANDS}</div>
"""
            )
        else:
            if sub_command == "signin":
                res = copilot_llm._signin()
                if res.get("status") == "AlreadySignedIn":
                    self.reply(MESSAGE_ALREADY_SIGNIN.format(**res))
                else:
                    self.reply(MESSAGE_TO_ASK_SIGNIN.format(**res))
            elif sub_command == "signout":
                res = copilot_llm._signout()
                if res.get("status") == "NotSignedIn":
                    self.reply(f"You have signed out.")
