# Jupyter AI 3.2 proposal

## Context

In Jupyter AI 3.0, instead of building our own agent, we wrap existing agent harnesses through the Agent Client Protocol (ACP) and present them as personas. This integrated eight frontier agents (Claude, Kiro, Copilot, Gemini, Goose, Codex, OpenCode, Mistral Vibe) in under two months, each available in any chat and invokable by `@`-mention.

[Jupyter AI 3.1](jupyter-ai-3.1), also known as Persona API v0.1, makes a persona configurable at runtime on the backend. It moves a persona's model, context, identity, and options out of the class definition into instance attributes, and adds `update_model`, `update_context`, `update_identity`, and `update_options` to change them while a chat is live. It covers the API, not the UI: a user still has no way to change those settings from the chat.

Jupyter AI 3.2 builds the UI on top of it: in-chat controls for model, effort, and usage that bring Jupyter AI to parity with popular agentic editors, while keeping what sets it apart, the ability to work with several personas, and several people, in one chat. The result is one kind of chat, as polished as those tools, that works the same whether you are talking to one persona or several.

## Motivation

Users coming from other popular agentic editors and AI assistants expect a consistent set of controls quickly available in the chat UI. Those tools ship them by default; Jupyter AI ships almost none:

| Feature | Popular agentic editors | Jupyter AI |
|---|---|---|
| Model selector | Yes | No, buried in a settings panel |
| Effort / reasoning level | Yes | No |
| Context usage | Yes | No |
| Session cost | Yes | No |
| Thinking display | Yes | No |
| Slash commands | Yes | Partial, no autocomplete polish |

These are non-trivial to add because of the multi-persona chat paradigm Jupyter AI works in. In other tools, a single conversation is built around one assistant, and the controls assume it; the ones that run several agents at once give each its own separate pane or thread. Jupyter AI is the one place they truly come together: several AI personas and several people collaborating in a single chat, where any message can address any persona. If a chat holds `@Claude` and `@Kiro`, which one's model selector belongs in the input box, which one's slash commands should autocomplete, and which one's context window does the indicator track?

This is the core problem 3.2 solves: how to show persona-specific data and options in a chat that can hold more than one persona, without splitting the product into two different kinds of chat.

Two related gaps compound it:

- All installed personas are initialized eagerly in every chat, and therefore all personas participate in every chat by default. There is no way to remove or add a persona.
- Persona configuration has no home in the chat. The settings that 3.1 makes changeable at runtime have nowhere to be changed from.

## Goals

3.2 provides the 3.1 persona API with a great UI: the state-of-the-art controls users expect from popular agentic editors, adapted to Jupyter AI's paradigm of several personas in one chat.

## A single set of in-chat controls

The design resolves the ambiguity with a single active persona: in a chat that holds several, the persona the input is currently addressed to. The model, effort, and usage controls live in the chat input and act on the active persona, so there is always exactly one persona's model selector to show, one set of slash commands to autocomplete, and one context window to track.

The active persona is detected automatically:

- In a chat with one persona, it is always that persona.
- When you `@`-mention a persona, it becomes active and stays active for the messages that follow, so you do not retype the `@` every time. Carl Boettiger's feedback in #1558 notes that users repeatedly forget the `@`; because the active persona persists and is always shown, a forgotten `@` is visible rather than silent.
- On a new chat, it is the default persona the chat opened with.

The input area shows the active persona next to the controls, so the user always knows who the next message will go to and whose settings they are seeing; if it is wrong, an `@`-mention fixes it. The controls change only in response to what the user types, never on their own. Changing the model or effort takes effect on the next message and is saved with the chat, and the context-and-cost indicator reflects the active persona, not the whole chat.

In a chat with one persona, the input area looks and behaves like a normal single-assistant tool. There is no separate chat type: a single-persona chat is just the multi-persona chat with one persona in it.

Persona information appears in two places:

- In the input area, for the active persona: the model the next message will use, the effort level, and the context left before compaction. This is the live state.
- In a footer on each message: the model, token count, and cost for that turn. This is the record of what already happened.

```text
+--------------------------------------------------------+
| Chat: cleanup.ipynb              [Claude] [Kiro]   (+) |
|                                                        |
|  Claude   Opus . 1,240 tokens . $0.03   <- msg footer  |
|  ...                                                   |
+--------------------------------------------------------+
| To: Claude      [Opus v]  [high v]      ctx 64%        |
| Type a message...                           [stop] [^] |
+--------------------------------------------------------+
```

This is a rough sketch; polished mockups will come with the prototype.

We considered two alternatives. Showing this information only per message gives no live controls, so a user could not change a model or effort before sending. A separate per-persona options panel duplicates the chat UI in a second place and pulls configuration away from where the user types. Putting the controls in the input area keeps them next to the message being written, with no separate place to manage.

## Personas in a chat

A chat has a default persona, so a single-persona experience works without any setup. To bring in another, the user `@`-mentions it or adds it from the roster; from then on the active persona follows whoever they address.

- The chat header shows a roster of the personas in the chat, the participant list any group chat has, like the member list in Slack or Discord: avatars with an add control that lists your installed personas, and a remove control on each.
- The create button is labeled "New chat".

## Routing clarity

Jupyter AI already changes its routing behavior based on who is in a chat, but it does so invisibly. While a single human is in a chat, a message that mentions no one goes to a default persona. As soon as a second human is present, personas fall silent unless a message explicitly mentions them. The intent is reasonable, to keep agents from talking over a human-to-human conversation, but because nothing in the UI signals the switch, users read it as the assistant breaking.

