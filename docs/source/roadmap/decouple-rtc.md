# Decoupling RTC from Jupyter AI

## Context

Jupyter AI brings AI agents into JupyterLab: a chat interface for talking to agents, and the ability for those agents to read and edit notebooks and files directly. For agent edits to feel live, Jupyter AI currently relies on real-time collaboration (RTC). RTC is the same technology that lets multiple humans co-edit a document. RTC models documents as conflict-free replicated data types (CRDT) replicated between the server and each web client over WebSockets. RTC in Jupyter uses YATA CRDTs powered by `yjs` and `yrs` libraries. Today Jupyter AI depends on RTC for two reasons: the chat itself is modeled as a shared document powered by RTC (`YChat`), and RTC allows agent edits to update the UI in real-time for every file or notebook you have open. Because of this, RTC has been a required dependency since Jupyter AI v3.0.

It is worth being precise about *which* RTC, because the ecosystem has several layers and it is easy to conflate them. At the bottom sit shared libraries used by every RTC implementation in Jupyter -- `pycrdt`, `jupyter_ydoc`, and the underlying `yjs`/`yrs` CRDT implementations. On top of those, two server backends provide the collaboration transport: `jupyter_collaboration` (via its `jupyter_server_ydoc` server extension), the long-standing community implementation; and `jupyter_server_documents` (JSD), a newer backend we built for Jupyter AI. And on top of that lie the labextensions shipped by `jupyter_docprovider` and `jupyter_collaboration_ui`, which power the RTC experience in the web browser, and are shared by Jupyter Collaboration and JSD.

JSD was created as a more minimal RTC server extension that allowed us to experiment with new improvements and bug fixes in an isolated fashion without impacting the existing Jupyter Collaboration codebase. The goal was to achieve a stable RTC experience, then feed bug fixes, design ideas, and lessons learned back upstream. Jupyter AI happens to depend specifically on JSD today -- a default we chose, and one that (as discussed below) should have been made optional. This proposal is *not* a judgment on `jupyter_collaboration`, which is not used by Jupyter AI v3.1 and below, and is blameless in the issues motivating this work. Nor is it an argument that RTC is the wrong long-term vision. It is a narrower, practical claim: RTC should not be a *mandatory* dependency of Jupyter AI, and we need a well-supported path that works without it.

## Motivation

Since Jupyter AI v3.0 launched in April, a recurring class of issues have been reported: most seriously, data loss and file corruption, but also failures like the server and frontend crashing when opening a large notebook. We have investigated these intensively and shipped fix after fix for every condition we could reproduce, yet reports keep arriving, including ones we cannot yet reproduce. A consistent signal in these reports is that these bugs appear more often in remote environments, and that the root causes were all traced to JSD or other packages in the RTC stack. Although it is possible that JSD is exclusively liable for each and every issue, it seems more likely that some are caused by the stack that both JSD and Jupyter Collaboration share. This correlates well with the finding that some bugs were reported to exist in both packages, despite providing two distinct RTC server extensions.

Today, because RTC is required by Jupyter AI, a regression anywhere in JSD or the RTC stack surfaces as a bug for every Jupyter AI user. Users impacted by these bugs have no fallback other than to either wait for a patch or uninstall Jupyter AI. For many prospective groups of users (who could potentially fund Jupyter AI development), this is a deal-breaker. *Any* persistent risk of data loss, however unlikely, is not an acceptable outcome.

However, careful analysis shows that RTC is not strictly necessary for Jupyter AI to work. The file-to-UI sync can be delivered through JupyterLab's existing plugin interfaces; and since chat is an append-only document where each client can only edit their own messages, there are no conflicts that require a CRDT. Given that, coupling Jupyter AI to RTC -- and, furthermore, defaulting them onto JSD without providing a usage path for the already-established Jupyter Collaboration package -- introduces more risk than benefit for the majority of users.

The goal of this proposal is to ***make RTC optional but not removed***: give the default experience a simpler, RTC-free foundation so agent edits and chat work reliably for the common single-user case, while keeping a fully supported optional path for users who want RTC -- with either Jupyter Collaboration or JSD. When complete, Jupyter AI will provide a stable default and not force users to adopt RTC before it is ready. Jupyter AI will stay RTC-compatible, and keep seamless multi-human and multi-agent collaboration on the roadmap as a shiny future we are building together.

## Design Requirements

