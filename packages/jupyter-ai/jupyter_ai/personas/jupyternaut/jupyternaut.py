from typing import Any, Optional
import time
import json

from jupyterlab_chat.models import Message
from litellm import acompletion

from ...litellm_utils import StreamResult, ToolCallOutput
from ..base_persona import BasePersona, PersonaDefaults
from ..persona_manager import SYSTEM_USERNAME
from .prompt_template import (
    JUPYTERNAUT_SYSTEM_PROMPT_TEMPLATE,
    JupyternautSystemPromptArgs,
)


class JupyternautPersona(BasePersona):
    """
    The Jupyternaut persona, the main persona provided by Jupyter AI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def defaults(self):
        return PersonaDefaults(
            name="Jupyternaut",
            avatar_path="/api/ai/static/jupyternaut.svg",
            description="The standard agent provided by JupyterLab. Currently has no tools.",
            system_prompt="...",
        )

    async def process_message(self, message: Message) -> None:
        if not self.config_manager.chat_model:
            self.send_message(
                "No chat model is configured.\n\n"
                "You must set one first in the Jupyter AI settings, found in 'Settings > AI Settings' from the menu bar."
            )
            return

        model_id = self.config_manager.chat_model

        # `True` before the first LLM response is sent, `False` afterwards.
        initial_response = True
        # List of tool call outputs computed in the previous invocation.
        tool_call_outputs: list[dict] = []

        # Initialize list of messages, including history and context
        messages: list[dict] = self.get_context_as_messages(model_id, message)

        # Loop until the AI is complete running all its tools.
        while initial_response or len(tool_call_outputs):
            # Stream message to the chat
            response_aiter = await acompletion(
                model=model_id,
                messages=messages,
                tools=self.get_tools(model_id),
                stream=True,
            )
            result = await self.stream_message(response_aiter)
            initial_response = False

            # Append new reply to `messages`
            reply = self.ychat.get_message(result.id)
            tool_calls_json = result.tool_call_list.to_json()
            messages.append({
                "role": "assistant",
                "content": reply.body,
                "tool_calls": tool_calls_json
            })
            
            # Render tool calls in new message
            if len(result.tool_call_list):
                self.render_tool_calls(result)

            # Run tools and append outputs to `messages`
            tool_call_outputs = await self.run_tools(result.tool_call_list)
            messages.extend(tool_call_outputs)

            # Render tool call outputs in new message
            if tool_call_outputs:
                self.render_tool_call_outputs(
                    message_id=result.id,
                    tool_call_outputs=tool_call_outputs
                )
    
    def render_tool_calls(self, stream_result: StreamResult):
        """
        Renders tool calls by appending the tool calls to a message.
        """
        message_id = stream_result.id
        tool_call_list = stream_result.tool_call_list

        for tool_call in tool_call_list.resolve():
            id = tool_call.id
            index = tool_call.index
            type_val = tool_call.type
            function = tool_call.function.model_dump_json()
            # We have to HTML-escape double quotes in the JSON string.
            function = function.replace('"', "&quot;")

            self.ychat.update_message(Message(
                id=message_id,
                body=f'\n\n<jai-tool-call id="{id}" type="{type_val}" index={index} function="{function}"></jai-tool-call>\n',
                sender=self.id,
                time=time.time(),
                raw_time=False
            ), append=True)


    def render_tool_call_outputs(self, message_id: str, tool_call_outputs: list[dict]):
        # TODO
        # self.ychat.update_message(Message(
        #     id=message_id,
        #     body=f"\n\n```\n{json.dumps(tool_call_outputs, indent=2)}\n```\n",
        #     sender=self.id,
        #     time=time.time(),
        #     raw_time=False
        # ), append=True)

        # Updates the content of the last message directly
        message = self.ychat.get_message(message_id)
        body = message.body
        for output in tool_call_outputs:
            if not output['content']:
                output['content'] = ""
            output = ToolCallOutput(**output)
            tool_id = output.tool_call_id
            tool_output = output.model_dump_json()
            tool_output = tool_output.replace('"', '&quot;')
            body = body.replace(
                f'<jai-tool-call id="{tool_id}"',
                f'<jai-tool-call id="{tool_id}" output="{tool_output}"',
            )

        self.log.error(body)
        self.ychat.update_message(Message(
            id=message.id,
            time=time.time(),
            body=body,
            sender=self.id,
            raw_time=False
        ))


    def get_context_as_messages(
        self, model_id: str, message: Message
    ) -> list[dict[str, Any]]:
        """
        Returns the current context, including attachments and recent messages,
        as a list of messages accepted by `litellm.acompletion()`.
        """
        system_msg_args = JupyternautSystemPromptArgs(
            model_id=model_id,
            persona_name=self.name,
            context=self.process_attachments(message),
        ).model_dump()

        system_msg = {
            "role": "system",
            "content": JUPYTERNAUT_SYSTEM_PROMPT_TEMPLATE.render(**system_msg_args),
        }

        context_as_messages = [system_msg, *self._get_history_as_messages()]
        return context_as_messages

    def _get_history_as_messages(self, k: Optional[int] = 2) -> list[dict[str, Any]]:
        """
        Returns the current history as a list of messages accepted by
        `litellm.acompletion()`.

        NOTE: You should usually call the public `get_context_as_messages()`
        method instead.
        """
        # TODO: consider bounding history based on message size (e.g. total
        # char/token count) instead of message count.
        all_messages = self.ychat.get_messages()

        # gather last k * 2 messages and return
        start_idx = 0 if k is None else -2 * k
        recent_messages: list[Message] = all_messages[start_idx:]

        history: list[dict[str, Any]] = []
        for msg in recent_messages:
            role = (
                "assistant"
                if msg.sender.startswith("jupyter-ai-personas::")
                else "system" if msg.sender == SYSTEM_USERNAME else "user"
            )
            history.append({"role": role, "content": msg.body})

        return history
