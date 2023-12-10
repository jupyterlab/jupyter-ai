from typing import Dict, Type

from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)

from ..models import (
    InlineCompletionList,
    InlineCompletionReply,
    InlineCompletionRequest,
    ModelChangedNotification,
)
from .base import BaseInlineCompletionHandler

SYSTEM_PROMPT = """
You are an application built to provide helpful code completion suggestions.
You should only produce the code. Any comments should be kept to minimum
and use the programming language comment syntax.
The code is written in JupyterLab, a data analysis and code development
environment which can execute code extended with additional syntax for
interactive features, such as IPython magics.
""".strip()

DEFAULT_TEMPLATE = """
The document is called `{filename}` and written in {language}.
The code after the completion request is:

```
{suffix}
```

Complete the following code:

```
{prefix}"""


class DefaultInlineCompletionHandler(BaseInlineCompletionHandler):
    llm_chain: LLMChain

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        lm_provider = self.config_manager.lm_provider
        lm_provider_params = self.config_manager.lm_provider_params
        next_lm_id = (
            f'{lm_provider.id}:{lm_provider_params["model_id"]}'
            if lm_provider
            else None
        )
        self.broadcast(ModelChangedNotification(model=next_lm_id))

        model_parameters = self.get_model_parameters(provider, provider_params)
        llm = provider(**provider_params, **model_parameters)

        if llm.is_chat_provider:
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT).format(
                        provider_name=llm.name, local_model_id=llm.model_id
                    ),
                    HumanMessagePromptTemplate.from_template(DEFAULT_TEMPLATE),
                ]
            )
        else:
            prompt_template = PromptTemplate(
                input_variables=["prefix", "suffix", "language", "filename"],
                template=SYSTEM_PROMPT.format(
                    provider_name=llm.name, local_model_id=llm.model_id
                )
                + "\n\n"
                + DEFAULT_TEMPLATE,
            )

        self.llm = llm
        self.llm_chain = LLMChain(llm=llm, prompt=prompt_template, verbose=True)

    async def process_message(
        self, request: InlineCompletionRequest
    ) -> InlineCompletionReply:
        self.get_llm_chain()
        prediction = await self.llm_chain.apredict(
            prefix=request.prefix,
            suffix=request.suffix,
            language=request.language,
            filename=request.path.split("/")[-1] if request.path else "untitled",
            stop=["\n```"],
        )
        return InlineCompletionReply(
            list=InlineCompletionList(items=[{"insertText": prediction}]),
            reply_to=request.number,
        )