There are 3 key feature requirements for AI in Jupyter to work. Existing solutions are all either provided by RTC or powered by packages that consume RTC-based APIs to work today. The new design will have to provide a new, RTC-free solution for each requirement, such that `pip install jupyter-ai` gives you a working Jupyter AI experience without requiring RTC.

- **Requirement 1: Filesystem to UI syncing** -- File changes on disk should update the UI *in real-time*, as long as it has a non-dirty state (no unsaved changes), analogous to the experience offered in VSCode and other IDEs.
- **Requirement 2: Chat functionality** -- There must be a chat that provides bidirectional communication between the web client and the server for AI in Jupyter to work.
- **Requirement 3: Jupyter AI plumbing** -- The server must route the user messages to all of the agents provided by Jupyter AI, and route their responses and tool calls back to the chat.

And across all of this, Jupyter AI should continue to support RTC, while providing users the option of using Jupyter Collaboration instead of JSD.

- **Requirement 4: Optional RTC compatibility** -- Users should be able to optionally use Jupyter AI with RTC enabled, and be free to choose between Jupyter Collaboration and JSD as RTC providers.

## Proposal

We propose the following changes to Jupyter AI's architecture:

- **A new RTC-free 'live content provider':** A new extension, tentatively named `jupyterlab_live_content`, will update the UI to respond to file changes on disk in real-time, without requiring RTC. This will leverage the existing plugin interfaces introduced in JupyterLab.

  - This addresses requirement 1.
- **Jupyter Chat powered by simple WebSockets**: This already exists in `jupyterlab-ws-chat` thanks to Nicolas Brichet. It needs to be updated to restore compatibility with `jupyterlab-chat`.

  - This addresses requirement 2.
- **An abstract chat model on the backend**: We need some shared package like `jupyter_chat_core` that defines the Python-side API contracts and schemas which `jupyterlab-chat` and `jupyterlab-ws-chat` must follow. The Jupyter AI subpackages need to be refactored to use the interfaces provided in this new shared package to remove their dependencies on RTC.

  - This addresses requirement 3 and some of requirement 4.

<!-- -->

- **Clever extension configurations that enable seamless transition to RTC**: Finally, we need a simple way to enable or disable the RTC experience that was the default in Jupyter AI v3.1 and below. Users should be able to opt-in by just installing `jupyter_collaboration` or `jupyter_server_documents`, and also be able to turn it off by disabling the RTC server extension(s) or installing the package(s).

  - This addresses requirement 4.

### New package structure

Currently Jupyter AI's dependencies look like this:

```
dependencies = [
  "jupyterlab_chat",
  "jupyter_server_documents",
  "jupyter_ai_router",
  "jupyter_ai_persona_manager",
  "jupyter_ai_chat_commands",
  "jupyter_ai_acp_client",
  "jupyter_server_mcp",
  "jupyter_ai_tools",
  "jupyterlab_notebook_awareness",
  "jupyterlab_commands_toolkit",
]

[project.optional-dependencies]
... # existing optional groups
```

The proposal would split off RTC-only packages into optional dependency groups, refactoring almost all of our packages to work RTC-free. A new extension package, `jupyterlab_live_content`, will be introduced to update the UI in real-time when AI agents make file edits without requiring RTC. `jupyterlab_ws_chat`, an existing chat implementation that just uses simple WebSockets to provide the chat, will replace `jupyterlab_chat` as a required dependency.

The new package structure will look like this:

```yaml
dependencies = [
  "jupyterlab_ws_chat",             # new, provides chat without RTC
  "jupyterlab_live_content",        # new, provides simple FS <=> UI sync without RTC
#  "jupyterlab_chat",               # made optional (RTC-only)
#  "jupyter_server_documents",      # made optional (RTC)
  "jupyter_ai_router",              # refactored
  "jupyter_ai_persona_manager",     # refactored
  "jupyter_ai_chat_commands",       # unchanged (?)
  "jupyter_ai_acp_client",          # refactored
  "jupyter_server_mcp",             # unchanged (?)
  "jupyter_ai_tools",               # refactored
  "jupyterlab_notebook_awareness",  # refactored
  "jupyterlab_commands_toolkit",    # unchanged (?)

]

[project.optional-dependencies]
rtc = ["jupyter_collaboration", "jupyterlab_chat"]
rtc-jsd = ["jupyter_server_documents", "jupyterlab_chat"]
```

