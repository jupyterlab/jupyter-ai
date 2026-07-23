# Jupyter AI v3.2.0

:::{note}
Please join the discussion at [this GitHub issue](https://github.com/jupyterlab/jupyter-ai/issues/1571)!
:::

:::{note}
The exact interface proposed here is still being ironed out and is subject to
change.
:::

## Context

The existing `jupyter_ai_persona_manager` 3.0 API fulfills the original vision
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
developers identified three key gaps in the current 3.0 API:

1. **Creating new personas requires writing Python code.**
Defining a custom persona requires writing a Python file with a class that
subclasses `BasePersona`. Even though we offer a way to [do this
locally](https://github.com/jupyter-ai-contrib/jupyter-ai-persona-manager/pull/1),
the barrier remains too high for most users. Users want to be able to just say
"re-use the Claude engine, but call this persona 'Researcher', and give it
these tools" in some kind of no-code format (`.yaml`, `.md`, etc.).

2. **An AI persona's identity, model, or context cannot be configured at
   runtime.** `BasePersona` provides no API for this. Users can set an AI
persona's model and MCP servers by editing agent-specific configuration files
and `.jupyter/mcp_settings.json`, but this only works for ACP agents, and
changes only take effect after restarting the server.

3. **AI personas rely on shared paths for skills and MCP servers.**
The lack of context isolation between AI personas powered by the same agent
engine makes it challenging to define AI personas with unique capabilities for
specific use-cases. For example, users may want to define an MCP tools working with
sensitive data, which should only be available to an AI persona powered by a
local on-prem model with instructions to sanitize outputs.

During the discussion on [jupyter-ai#1571](https://github.com/jupyterlab/jupyter-ai/issues/1571),
the community surfaced a fourth gap that this revision addresses:

4. **The agent engine cannot be swapped like the other building blocks.** In
   the 3.0 design, the agent engine is baked into the persona *class*: an AI
persona built on OpenCode is an instance of `OpenCodeAcpPersona`. As Matt
Fisher argued, this special-cases the engine: it is the one building block of a
persona that you cannot swap at runtime the way you can swap a model or a
context. There is no `update_engine` to mirror `update_model`. A user who wants
to try the same persona on a different engine would have to tear it down and
build a new instance of a different class.

## Proposal Summary

In 3.2, we will deconstruct the persona into separate, well-defined building
blocks, and lift **everything**, including the agent engine, out of the class
definition. An AI persona is composed of five swappable parts:

- **Identity** (instance-level) — specifies the name and avatar shown in the chat.
- **Model** (instance-level) — specifies the model provider, model ID, and model URL.
- **Context** (instance-level) — specifies skills paths, MCP servers, and system prompt for the agent.
- **Engine** (instance-level) — the **agent engine** that processes messages (e.g. Claude, Codex, OpenCode). The engine is identified by an ID and namespaces all engine-specific behavior.
- **Options** (instance-level) — specifies additional per-engine settings, e.g. planning/agent mode, effort, hyperparameters. This will be left deliberately unstructured as it will be used as a way to pass per-instance settings that may be specific to an AI persona engine.

The key change from the previous revision of this proposal is that the **agent
engine is now a building block, not the persona class**. Previously,
`BasePersona` subclasses defined the engine (`persona_class` ⇒ engine). Now,
the implementation layer is shifted into a dedicated **persona engine**: a
persona's model, context, identity, options, *and engine* are all
instance-level attributes defined by dedicated Pydantic models or referenced by
ID, accepted in the constructor.

`BasePersona` becomes a standardized container that holds these building blocks
and delegates message handling to its engine via `self.engine`. To enable
future work on making model selection and persona configuration more intuitive,
the new `BasePersona` interface in 3.2 will provide a complete API for updating
every one of these instance-level attributes at runtime, including a new
`update_engine` method. Here is the new `BasePersona` interface being proposed
for 3.2 compared to 3.0, with the less important methods hidden:

`````{tabs}
````{tab} 3.2
```
class BasePersona(LoggingConfigurable):
    # ─── Lifecycle methods ────────────────────────────────
    def __init__(
        self,
        *args,
        ychat: "YChat",
        engine: PersonaEngine,
        model: PersonaModel | None = None,
        context: PersonaContext | None = None,
        identity: PersonaIdentity | None = None,
        options: dict | None = None,
        **kwargs,
    ): ...
    async def shutdown(self): ...

    # ─── Process message (delegates to self.engine) ───────
    async def process_message(self, message: Message) -> None: ...

    # ─── Runtime update APIs ────────────────────────────────
    def update_engine(self, engine: PersonaEngine) -> None: ...
    def update_model(self, model: PersonaModel) -> None: ...
    def update_context(self, context: PersonaContext) -> None: ...
    def update_identity(self, identity: PersonaIdentity) -> None: ...
    def update_options(self, options: dict) -> None: ...
```
````

````{tab} 3.0
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
engines are free to ignore any or all of these instance-level attributes and
leave their corresponding methods unimplemented. For non-agents, the engine may
define an "LLM runtime" or "AI workflow template" instead of an agent harness.
We deliberately use the term **engine** rather than **harness** precisely
because an engine need not wrap an agent harness at all: an educator may want a
chat-only engine with no tool access. This proposal preserves the generality of
the AI persona as a concept.
:::

(persona-engines)=
## Persona engines

A **persona engine** is the swappable implementation layer behind a persona. It
is what `process_message` delegates to, and it owns all engine-specific
behavior, e.g. how an ACP agent subprocess is orchestrated, or how a particular
harness loads skills and applies a model selection. By lifting this out of the
persona class and into a building block, we gain several things:

1. **Users can swap AI engines on a persona just like any other building
   block.** A user can try building their AI persona as LLM-only, on top of the
LiteLLM + LangChain runtime in `jupyter-ai-jupyternaut`, or on top of an ACP
engine in `jupyter-ai-acp-client`, to see what works best, without recreating
the persona.

2. **It unifies the developer API.** Everything is swappable at runtime through
   the `BasePersona` API. Developers no longer need to learn that swapping an
engine, unlike swapping a model, requires removing the instance and creating a
new one of a different class.

3. **It simplifies the conceptual model of a persona.** An AI persona is an
   artificial, human-like entity you can design from the ground up. The
application should be able to swap out the "brain" of a persona without tearing
it down and recreating it. The brain is a component of a persona, not its
definition.

4. **It namespaces engine-specific methods.** Engine-specific methods now live
   on `persona.engine`, while the `BasePersona` API stays completely
standardized.

5. **It leads toward merging JupyterLite AI with Jupyter AI.** An engine can
   declare an `engine.type` of `'server'` or `'lab'`, which defines whether the
engine runs on the backend or in the frontend. Migrating an AI persona to also
work on JupyterLite then just means picking an engine with `engine.type ==
'lab'`, something the persona manager could eventually do automatically.

### Engines are identified by ID

Because engines are now instance-level building blocks, they need a stable
identifier so a persona definition can reference one without importing a Python
class. Each engine is registered under an **engine ID** (e.g. `claude-acp`,
`opencode-acp`, `jupyternaut`). This is what makes the no-code path below
possible: a persona definition simply names the engine it wants.

```python
from pydantic import BaseModel

class PersonaEngine(ABC, LoggingConfigurable):
    """The swappable implementation layer behind a persona."""

    # Stable identifier used to reference this engine from a persona
    # definition, e.g. "claude-acp".
    id: ClassVar[str]

    # Whether this engine runs on the server or in the lab (frontend).
    type: ClassVar[Literal["server", "lab"]] = "server"

    async def process_message(self, message: Message) -> None: ...
    async def shutdown(self): ...

    # Engine-specific configuration hooks invoked by the BasePersona
    # update_* methods. An engine that ignores a building block may leave
    # the corresponding hook unimplemented.
    def apply_model(self, model: PersonaModel) -> None: ...
    def apply_context(self, context: PersonaContext) -> None: ...
    def apply_options(self, options: dict) -> None: ...
```

In the next section, we will show examples that better convey why the new APIs
proposed here close the gaps identified in 3.0 from a developer and user
perspective.

## Examples

### Example 1: Defining agentic AI personas powered by local models

In 3.0, to define an AI persona that uses local models, you need to use an
open-source agent engine (only OpenCode or Goose currently), then set the
model ID and skills at some agent-specific settings path. Once you do all of
that, Jupyter AI initializes your persona like this (shortened for brevity):


```py
# initializes '@OpenCode' that just reads from your local OpenCode config
OpenCodeAcpPersona(ychat=ychat)
# cannot add another instance of `OpenCodeAcpPersona`
```

In 3.0, you can only invoke this persona as `@OpenCode` since the persona's
identity is defined by the class. Since each persona class maps to exactly one
persona instance per chat, there's no way to create another AI persona built on
OpenCode that uses a different model and skillset.

The 3.2 API will allow developers to *reuse*
an existing engine to create a new AI persona, with
a different model, context, identity, and options. In 3.2, personas can be
initialized like this:

```py
# initializes '@MyAgent', your custom general-purpose agent
BasePersona(
    ychat=ychat,
    engine=PersonaEngine.from_id("opencode-acp"),
    model=PersonaModel(model_id="anthropic/claude-opus-4-8"),
    identity=PersonaIdentity(name="Researcher", avatar="<some-url-or-b64-img>"),
    context=PersonaContext(
        skills=".jupyter/skills/*",
        mcp_servers=[...]
    ),
    options={"temperature": 0.8},
)

# initializes '@SensitiveDataAnalyst', a self-hosted agent for sensitive data
BasePersona(
    ychat=ychat,
    engine=PersonaEngine.from_id("opencode-acp"),
    model=PersonaModel(model_id="ollama/llama-3.1", model_url="http://localhost:11434"),
    identity=PersonaIdentity(name="SensitiveDataAnalyst", avatar="<some-url-or-b64-img>"),
    context=PersonaContext(
        skills=".jupyter/sensitive-data-skills/*",
        mcp_servers=[McpServer(name="Sensitive data tools", ...)]
    ),
    options={"temperature": 0.2},
)
```

This would create 2 AI personas in your chat: `@MyAgent` and
`@SensitiveDataAnalyst`. These AI personas are built on the same agent engine
(`opencode-acp`), but have separate identities,
models, contexts, and options. Either persona could later be moved to a
different engine at runtime with `persona.update_engine(...)`, without being
recreated.

### Example 2: No-code path to defining a custom persona

It is clear from the above example that if we are just re-using an engine,
there is no need to create a Python module to define an AI persona. Since all of the
arguments are serializable, and the engine is referenced by ID, they can be
represented in any no-code format that
can express dictionaries / key-value pairs. Markdown files with YAML
frontmatter are well-suited for this while being easily readable. The 3.2
architecture enables a future where `.persona.md` files can be used to define
AI personas by naming an existing engine.

The use-case described above in Example 1 can then be created simply by
creating two new Markdown files under `.jupyter/personas`, with no code changes
required.

```{code-block} markdown
:caption: .jupyter/personas/researcher.persona.md

---
engine: opencode-acp
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
engine: opencode-acp
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

### Example 3: Swapping a persona's engine at runtime

Because the engine is just another building block, swapping it looks like
swapping any other component. A user can edit the `engine` field in
`.jupyter/personas/researcher.persona.md`:

```diff
---
- engine: opencode-acp
+ engine: claude-acp
model:
  model_id: anthropic/claude-opus-4-8
...
```

After the user runs `/refresh-personas`, the `PersonaManager` reloads the
definition and re-binds the persona to the `claude-acp` engine, preserving its
identity, model, context, and chat history. Because `update_engine` lives on the
standardized `BasePersona` interface, a future UI could offer this as a simple
engine dropdown, exactly like the model selector.

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

The engine is referenced by ID in persona definitions (`engine: claude-acp`)
and resolved to a registered `PersonaEngine` subclass at load time. See the
[Persona engines](persona-engines) section above for the engine interface.

### Other required updates

Out of brevity, the proposal summary did not exhaustively list all of the
technical changes needed to make this feature work. Here is a rough sketch of
the other requirements not yet described:

- We need an **engine registry** so engines can be discovered and resolved by
  ID. Engine packages (e.g. `jupyter-ai-acp-client`) will register their engines
under stable IDs (`claude-acp`, `opencode-acp`, …) via entry points.

- `PersonaManager` will need new methods to support loading Markdown files as
personas, and call these automatically on `__init__()` or when
`/refresh-personas` is called.

- Currently, `persona.id` just uses the module path and the class name to
  create the ID. This is not unique if we allow multiple personas using the
same engine to co-exist in the same chat, so we need to make a breaking
change in how persona IDs are generated automatically.

- We need to come up with some way to allow users to disable the "default
  persona instance". Support use cases where a user builds personas on top of
the `opencode-acp` engine, but does not want `@OpenCode` as a persona.

- To take advantage of the new APIs introduced in `BasePersona`, we need to
  provide some way in the UI to update the engine, model, context, identity, and
options. [Jupyter AI 3.1](completed/jupyter-ai-3.1) delivers the first cut of that UI on
top of ACP directly; this proposal focuses on making the right API so that UI
can eventually be backed by the unified persona API.

- We need to make chats portable. Right now each persona avatar is served from
  the server on a special API route, so these avatars get lost if the chat is
shared to another user without that persona installed. Both persona and user
identities should be encoded and saved into a chat directly so AI chats are
portable and shareable.

## Related efforts

- [Jupyter AI 3.1](completed/jupyter-ai-3.1), the in-chat UI that ships first and that
this API cleanup later backs.

- [jupyter-ai-persona-manager#32](https://github.com/jupyter-ai-contrib/jupyter-ai-persona-manager/pull/32) by Jordi Adoumie (Bloomberg) at the 2026 Q1 Jupyter AI Workshop in Seattle, a key contribution and reference point that inspired us to think about zero-code ways of defining AI personas.

- [Jupyter AI Quickagents](https://github.com/srdas/jupyter-ai-quickagent) by Sanjiv Das (SCU), a project that helped establish and refine our vision of creating AI personas with AI personas.

- [jupyter-ai#1558](https://github.com/jupyterlab/jupyter-ai/issues/1558) by Carl Boettiger (UC Berkeley), Matt Fisher, and others, which helped identify the gaps in the 3.0 design that were confusing users and developers.

## Acknowledgements

Thank you to everyone who attended the Jupyter AI community calls and events to
drive deep discussion and collaboration on this topic, especially Matt, Carl,
Sanjiv, Jordi, and Fernando! The persona engine concept in particular grew out
of Matt Fisher's argument that the agent harness should be a swappable building
block rather than a special-cased persona class.

:::{note}
Join the discussion on [this GitHub issue](https://github.com/jupyterlab/jupyter-ai/issues/1571)!
:::
