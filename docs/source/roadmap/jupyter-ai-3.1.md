# Jupyter AI 3.1

:::{note}
Please join the discussion at [this GitHub issue](https://github.com/jupyterlab/jupyter-ai/issues/1584)!
:::

## Context

In Jupyter AI 3.0, instead of building our own agent, we wrap existing agent harnesses through the Agent Client Protocol (ACP) and present them as personas. This integrated eight frontier agents (Claude, Kiro, Copilot, Gemini, Goose, Codex, OpenCode, Mistral Vibe) in under two months, each available in any chat and invokable by `@`-mention.

The controls users expect from popular agentic editors, e.g. a model selector, an effort level, context usage, and per-message cost, are already exposed by the agents we wrap, over ACP. We do not need to wait for a new persona API to surface them: ACP's session-update events and RPCs carry this information today. Jupyter AI 3.1 brings these controls into the chat by consuming what ACP already provides.

[Jupyter AI 3.2](jupyter-ai-3.2), the persona API cleanup, comes afterward. It moves a persona's model, context, identity, engine, and options out of the class definition into instance attributes, and adds runtime update methods. That work takes longer and benefits only users authoring custom personas, so it does not block the UI improvements described here. Where 3.1 reads and writes persona configuration directly over ACP, 3.2 will later unify that behind a standardized persona API.

Jupyter AI 3.1 delivers the UI: in-chat controls for model, effort, and usage that bring Jupyter AI to parity with popular agentic editors, while keeping what sets it apart, the ability to work with several personas, and several people, in one chat. The result is one kind of chat, as polished as those tools, that works the same whether you are talking to one persona or several.

## Motivation

Users coming from other popular agentic editors and AI assistants expect a consistent set of controls quickly and conveniently available in the chat UI.

| Feature | Popular agentic editors | Jupyter AI |
|---|---|---|
| Model selector | Yes | No, only in a settings panel |
| Effort / reasoning level | Yes | No |
| Context usage | Yes | No |
| Session cost | Yes | No |
| Thinking display | Yes | No |
| Slash commands | Yes | Partial, no autocomplete polish |

The multi-persona chat paradigm Jupyter AI works in makes them non-trivial to add. In other tools, a single conversation is built around one assistant, and the controls assume it; the ones that run several agents at once give each its own separate pane or thread. Jupyter AI brings them together: several AI personas and several people collaborating in a single chat, where any message can address any persona. If a chat holds `@Claude` and `@Kiro`, which one's model selector belongs in the input box, which one's slash commands should autocomplete, and which one's context window does the indicator track?

This is the core problem 3.1 solves: how to show persona-specific data and options in a chat that can hold more than one persona, without splitting the product into two different kinds of chat.

Two related gaps compound it:

- All installed personas are initialized eagerly in every chat, and therefore all personas participate in every chat by default. There is no way to remove or add a persona.
- Persona configuration has no home in the chat. The settings exposed over ACP have nowhere to be changed from.

## Goals

3.1 gives Jupyter AI the state-of-the-art controls users expect from popular agentic editors, surfaced from what ACP exposes today and adapted to Jupyter AI's paradigm of several personas in one chat.

## User stories

- As a Jupyter user, I want to pick a persona's model and effort from the chat, so I can match the task without opening a settings panel.
- As a Jupyter user working with several personas, I want to see and switch which one I am addressing, so I am not retyping `@` on every message.
- As a Jupyter user, I want each reply to show its model and cost, so I can track what I am spending.
- As a Jupyter user, I want to add and remove personas in a chat, so it holds exactly the assistants I need.

## A single set of in-chat controls

The design resolves the ambiguity with a single active persona: in a chat that holds several, the active persona is the one the input is currently addressed to. The model, effort, and usage controls live in the chat input and show information about the active persona, so there is always exactly one persona's model selector to show, one set of slash commands to autocomplete, and one context window to track.

By default, the active persona is detected automatically:

- In a chat with one persona, it is always that persona.
- When you `@`-mention a persona, it becomes active and stays active for the messages that follow, so you do not retype the `@` every time. Carl Boettiger's feedback in #1558 notes that users repeatedly forget the `@`; because the active persona persists and is always shown, a forgotten `@` is visible rather than silent.

The user can also switch the active persona directly from the selector. The input area always shows it next to the controls, so the user knows who the next message will go to and whose settings they are seeing. It changes only when the user mentions a persona or picks one, never on its own. Changing the model or effort takes effect on the next message and is saved with the chat. Context usage is shown for the active persona, since each persona has its own model and its own context window, so a single window to track only makes sense for one persona at a time. Cost is reported both per message and as a running total for the whole chat, since cost is additive across personas and the chat total is what tells the user what a deliverable cost.

In a chat with one persona, the input area looks and behaves like a standard single-assistant tool. It is the same chat either way: every chat can hold more than one persona, and one with a single persona is just a chat that has one in it right now. Adding or removing personas changes who is in the room, not how the chat works.

Persona information appears in two places:

- In the input area, the controls for the active persona: the model and effort selectors and the context-usage indicator, alongside the chat's running cost total. This is the live state, what the next message will use.
- In a footer on each message: which model answered, the tokens it used, and the cost. This is the record of what already happened.

```text
+--------------------------------------------------------+
| Chat: cleanup.ipynb              [Claude] [Kiro]   (+) |
|                                                        |
|  Claude   Opus . 1,240 tokens . $0.03   <- msg footer  |
|  ...                                                   |
+--------------------------------------------------------+
| To: [Claude v] [Opus v] [high v]  ctx 64%  $0.41 total |
| Type a message...                           [stop] [^] |
+--------------------------------------------------------+
```

This is a rough sketch; polished mockups will come with the prototype.

We considered two alternatives. Showing this only per message gives no live controls, so the user could not change a model or effort before sending. A separate options panel splits configuration into a second surface, away from where the user types. The input area keeps the controls next to the message being written.

## Personas in a chat, and who responds

A chat's personas are the ones the user has added to it. The chat header shows them as a roster: avatars with an add control that lists installed personas and a remove control on each, like the member list in a group chat. A new chat starts empty; the user adds a persona by picking it from the roster or `@`-mentioning it.

Today, who will respond is not shown, which can catch users off guard. With one human in the chat, a message that mentions no one goes to the default persona; once a second human joins, personas stay silent unless mentioned, to avoid talking over a human conversation. Because nothing signals that change, the personas can appear to have gone quiet for no reason. The roster and the active-persona selector address this: the roster shows who can respond, the selector shows who the next message goes to, and the UI signals when routing becomes mention-only.

## Local and global configuration

Configuration is either local or global. A change the user makes in a chat, a persona's model or effort, is written back to the agent over ACP (`session/set_config_option`) and is saved with the chat, so it travels with that chat and touches no other. The global defaults, the default persona and model and the allowed-model list, live in the persona definitions and the settings panel, and define what new chats start from. The two never cross: editing a chat's persona does not change the user's defaults, and changing defaults does not rewrite existing chats.

Once [Jupyter AI 3.2](jupyter-ai-3.2) lands the persona API, these per-chat writes will be unified behind the standardized runtime update methods (`update_model`, `update_options`) rather than going to ACP directly, but the user-facing behavior described here stays the same.

## Plan

Phase one gives a single persona its in-chat controls: model, effort, context usage, thinking, and cost, brought into the chat input on top of the active persona, read from and written to ACP. This is the bulk of the value, with no dependency on the multi-persona work or on the 3.2 persona API. Phase two extends it to several personas in one chat: the roster, lazy initialization, routing clarity, and the local-and-global split.

The work splits into four mostly-parallel tracks that can be owned independently.

Chat shell (`jupyter-chat`). The frontend scaffolding the other tracks plug into.

- A new active-persona field on the input model, set from the draft's `@`-mentions, the last-addressed persona, or the selector, that the controls read. Today the input model only records mentions when a message is submitted, so this is new.
- Slots for the active-persona controls, the per-message footer, and the thinking block. These use extension points that already exist: the input toolbar registry, the message footer registry, and the message preamble registry (already used to render tool calls).
- This track has no backend dependency and can start now.

Persona configuration (ACP client and persona manager). Surface the per-persona settings the agents already expose over ACP. Of the ACP v1 schema's 11 session-update events and 13 RPCs, several that these features need are unhandled today:

- Handle the `config_option_update` and `usage_update` events the client does not consume today, and read the config options already present on the new-session response.
- Implement the `session/set_config_option` call so the model and effort selectors can write back.
- Render the `agent_thought_chunk` events the client currently drops, for the thinking block.
- Expose a persona's current model, effort, and usage to the frontend over a REST endpoint.

Active-persona controls (frontend). The model, effort, and context-usage controls, the running cost total, and the per-message footer, wired to the configuration track and to the active-persona field.

Multi-persona (persona manager and frontend).

- Track which personas a chat is with, saved with the chat, replacing today's eager creation of every persona in every chat.
- Lazy initialization: create a persona when it is first used or added.
- The roster UI, which needs a new chat-header component that does not exist today.
- The routing-clarity changes and the mode-change signal.

Later, smaller gaps:

- Slash-command polish. Autocomplete already works, but agents advertise few commands and the UI does not yet show whose commands are listed.
- Execution-plan and task-list display.
- Session management: list, resume, delete, and graceful close, plus agent-set chat titles.
- Mode selector for agents that expose modes.
- Image paste into the chat input.

## Related discussions

- [Jupyter AI 3.2](jupyter-ai-3.2), the persona API cleanup and persona engines that follow this UI work, and its discussion on [jupyter-ai#1571](https://github.com/jupyterlab/jupyter-ai/issues/1571).
- [jupyter-ai#1558](https://github.com/jupyterlab/jupyter-ai/issues/1558) and the ACP-bridge prototype by Carl Boettiger, Matt Fisher, and others, which surfaced the per-thread harness-binding and model-selection patterns that informed the active-persona design.