## Proposal details

### New RTC-free 'live content provider'

The goal of this component is to make server-side file changes appear in the browser UI in real time without RTC. We propose creating a new extension package named `jupyterlab_live_content`, which ships a lab (frontend) and server extension connected by a single WebSocket endpoint.

While [prior art](#references) is known to us, we believe a dedicated package is still warranted. These efforts are early-stage and not yet available as a released, maintained solution. A focused package lets us ship a working RTC-free experience now, synthesizing ideas from other contributors as it matures. This package will live under the `jupyter-ai-contrib/` org for now. This allows us to ship a fix to affected users as quickly as possible, while maintaining an easy path to move this into an official Project Jupyter org in the future.

#### Frontend

The labextension needs to know exactly which files the user currently has open, so it can (a) tell the server which files to watch and (b) know which open document to refresh when a change arrives. It gets this from two core JupyterLab services:

- `IDocumentWidgetOpener` -- its `opened` signal fires whenever any file-backed document is opened. Each event hands us the document widget, which gives access to the model underneath.
- `ILabShell` -- this lets us enumerate document widgets that were already open before the plugin loaded.

Together these give the plugin a live picture of every open file. The flow is:

1. When a document is opened, the plugin sends the server a message to begin watching that path. When the document is closed (its context is disposed), it tells the server to stop watching.
2. When the server reports that a watched file changed, the plugin finds the corresponding open document and:

   - if the document is not dirty (no unsaved local edits), it calls `context.revert()`, which reloads the content from disk and updates the UI live;
   - if the document is dirty, it does nothing. The user's in-progress edits are preserved, and JupyterLab's built-in save-conflict dialog resolves the divergence the next time they save.

#### Backend

The server extension watches the files that clients report as open and notifies them when those files change on disk. For file watching we propose using [`watchfiles`](https://github.com/samuelcolvin/watchfiles), a Rust-backed library that subscribes to the operating system's native filesystem-notification APIs rather than polling. This makes it both fast and scalable: the OS pushes change events to us, so watching many files costs essentially nothing while idle. These kernel notification APIs are available in virtually all normal deployments; the main exceptions are environments like WSL or unusual filesystems, where `watchfiles` transparently falls back to polling.

The watch set can be scoped to the files clients actually have open rather than every file in the workspace recursively. The server maintains its watch set from the `client_opened` (and, symmetrically, close) messages, so a change to a file nobody is viewing does no work, and a change to a watched file fans out only to the clients viewing it.

#### WebSocket API

The two halves communicate over a single WebSocket endpoint, `/api/live`. The initial message set is intentionally minimal:

```jsonc
// client -> server: "I opened this file; please watch it"
{ "type": "client_opened", "path": "notebooks/analysis.ipynb" }

// server -> client: "this file changed on disk; reload it if you can"
{ "type": "server_update", "path": "notebooks/analysis.ipynb" }
```

#### Scope and future work

Even though reloading the whole document on any change is simple and universal, it reflows the entire UI and resets cursor position and scroll state in the affected document. This is not an ideal user experience and may be slow on browsers with larger files or notebooks open.

One way to (mostly) fix this issue in Jupyter AI is to ensure that Jupyter AI tools forward file updates it made to `jupyterlab_live_content` after making an edit. This naturally lets `jupyterlab_live_content` include a diff, as each tool's arguments already communicate information like "added a new cell 5 after cell 4" or "lines 201-400 have been replaced with new text". By including this diff in updates broadcast by the server, the client can apply the diff cleanly by updating the document model without rebuilding the entire document via `context.revert()`.

The ideal end state is to always have the UI update intelligently, even for out-of-band changes. The server would compute the diff itself if a diff was not received from an AI tool, guaranteeing that reflow is minimized and editor state is preserved. However, this would require diffing on the server, which can be CPU-intensive for large files and requires careful design, validation, and testing against performance benchmarks.

Therefore, these improvements are left out of the initial scope of the proposal. We will make a best-effort to ensure AI edits work well by the minor release date, but will not delay the minor release if the feature cannot be made extremely stable and robust within a few days.

### Jupyter Chat powered by simple WebSockets

This work has already been done in `jupyterlab-ws-chat` by Nicolas Brichet and others. This package only needs to be updated to support the latest Jupyter Chat library and APIs, and implement the new interfaces as described in the next section. There are two potential futures for this repo:

1. Move this into the `jupyterlab/jupyter-chat` repo, or
2. Move the repo under the `jupyter-ai-contrib/` GitHub org.

As both `jupyterlab-chat` and `jupyterlab-ws-chat` are both powered by the same `@jupyter/chat` NPM library package, restoring compatibility between the two implementations is not expected to be difficult (relative to the other sections of this proposal).

### Abstract chat model on the backend

Currently, Jupyter Chat consumers on the server-side directly use the `YChat` interface to perform operations on a chat, which has to be generalized to support both RTC-free and RTC-based implementations. There is currently no server-side analogue of the  `@jupyter/chat` NPM package, which defines a standard interface and library that frontend consumers may use to provide other implementations.

To allow RTC-free and RTC-based chat implementations to be swappable, there needs to be a Python library that defines the API contract that providers may implement, while being separate from any specific implementation. For this, we propose a new Python package in the `jupyterlab/jupyter-chat` repo: `jupyter_chat_core`.

This new package may have a structure like this:

```
jupyter_chat_core/
|- interfaces/  # abstract classes, dataclass definitions, etc.
|- lib/         # things that are useful to both implementations
|- extension.py # the server extension
```

The most important new pieces of this are:

- `interfaces/abstract_chat.py` - defines the `AbstractBaseChat` class that `YChat` and `WsChat` may implement.
- `interfaces/message.py` - definition of the `Message` interface (currently as a dataclass)
- `lib/__init__.py` - defines shared library functions.

  - `get_rtc_provider(serverapp: ServerApp)` - a unified way to determine which RTC provider is available, if any.
  - `get_chat_provider(serverapp: ServerApp)` - a unified way to determine which chat implementation wins if both are available, based on whether an RTC provider is available
- `extension.py` - a minimal server extension that advertises this to frontend plugins via `PageConfig`

### Clever extension configurations that enable seamless transition to RTC

In the previous section, we proposed a design to create a shared package that allows the chat implementation to be modularized. But if both are installed, how do we pick the right implementation? In other words, how is `get_chat_provider()` implemented?

We need a way to control extension behavior based on the environment. A naive way to approach this is to just detect if RTC packages are installed to determine whether to use RTC:

```
# naive way
def get_chat_provider():
    """Picks the right server extension to provide the chat feature based on env"""
    HAS_RTC = 0
    try:
      import jupyter_collaboration
    except:
      try:
        import jupyter_server_documents
      except:
        HAS_RTC = 1

    return 'jupyterlab_chat' if HAS_RTC else 'jupyterlab_ws_chat'
```

However, it's not enough to just check whether an RTC extension is installed. An RTC extension must be both installed and enabled for this server session for RTC to support to exist. If the above code were used as-is, admins would have no way to configure a space to not use RTC when `jupyter_collaboration` or `jupyter_server_documents` is installed. This is a valid concern for admins who may deploy both private and RTC instances from a single image or Dockerfile. For these users, Jupyter AI cannot break when RTC is installed but disabled.

The right approach is to use the `ServerApp` object to discover which extensions are actually installed and enabled.

```python
from __future__ import annotations

from typing import Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from jupyter_server.serverapp import ServerApp

# --- RTC providers -----------------------------------------------------------

RTCProvider = Literal["jupyter_server_documents", "jupyter_server_ydoc"]

# RTC providers are the backend server extensions that supply the shared-document
# (YCRDT) transport `jupyterlab_chat` relies on. jupyter_chat_core only needs
# their *names* -- it never imports them or touches their internals.
RTC_PROVIDERS: set[RTCProvider] = {"jupyter_server_documents", "jupyter_server_ydoc"}

# --- Chat providers ----------------------------------------------------------

ChatProvider = Literal["jupyterlab_chat", "jupyterlab_ws_chat"]

# A "chat provider" is the server extension that owns the chat feature for a
# given session: it ships the chat UI plugin and the server side that backs it.
# Exactly one is active at a time. The two implementations differ only in how
# chat state is stored and transported to the browser:
#   - CHAT_RTC_YCRDT: chat lives in a shared YDoc/CRDT that an RTC provider
#     replicates to clients. Requires an RTC provider to actually serve it (its
#     own server side is just a doc-type registration).
#   - CHAT_WS: a standalone websocket chat that owns its own state and transport
#     -- no RTC, no CRDT. The universal fallback.
CHAT_RTC_YCRDT: ChatProvider = "jupyterlab_chat"
CHAT_WS: ChatProvider = "jupyterlab_ws_chat"

CHAT_PROVIDERS: set[ChatProvider] = {CHAT_RTC_YCRDT, CHAT_WS}

# --- Detection ---------------------------------------------------------------

def _is_enabled(serverapp: "ServerApp", name: str) -> bool:
    """True iff `name` is a server extension that is *configured AND enabled* for
    THIS session.

    Authoritative, unlike `import name`: returns False when the package is
    installed but disabled via `jupyter server extension disable <name>`.
    Enablement is resolved from merged jpserver_extensions config before any
    extension loads, so this is safe to call from an extension's initialize().
    """
    ext = serverapp.extension_manager.extensions.get(name)
    return bool(ext and ext.enabled)

def get_rtc_provider(serverapp: "ServerApp") -> Optional[RTCProvider]:
    """Name of the enabled RTC provider, or None if RTC is off.

    If both are enabled, jupyter_server_documents (JSD) wins. (In practice JSD
    ships config that disables jupyter_server_ydoc, so both-enabled only happens
    if an admin re-enables JSY.) Asks the server which extensions are enabled;
    knows nothing about how any provider actually works.
    """
    enabled = {name for name in RTC_PROVIDERS if _is_enabled(serverapp, name)}
    if "jupyter_server_documents" in enabled:
        return "jupyter_server_documents"
    if "jupyter_server_ydoc" in enabled:
        return "jupyter_server_ydoc"
    return None

def get_chat_provider(serverapp: "ServerApp") -> Optional[ChatProvider]:
    """Pick the chat server extension that should be active this session.

    Every extension that calls this reads the same serverapp state, so each one
    independently reaches the SAME verdict -- no handshake needed.

      1. RTC provider enabled AND jupyterlab_chat enabled -> CHAT_RTC_YCRDT
      2. else jupyterlab_ws_chat enabled                  -> CHAT_WS
      3. else (nothing viable)                            -> None  # caller fails loud

    `jupyterlab_chat` is only viable with an RTC provider (its server side is a
    hollow shell; transport comes from the RTC backend), so it's never chosen
    when RTC is off -- ws-chat is the universal fallback.
    """
    if get_rtc_provider(serverapp) and _is_enabled(serverapp, CHAT_RTC_YCRDT):
        return CHAT_RTC_YCRDT
    if _is_enabled(serverapp, CHAT_WS):
        return CHAT_WS
    return None
```

`jupyter_chat_core`, in addition to providing library functions, will also be a server extension. For now, it will just serve to publish this information to the frontend via `PageConfig` under the `chatServerSessionInfo` key. The frontend will query it using the `getChatServerSessionInfo()` function (which gets added to `@jupyter/chat` NPM package):

```typescript
import { PageConfig } from '@jupyterlab/coreutils';

// Mirror of the Python Literals in jupyter_chat_core (server module names).
export type RTCProvider = 'jupyter_server_documents' | 'jupyter_server_ydoc';
export type ChatProvider = 'jupyterlab_chat' | 'jupyterlab_ws_chat';

export interface IChatServerSessionInfo {
  /** Winning chat provider, or null if none is viable. */
  activeChatProvider: ChatProvider | null;
  /** True iff an RTC provider is enabled this session. */
  rtcEnabled: boolean;
  /** Which RTC backend is active (informational), or null. */
  rtcProvider: RTCProvider | null;
}

export const CHAT_CORE_PAGE_CONFIG_KEY = 'chatServerSessionInfo';


/** Read the chat-core config the server published into page config. */
export function getChatServerSessionInfo(): IChatServerSessionInfo {
  const raw = PageConfig.getOption(CHAT_CORE_PAGE_CONFIG_KEY);
  // getOption always returns a string ('' if unset); raise error if unset
  if (!raw) { throw new Error("'chatServerSessionInfo' not found in PageConfig."); }
  return JSON.parse(raw);
}
```

For every extension that either requires RTC to be enabled or requires RTC to be disabled:

- Every labextension plugin should only be disabled if the `PageConfig` indicates the corresponding server extension is not the one being used for this session.
- The server extension should import `get_chat_provider()` from `jupyter_chat_core.lib`, run the function to determine whether they will be used in this session, and do nothing if not being used in this session.

The following packages get disabled when RTC is *not* enabled:

- `jupyterlab_chat` (if installed)

The following packages get disabled when RTC *is* enabled:

- `jupyterlab_live_content`
- `jupyterlab_ws_chat`

The following packages remain enabled regardless, but have different behavior based on whether RTC is enabled in the server session:

- `jupyter-ai-router`
- `jupyter-ai-tools`
- `jupyterlab-notebook-awareness`

### How admins can turn RTC on and off

Users can enable RTC simply by installing the optional dependency group they want:

```
# enable RTC via Jupyter Collaboration
pip install "jupyter-ai[rtc]"

# enable RTC via Jupyter Server Documents
pip install "jupyter-ai[rtc-jsd]"
```

To turn RTC off, either:

1. Uninstall `jupyter_collaboration` (or `jupyter_server_documents`), or
2. Disable `jupyter_server_ydoc` (or `jupyter_server_documents`) via `jupyter server extension disable ...`.

   1. And to undo this, just repeat this with `jupyter server extension enable ...`.

### Jupyter AI refactoring

Almost all of the Jupyter AI subpackages need to be refactored to consume any implementation of `AbstractBaseChat` instead of just `YChat`. They will depend on `jupyter_chat_core` to provide the expected interfaces and APIs, and none should explicitly require `jupyterlab_chat` or `jupyterlab_ws_chat`. As described before, any packages that either require or conflict with RTC should automatically disable themselves by using `jupyter_chat_core` to query their environment.

This should get us 80% of the way there. To limit its length, this proposal doesn't go into detail on how these packages will be implemented:

- `jupyter-ai-tools` : the tools need to be refactored to also work without RTC.
- `jupyterlab-notebook-awareness` : the user's notebook state is advertised over each notebook's Yjs awareness channel. We will need to add an RTC-free implementation that works.

Both of these packages will likely have to rely on conditional imports for now to support areas where `jupyter_server_documents` or `jupyter_collaboration` APIs are needed, since those packages are not guaranteed to be installed anymore. This is a bit ugly and may cause type hinting issues, but it is safe in the Python runtime, and can be refactored in future releases once a proof-of-concept is reached.

## Roadmap

Development will be tackled in 4 key phases:

1. Initial setup

   1. Set up `jupyter_chat_core`
   2. Set up `jupyterlab_live_content`
   3. Update `jupyterlab_ws_chat`
2. Jupyter AI proof-of-concept

   1. Update `jupyter-ai-router`
   2. Update `jupyter-ai-persona-manager` , `jupyter-ai-acp-client`, and other core packages.
3. Jupyter AI feature completeness

   1. Update `jupyterlab_notebook_awareness` to work RTC-free
   2. Update `jupyter_ai_tools` to work RTC-free
   3. Update optional packages `jupyter-ai-magic-commands` and `jupyter-ai-jupyternaut` as time permits.
4. Testing, validation, and finishing touches

   1. Add tests that assert Jupyter AI works in all 3 supported modes: RTC-free, RTC with Jupyter Collaboration, and RTC with Jupyter Server Documents. (may get split up in CI pipelines over various packages)
   2. Fix any bugs found along the way
   3. Ship pre-releases, test, and get feedback on the experience
   4. Update documentation and add Jupyter AI release notes for next minor release

We hope to ship this by 2026-09-01.

## References

**Existing requests to provide these features without RTC**

- Explicit request for this on the Jupyter Community Forum: https://discourse.jupyter.org/t/using-jupyter-ai-without-real-time-collaboration-rtc/38782
- Upstream issue in JupyterLab by `@ctcjab`: https://github.com/jupyterlab/jupyterlab/issues/18699

**Prior art at decoupling RTC from the file-sync UI**

While prior art is known to us, we believe a dedicated package is still warranted: these efforts are early-stage and not yet available as a released, maintained solution, and the upstream PR is paused pending a larger redesign. A focused package lets us deliver a working RTC-free experience now while aligning with the upstream direction (contents-manager-level detection via `watchfiles`), so it can converge with — or be upstreamed into — JupyterLab later.

- JupyterLab PR by `@xicoo22`: https://github.com/jupyterlab/jupyterlab/pull/18944 — adds OS-level external change detection; currently unmerged, with maintainers favoring a contents-manager-level design built on `watchfiles`.
- Unofficial extension by `@kolibril13`: https://github.com/kolibril13/hot-notebook-patching — an experimental approach to patching open notebooks from external changes.