The active-persona indicator and the roster make routing visible instead of hidden. The roster shows who can respond, and the indicator shows who the next message is going to. We will also signal the mode change directly, so when routing shifts to mention-only the user understands why. The implementation of the routing changes lands in the multi-persona phase below; 3.2 commits to naming the behavior and making it visible.

## Local and global configuration

3.2 draws a clear line between two kinds of configuration that are easy to conflate.

- Local configuration changes one persona's behavior inside one chat. Setting `@Claude` to Opus at high effort in this chat is local. It is set from the active persona's controls and the roster, and stored with the chat.
- Global configuration defines the defaults for all personas in all new chats. The default model, the allowed-model list, and the persona definitions from 3.1 are global. These stay in the settings panel.

Keeping the two separate lets a user tune a persona for the task in front of them without changing their defaults everywhere. The proposal treats "edit this chat's persona" and "edit my defaults" as distinct actions with distinct homes.

## User stories

- As a Jupyter user, I want a new chat to be ready to talk to an assistant immediately, so I can start working without any setup.
- As a Jupyter user, I want to change the model or effort for the assistant I am talking to from the chat itself, so I can match the task without digging through settings.
- As a Jupyter user working with several assistants at once, I want to see which one I am addressing and have it stay until I address another, so I am not retyping `@` on every message.
- As a Jupyter user, I want each reply to show which model produced it and what it cost, so I can keep track of what I am spending.
- As a Jupyter user, I want to add a persona to a chat or remove one, so the chat holds exactly the assistants I need.
- As someone sharing a chat with a teammate, I want it to be clear when the assistants will reply on their own and when they will not, so their silence is not confusing.

## Plan

3.2 ships in two phases, then a backlog of smaller gaps. The two phases share one design; phase one delivers it for a single persona, so none of that work is wasted when phase two adds the rest.

Phase one, a great single-persona chat: the model, effort, and context-and-cost controls in the input, thinking shown as a collapsible block, a per-message footer with the model and cost, and a new chat that is ready to use immediately. This is the bulk of the value, and it has no dependency on the multi-persona work.

Phase two, multiple personas: the roster with add and remove, lazy initialization, the routing-clarity changes, and the local-and-global configuration split.

Later, smaller gaps:

- Slash-command polish. Autocomplete already works, but agents advertise few commands and the UI does not yet show whose commands are listed.
- Execution-plan and task-list display.
- Session management: list, resume, delete, and graceful close, plus agent-set chat titles.
- Mode selector for agents that expose modes.
- Image paste into the chat input.

## Delivery as workstreams

The phases split into tracks that can largely run in parallel and be owned independently. The first three deliver phase one; the last is phase two.

Chat shell (`jupyter-chat`). The frontend scaffolding the other tracks plug into.

- The new-chat experience: a default persona on open and the "New chat" label.
- A new active-persona field on the input model, derived from the draft's `@`-mentions and the last-addressed persona, that the controls read. Today the input model only records mentions when a message is submitted, so this is new.
- Slots for the active-persona controls, the per-message footer, and the thinking block. These use extension points that already exist: the input toolbar registry, the message footer registry, and the message preamble registry (already used to render tool calls).
- This track has no backend dependency and can start now.

Persona configuration (ACP client and persona manager). Make the per-persona settings real on the backend. Of the 24 capabilities in the ACP v1 schema (11 events, 13 calls), 11 are implemented, and the ones these features need are among the gaps.

- Handle the `config_option_update` and `usage_update` events the client currently discards, and read the config options already present on the new-session response.
- Implement the `session/set_config_option` call so the model and effort selectors can write back.
- Render the `agent_thought_chunk` events the client currently drops, for the thinking block.
- Expose a persona's current model, effort, and usage to the frontend over a REST endpoint.

Active-persona controls (frontend). The model, effort, and context-and-cost controls and the per-message footer, wired to the configuration track and to the active-persona field.

Multi-persona (persona manager and frontend).

- Track which personas a chat is with, saved with the chat, replacing today's eager creation of every persona in every chat.
- Lazy initialization: create a persona when it is first used or added.
- The roster UI, which needs a new chat-header component that does not exist today.
- The routing-clarity changes and the mode-change signal.

## Related efforts

- [Jupyter AI 3.1](jupyter-ai-3.1), the runtime-configuration persona API this UI is built on, and its discussion on [jupyter-ai#1571](https://github.com/jupyterlab/jupyter-ai/issues/1571).
- [jupyter-ai#1558](https://github.com/jupyterlab/jupyter-ai/issues/1558) and the ACP-bridge prototype by Carl Boettiger, Matt Fisher, and others, which surfaced the per-thread harness-binding and model-selection patterns that informed the active-persona design.
- The ACP integrations in [jupyter-ai-acp-client](https://github.com/jupyter-ai-contrib/jupyter-ai-acp-client), whose session config options and usage events 3.2 will start consuming.
- The agent panels in [Zed](https://zed.dev/docs/ai/agent-panel), [Cursor](https://docs.cursor.com/), and [VS Code Copilot](https://code.visualstudio.com/docs/copilot/chat/copilot-chat), and the model switcher in [T3 Chat](https://t3.chat), whose in-chat model, effort, and usage controls set the bar for the single-persona experience.
- [cmux](https://github.com/manaflow-ai/cmux), a terminal for running several AI coding agents in parallel, a reference for presenting more than one agent in one place.
