# `'jupyter_ai.personas'`

```{contents} Contents
```

## Summary

This entry point group allows packages to add custom AI personas to the chat.
AI personas are analogous to "bots" in other chat applications. Every available
persona will be available in every chat by default. If a chat has any other
users besides the current user and a single AI persona, then AI personas will
only respond when `@`-mentioned. Jupyternaut provides a single AI persona by
default: `Jupyternaut`.

For example, if your Jupyter AI instance has `Jupyternaut` and `MyCustomPersona`
as 2 AI personas, then each persona will only respond when `@`-mentioned.

- To call `Jupyternaut`, your message must include `@Jupyternaut`.

- To call `MyCustomPersona`, your message must include `@MyCustomPersona`.

- Multiple personas may be mentioned in a single message. Each mentioned persona
  will reply to the new message, allowing you to compare performance across AI
  personas.

This group expects a **persona class**, a subclass of
`jupyter_ai.personas:BasePersona`. Instructions on defining one are given in the
next section.

## How-to: Define a custom AI persona

Defining a custom AI persona is simple. One needs to define a new class that
inherits from `BasePersona` and implements its two abstract methods.

The two abstract methods required are the `defaults` property and the
`process_message()` method.

- `defaults` defines the default settings of the persona. This is mainly used to
control the name and avatar shown in the Jupyter AI chat.

- `process_message()` defines how your persona responds to new messages.

We will dive into the `process_message()` method first, then discuss how to
define the `defaults` property.

### Defining how an AI persona processes messages

The `process_message()` method takes the signature:

```py
    @abstractmethod
    async def process_message(self, message: Message) -> None:
        """
        Processes a new message. This method exclusively defines how new
        messages are handled by a persona, and should be considered the "main
        entry point" to this persona. Reading chat history and streaming a reply
        can be done through method calls to `self.ychat`. See
        `JupyternautPersona` for a reference implementation on how to do so.

        This is an abstract method that must be implemented by subclasses.
        """
```

This method accepts a `Message` object that represents a new message from a
human user. There are many attributes on this object, but the main one is
`message.body`, which contains the content of the message as a string.
A full reference can be found in `jupyterlab_chat.models:Message`.

Subclasses may use the built-in methods on `BasePersona` to respond to the user.
The two main methods are:

- `send_message(body: str)`: Accepts a string and replies immediately.

- `stream_message(stream: AsyncIterator[str])`: Accepts an async interator that
yields string chunks, and streams the response to the chat. The output of the
`astream()` method on LangChain models can be passed to this method directly.

### Using Jupyternaut's configured chat model

The personas feature gives developers total freedom in how their persona
responds to new messages. Personas do not need to use the same chat model as
Jupyternaut, and can use any library of their choice, provided it is installed
in the same environment.

However, if your persona wants to use the same configured LangChain model used
by Jupyternaut, you can access that through the `self.config: ConfigManager`
attribute available to subclasses.

Add and call this method on a persona to access the LangChain runnable used by
Jupyternaut:

```py
def build_runnable(self) -> Any:
    llm = self.config.lm_provider(**self.config.lm_provider_params)
    runnable = JUPYTERNAUT_PROMPT_TEMPLATE | llm | StrOutputParser()

    runnable = RunnableWithMessageHistory(
        runnable=runnable,  #  type:ignore[arg-type]
        get_session_history=lambda: YChatHistory(ychat=self.ychat, k=2),
        input_messages_key="input",
        history_messages_key="history",
    )

    return runnable
```

See `jupyter_ai.personas.jupyternaut` for a complete reference.

### Defining AI persona defaults

The `defaults` property takes the signature:

```py
    @property
    @abstractmethod
    def defaults(self) -> PersonaDefaults:
        """
        Returns a `PersonaDefaults` data model that represents the default
        settings of this persona.

        This is an abstract method that must be implemented by subclasses.
        """
```

This property should return a `PersonaDefaults` instance:

```py
class PersonaDefaults(BaseModel):
    name: str  # e.g. "Jupyternaut"
    description: str  # e.g. "..."
    avatar_path: str  # e.g. /avatars/jupyternaut.svg
    system_prompt: str  # e.g. "You are a language model named..."
```

- The `name` field determines the name of the AI persona shown in chat.

- The `description` field is currently reserved but unused.

- The `avatar_path` field takes the URL path to an image served by the Jupyter
Server, relative to the server's domain. This can be used to show custom avatars
for your AI persona.

    - We may change this to pass base64-encoded images instead of URL paths in
    the future.

- The `system_prompt` field is currently reserved but unused.

## Reference implementation

This code defines a custom AI persona with the name `DebugPersona`, that always
replies with `'Hello!'`.

```py
class DebugPersona(BasePersona):
    """
    The Jupyternaut persona, the main persona provided by Jupyter AI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def defaults(self):
        return PersonaDefaults(
            name="DebugPersona",
            avatar_path="/api/ai/static/jupyternaut.svg",
            description="A mock persona used for debugging in local dev environments.",
            system_prompt="...",
        )

    async def process_message(self, message: Message):
        self.send_message(NewMessage(body="Hello!", sender=self.id))
        return
```

:::{note}
To make a custom AI persona available to Jupyter AI, you must provide it as an
entry point in your package. See the documentation on
<project:providing_entry_points.md> to learn more.
:::
