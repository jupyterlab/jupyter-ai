import os
from typing import Any

from jupyterlab_chat.models import Message
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

from ...history import YChatHistory
from ..base_persona import BasePersona, PersonaDefaults
from .prompt_template import JUPYTERNAUT_PROMPT_TEMPLATE, JupyternautVariables


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
        if not self.config_manager.lm_provider:
            self.send_message(
                "No language model provider configured. Please set one in the Jupyter AI settings."
            )
            return

        provider_name = self.config_manager.lm_provider.name
        model_id = self.config_manager.lm_provider_params["model_id"]

        # Process file attachments and include their content in the context
        context = self._process_attachments(message)

        runnable = self.build_runnable()
        variables = JupyternautVariables(
            input=message.body,
            model_id=model_id,
            provider_name=provider_name,
            persona_name=self.name,
            context=context,
        )
        variables_dict = variables.model_dump()
        reply_stream = runnable.astream(variables_dict)
        await self.stream_message(reply_stream)

    def build_runnable(self) -> Any:
        # TODO: support model parameters. maybe we just add it to lm_provider_params in both 2.x and 3.x
        llm = self.config_manager.lm_provider(**self.config_manager.lm_provider_params)
        runnable = JUPYTERNAUT_PROMPT_TEMPLATE | llm | StrOutputParser()

        runnable = RunnableWithMessageHistory(
            runnable=runnable,  #  type:ignore[arg-type]
            get_session_history=lambda: YChatHistory(ychat=self.ychat, k=2),
            input_messages_key="input",
            history_messages_key="history",
        )

        return runnable

    def _process_attachments(self, message: Message) -> str:
        """
        Process file attachments in the message and return their content as a string.
        """
        self.log.info(f"DEBUG: _process_attachments called with message: {message}")
        self.log.info(f"DEBUG: Message has attachments: {hasattr(message, 'attachments')}")
        
        if not hasattr(message, 'attachments') or not message.attachments:
            self.log.info("DEBUG: No attachments found in the message.")
            return None

        context_parts = []

        for attachment_id in message.attachments:
            self.log.info(f"DEBUG: Processing attachment with ID: {attachment_id}")
            try:
                # Try to resolve attachment using multiple strategies
                file_path = self._resolve_attachment_to_path(attachment_id)
                
                if not file_path:
                    self.log.warning(f"Could not resolve attachment ID: {attachment_id}")
                    continue
                
                # Read the file content
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                # Get relative path for display
                rel_path = os.path.relpath(file_path, self.get_workspace_dir())
                
                # Add file content with header
                context_parts.append(
                    f"File: {rel_path}\n```\n{file_content}\n```"
                )

            except Exception as e:
                self.log.warning(f"Failed to read attachment {attachment_id}: {e}")
                context_parts.append(
                    f"Attachment: {attachment_id} (could not read file: {e})"
                )

        result = "\n\n".join(context_parts) if context_parts else None
        return result

    def _resolve_attachment_to_path(self, attachment_id: str) -> str | None:
        """
        Resolve an attachment ID to its file path using multiple strategies.
        """
        try:
            self.log.info(f"DEBUG: Resolving attachment ID: {attachment_id}")
            
            attachment_data = self._get_attachment_from_ychat(attachment_id)
            self.log.info(f"DEBUG: YChat attachment data: {attachment_data}")
            
            if attachment_data and isinstance(attachment_data, dict):
                # If attachment has a 'value' field with filename
                if 'value' in attachment_data:
                    filename = attachment_data['value']
                    
                    # Try relative to workspace directory
                    workspace_path = os.path.join(self.get_workspace_dir(), filename)
                    if os.path.exists(workspace_path):
                        self.log.info(f"DEBUG: Found file at workspace path: {workspace_path}")
                        return workspace_path
                    
                    # Try as absolute path
                    if os.path.exists(filename):
                        self.log.info(f"DEBUG: Found file at absolute path: {filename}")
                        return filename
                        
            return None
            
        except Exception as e:
            self.log.error(f"Failed to resolve attachment {attachment_id}: {e}")
            return None

    def _get_attachment_from_ychat(self, attachment_id: str) -> dict | None:
        """
        Get attachment data from the YChat document.
        """
        try:
            # Access the underlying YDoc document
            ydoc = self.ychat._ydoc
            self.log.info(f"DEBUG: YDoc type: {type(ydoc)}")
            
            # Try to access attachments from the document
            with ydoc.transaction():
                # Try getting attachments as a Map
                try:
                    import pycrdt
                    yattachments = ydoc.get("attachments", type=pycrdt.Map)
                    if yattachments and attachment_id in yattachments:
                        attachment_data = yattachments[attachment_id]
                        self.log.info(f"DEBUG: Found attachment in pycrdt Map: {attachment_data}")
                        return attachment_data

                except Exception as e:
                    self.log.info(f"DEBUG: pycrdt Map access failed: {e}")
                
                # Try getting attachments as dict
                try:
                    attachments_dict = ydoc.get("attachments", {})
                    if isinstance(attachments_dict, dict) and attachment_id in attachments_dict:
                        return attachments_dict[attachment_id]

                except Exception as e:
                    self.log.info(f"DEBUG: Dict access failed: {e}")
                    
            return None
            
        except Exception as e:
            self.log.error(f"Failed to get attachment from YChat: {e}")
            self.log.exception(f"DEBUG: Full exception during YChat access")
            return None
