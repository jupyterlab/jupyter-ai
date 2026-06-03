# Persona API v0.1

:::{note}
Join the discussion on [this GitHub issue](https://github.com/jupyterlab/jupyter-ai/issues/1571)!
:::

## Context

The existing `jupyter_ai_persona_manager` v0.0 API fulfills the original vision
of **AI personas** in Jupyter AI as generic, named entities available in each
chat that process messages that `@`-mention them. AI personas are implemented
via the `BasePersona` class, which is initialized once per chat, per persona.
Its main API is simply a `process_message(self, message: Message)` method that
defines how the agent handles a message that `@`-mentions it. The chat API is
accessed from the `self.ychat` attribute. This remarkably minimal definition
provides developers with extreme flexibility in what a persona can be: a
persona can be a tutor that responds with guided explanations and no tool
access, or a structured AI workflow, or a full agentic assistant with tool
calling and MCP server integration.

Our most mature and feature-rich implementations of AI personas live in the
`jupyter_ai_acp_client` package, which provides `BaseAcpPersona` as a general
template for defining Agent Client Protocol (ACP) agents as AI personas.
`BaseAcpPersona` inherits from `BasePersona`, orchestrates the ACP agent
subprocess in `__init__()`, and overrides the `process_message()` to delegate
message handling to a unified ACP client that speaks to agents and writes back
to the chat.  AI personas built on ACP (e.g. `CodexAcpPersona`) then derive
from `BaseAcpPersona` while specifying an agent executable, persona name +
avatar, and optional auth logic.  We have used the personas abstraction to
great success here, integrating 8 frontier agents (Claude, Kiro, Copilot,
Gemini, Goose, Codex, OpenCode, Mistral Vibe) in less than 2 months.

## Motivation

In recent community calls and at the Q2 2026 Developer Summit, users and
developers identified three key gaps in the current v0.0 API:

1. **Creating new personas requires writing Python code.**
Defining a custom persona requires writing a Python file with a class that
subclasses `BasePersona`. Even though we offer a way to [do this
locally](https://github.com/jupyter-ai-contrib/jupyter-ai-persona-manager/pull/1),
the barrier remains too high for most users. Users want to be able to just say
"re-use the Claude harness, but call this persona 'Researcher', and give it
these tools" in some kind of no-code format (`.yaml`, `.md`, etc.).

2. **An AI persona's identity, model, or context cannot be configured at
   runtime.** `BasePersona` provides no API for this. Users can set an AI
persona's model and MCP servers by editing agent-specific configuration files
and `.jupyter/mcp_settings.json`, but this only works for ACP agents, and
changes only take effect after restarting the server.

3. **AI personas rely on shared paths for skills and MCP servers.**
The lack of context isolation between AI personas powered by the same agent
harness makes it challenging to define AI personas with unique capabilities for
specific use-cases. For example, users may want to define an MCP tools working with
sensitive data, which should only be available to an AI persona powered by a
local on-prem model with instructions to sanitize outputs.

## Proposal Summary

In v0.1, we will deconstruct the persona into separate, well-defined concepts,
and lift everything except the agent harness out of the class definition:

- **Persona class** — defines the **agent harness** (e.g. Claude, Codex, OpenCode). The class may also define what defaults apply when no configuration is provided.
- **Model** (instance-level) — specifies the model provider, model ID, and model URL.
- **Context** (instance-level) — specifies skills paths, MCP servers, and system prompt for the agent.
- **Identity** (instance-level) — specifies the name and avatar shown in the chat.
- **Options** (instance-level) — specifies additional per-agent settings, e.g. planning/agent mode, effort, hyperparameters. This will be left deliberately unstructured as it will be used as a way to pass per-instance settings that may be specific to an AI persona class.

`BasePersona` will continue to define the agent harness in its class
definition. However, a persona's model, context, identity, and options will
all become instance-level attributes defined by dedicated Pydantic models
accepted in the constructor. 

To enable future work on making model selection and persona configuration more
intuitive, the new `BasePersona` interface in v0.1 will also provide a complete
API for updating these instance-level attributes at runtime. Here is the new
`BasePersona` interface being proposed for v0.1 compared to v0.0, with the less
important methods hidden:

`````{tabs}
````{tab} v0.1
```
class BasePersona(ABC, LoggingConfigurable):
    # ─── Lifecycle methods ────────────────────────────────
    def __init__(
        self,
        *args,
        ychat: "YChat",
        model: PersonaModel | None = None,
        context: PersonaContext | None = None,
        identity: PersonaIdentity | None = None,
        options: dict | None = None,
        **kwargs,
    ): ...
    async def shutdown(self): ...

    # ─── Process message ────────────────────────────────
    async def process_message(self, message: Message) -> None: ...

    # ─── Runtime update APIs ────────────────────────────────
    def update_model(self, model: PersonaModel) -> None: ...
    def update_context(self, context: PersonaContext) -> None: ...
    def update_identity(self, identity: PersonaIdentity) -> None: ...
    def update_options(self, options: dict) -> None: ...
```
````

````{tab} v0.0
```python
class BasePersona(ABC, LoggingConfigurable):
    # ─── Lifecycle methods ────────────────────────────────
    def __init__(
        self,
        *args,
        ychat: "YChat",
        **kwargs,
    ): ...
    async def shutdown(self): ...

    # ─── Process message ────────────────────────────────
    async def process_message(self, message: Message) -> None: ...
```
````
`````

:::{note}
In this proposal, we are not re-defining personas to only be agents. Persona
classes are free to ignore any or all of these instance-level attributes and
leave their corresponding methods unimplemented.  For non-agents, the persona
class may define an "LLM runtime" or "AI workflow template" instead of an
agent harness. This proposal preserves the generality of the AI persona as a
concept.
:::


In the next section, we will show examples that better convey why the new APIs
proposed here close the gaps identified in v0.0 from a developer and user
perspective.

## Examples

### Example 1: Defining agentic AI personas powered by local models

In v0.0, to define an AI persona that uses local models, you need to use an
open-source agent harness (only OpenCode or Goose currently), then set the
model ID and skills at some agent-specific settings path. Once you do all of
that, Jupyter AI initializes your persona like this (shortened for brevity):


```py
# initializes '@OpenCode' that just reads from your local OpenCode config
OpenCodeAcpPersona(ychat=ychat)
# cannot add another instance of `OpenCodeAcpPersona`
```

In v0.0, you can only invoke this persona as `@OpenCode` since the persona's
identity is defined by the class. Since each persona class maps to exactly one
persona instance per chat, there's no way to create another AI persona built on
OpenCode that uses a different model and skillset.

The v0.1 API will allow developers to *reuse*
the harness defined in an existing class to create a new AI persona, with
a different model, context, identity, and options. In v0.1, personas can be
initialized like this:

```py
# initializes '@MyAgent', your custom general-purpose agent
OpenCodeAcpPersona(
    ychat=ychat,
    model=PersonaModelSpec(model_id="anthropic/claude-opus-4-8"),
    identity=PersonaIdentity(name="Researcher", avatar="<some-url-or-b64-img>"),
    context=PersonaContext(
        skills=".jupyter/skills/*",
        mcp_servers=[...]
    ),
    options={"temperature": 0.8},
)

# initializes '@SensitiveDataAnalyst', a self-hosted agent for sensitive data
OpenCodeAcpPersona(
    ychat=ychat,
    model=PersonaModelSpec(model_id="ollama/llama-3.1", model_url="http://localhost:11434"),
    identity=PersonaIdentity(name="SensitiveDataAnalyst", avatar="<some-url-or-b64-img>"),
    context=PersonaContext(
        skills=".jupyter/sensitive-data-skills/*",
        mcp_servers=[McpServer(name="Sensitive data tools", ...)]
    ),
    options={"temperature": 0.2},
)
```

This would create 2 AI personas in your chat: `@MyAgent` and
`@SensitiveDataAnalyst`. These AI personas are built on the same agent harness
defined in the `OpenCodeAcpPersona` class, but have separate identities,
models, contexts, and options.

### Example 2: No-code path to defining a custom persona

It is clear from the above example that if we are just re-using a persona class,
there is no need to create a Python module to define an AI persona. Since all of the
arguments are serializable, they can be represented in any no-code format that
can express dictionaries / key-value pairs. Markdown files with YAML
frontmatter are well-suited for this while being easily readable. The v0.1
architecture enables a future where `.persona.md` files can be used to define
AI personas by reusing an existing AI persona class.

The use-case described above in Example 1 can then be created simply by
creating two new Markdown files under `.jupyter/personas`, with no code changes
required.

```{code-block} markdown
:caption: .jupyter/personas/researcher.persona.md

---
persona_class: OpenCodeAcpPersona
model:
  model_id: anthropic/claude-opus-4-8
identity:
  name: Researcher
  avatar: researcher.svg
context:
  skills:
    - .jupyter/skills/*
  mcp_servers:
    - name: Research tools
      type: http
      url: http://localhost:3001/mcp
options:
  temperature: 0.8
---

You are a research assistant specialized in scientific literature review.
Synthesize findings across papers, identify gaps, and suggest next steps.
Always cite your sources.
```

```{code-block} markdown
:caption: .jupyter/personas/sensitive-data-analyst.persona.md

---
persona_class: OpenCodeAcpPersona
model:
  model_id: ollama/llama-3.1
  model_url: http://localhost:11434
identity:
  name: SensitiveDataAnalyst
  avatar: sensitive-data.svg
context:
  skills:
    - .jupyter/sensitive-data-skills/*
  mcp_servers:
    - name: Sensitive data tools
      type: stdio
      command: python
      args: ["-m", "sensitive_data_mcp"]
options:
  temperature: 0.2
---

You are a data analyst working with sensitive datasets. Always sanitize
outputs before presenting them. Never include raw PII in your responses.
Prefer aggregations and anonymized summaries.
```

After these personas are defined and saved as files, they will appear
automatically in new chats. They will appear in existing chats after a user
runs `/refresh-personas`.

## Technical Details

### Pydantic Models

:::{note}
The structure of these models is subject to change in future versions; it is
likely that we will need to add or update fields to align with what makes sense
in practice.
:::

```python
from pydantic import BaseModel
from typing import Optional


class PersonaModel(BaseModel):
    """Defines which LLM a persona uses."""
    model_id: str
    model_url: Optional[str] = None


class PersonaContext(BaseModel):
    """Defines the context available to a persona."""
    system_prompt: str | None
    mcp_servers: list[McpServerStdio | McpServerHttp] = []
    skills_paths: list[str] = []


class PersonaIdentity(BaseModel):
    """Defines how a persona appears in the chat."""
    name: str
    avatar: str | None = None
    description: str | None = None
```

### Other required updates

Out of brevity, the proposal summary did not exhaustively list all of the
technical changes needed to make this feature work. Here is a rough sketch of
the other requirements not yet described:

- `PersonaManager` will need new methods to support loading Markdown files as
personas, and call these automatically on `__init__()` or when
`/refresh-personas` is called.

- Currently, `persona.id` just uses the module path and the class name to
  create the ID. This is not unique if we allow multiple personas deriving from
the same class to co-exist in the same chat, so we need to make a breaking
change in how persona IDs are generated automatically.

- We need to come up with some way to allow users to disable the "default
  persona instance". Support use cases where a user builds personas on top of
`OpenCodeAcpPersona`, but does not want `@OpenCode` as a persona.

- To take advantage of the new APIs introduced in `BasePersona`, we need to
  provide some way in the UI to update the model, context, identity, and
options. We will focus on making the right API first before diving into the UI
decisions.

- We need to make chats portable. Right now each persona avatar is served from
  the server on a special API route, so these avatars get lost if the chat is
shared to another user without that persona installed. Both persona and user
identities should be encoded and saved into a chat directly so AI chats are
portable and shareable.

## Related efforts

- [PR opened](https://github.com/srdas/jupyter-ai-quickagent) by Jordi Adoumie (Bloomberg) at the 2026 Q1 Jupyter AI Workshop in Seattle, a key contribution and reference point that inspired us to think about zero-code ways of defining AI personas.

- [Jupyter AI Quickagents](https://github.com/srdas/jupyter-ai-quickagent) by Sanjiv Das (SCU), a project that helped establish and refine our vision of creating AI personas with AI personas.

- [jupyter-ai#1558](https://github.com/jupyterlab/jupyter-ai/issues/1558) by Carl Boettiger (UC Berkeley), Matt Fisher, and others, which helped identify the gaps in the v0.0 design that were confusing users and developers.

## Acknowledgements

Thank you to everyone who attended the Jupyter AI community calls and events to
drive deep discussion and collaboration on this topic, especially Matt, Carl,
Sanjiv, Jordi, and Fernando!

:::{note}
Join the discussion on [this GitHub issue](https://github.com/jupyterlab/jupyter-ai/issues/1571)!
:::

