"""Sphinx extension: auto-generated API reference for subpackages.

This is the auto-generation counterpart to ``subpackage_docs.py``. Where that
extension *aggregates* hand-written subpackage docs, this one wires up the
machinery so a subpackage's contributor/developer pages can pull their API
reference straight from source with ``sphinx.ext.autodoc`` directives, e.g.::

    ```{eval-rst}
    .. autoclass:: jupyter_ai_persona_manager.BasePersona
       :members:
    ```

    ```{eval-rst}
    .. autopydantic_model:: jupyter_ai_persona_manager.PersonaDefaults
    ```

It bundles three things so the main ``conf.py`` only has to load one extension:

1. The autodoc stack — ``sphinx.ext.autodoc``, ``sphinx.ext.napoleon`` (Google/
   NumPy docstrings), ``sphinx.ext.linkcode`` (source links), and
   ``sphinxcontrib.autodoc_pydantic`` (rich Pydantic model docs).
2. Sensible default settings for those extensions.
3. A ``linkcode_resolve`` that maps any documented object to a **GitHub source
   URL with a line range**, pinned to the commit of the checkout the object was
   imported from. The module→repo map is derived from
   ``submodules/manifest.json``, so no per-object links are ever maintained by
   hand.

For autodoc to import a subpackage, that subpackage must be importable in the
docs build environment (installed, not merely present as a docs-only submodule).
On Read the Docs that means installing the subpackages; locally the workbench
dev-installs them.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

# Extensions this one pulls in. Loaded via `app.setup_extension` in `setup`.
_BUNDLED_EXTENSIONS = (
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.linkcode",
    "sphinxcontrib.autodoc_pydantic",
)

# Opinionated defaults for the bundled extensions. Set as config defaults (not
# forced) so a subpackage or the main conf can still override them.
_CONFIG_DEFAULTS = {
    "autodoc_member_order": "bysource",
    "autodoc_typehints": "description",
    "autoclass_content": "class",
    # autodoc_pydantic: keep it readable — a field summary table, constraints,
    # and defaults, but not the JSON schema / validator noise.
    "autodoc_pydantic_model_show_json": False,
    "autodoc_pydantic_model_show_config_summary": False,
    "autodoc_pydantic_model_show_validator_summary": False,
    "autodoc_pydantic_model_show_validator_members": False,
    "autodoc_pydantic_field_list_validators": False,
    "autodoc_pydantic_model_member_order": "bysource",
    "autodoc_pydantic_field_show_constraints": True,
    "autodoc_pydantic_model_show_field_summary": True,
}


@lru_cache(maxsize=1)
def _module_to_repo(submodules_root_str: str) -> dict[str, str]:
    """Map each subpackage's importable top-level module → ``org/repo``.

    Derived from ``submodules/manifest.json`` (``"pypi_name": "org/repo"``). The
    manifest key is the PyPI/import name (``jupyter_ai_persona_manager``); the
    value's repo half is the GitHub repo. This is exactly the mapping
    ``linkcode`` needs to turn ``info["module"]`` into a repo.
    """
    manifest_path = Path(submodules_root_str) / "manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = json.loads(manifest_path.read_text())
    return {pypi_name: org_repo for pypi_name, org_repo in manifest.items()}


@lru_cache(maxsize=None)
def _revision_for(repo_dir: str, top_module: str) -> str:
    """Resolve a stable git ref to pin source links to, for ``top_module``.

    Order of preference:

    1. The git commit SHA of the checkout at ``repo_dir`` — correct for a local
       editable/dev install (e.g. the workbench dev worktree), and pins links to
       exactly the code being documented.
    2. The installed package version mapped to a ``v``-prefixed tag
       (``0.1.0b1`` → ``v0.1.0b1``) — correct on Read the Docs, where the
       subpackage is pip-installed from PyPI into a non-git ``site-packages``.
       Contrib repos tag releases uniformly ``v``-prefixed, matching this.
    3. ``main`` as a last resort.

    Either way the resulting links point at the same source the build imported.
    """
    try:
        sha = subprocess.check_output(
            ["git", "-C", repo_dir, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return sha.decode().strip()
    except Exception:
        pass
    try:
        import importlib.metadata as md

        return "v" + md.version(top_module)
    except Exception:
        return "main"


def _make_linkcode_resolve(submodules_root: Path):
    module_to_repo = _module_to_repo(str(submodules_root))

    def linkcode_resolve(domain, info):
        if domain != "py" or not info["module"]:
            return None

        top = info["module"].split(".")[0]
        org_repo = module_to_repo.get(top)
        if not org_repo:
            return None

        try:
            module = importlib.import_module(info["module"])
        except Exception:
            return None

        obj = module
        for part in info["fullname"].split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        obj = inspect.unwrap(obj)

        try:
            source_file = inspect.getsourcefile(obj)
            source, start = inspect.getsourcelines(obj)
        except (TypeError, OSError):
            return None
        if not source_file:
            return None

        # Repo-relative path: keep everything from the top-level module dir on.
        parts = source_file.split(os.sep)
        try:
            idx = len(parts) - 1 - parts[::-1].index(top)
        except ValueError:
            return None
        rel_path = "/".join(parts[idx:])

        rev = _revision_for(os.path.dirname(source_file), top)
        end = start + len(source) - 1
        return f"https://github.com/{org_repo}/blob/{rev}/{rel_path}#L{start}-L{end}"

    return linkcode_resolve


# Attribute a subpackage may stamp on a member to declare its "contract level"
# (how a subclass author should treat it). Read duck-typed so this extension
# stays decoupled from any one subpackage. The value is expected to have a
# ``.label`` (e.g. "Required") and a ``.rfc2119`` sentence; a plain string works
# too. See jupyter_ai_persona_manager.contract for the reference implementation.
_CONTRACT_ATTR = "__contract_level__"


def _contract_of(obj):
    """Return (label, rfc2119) for a documented object, or None if untagged."""
    target = getattr(obj, "fget", obj)  # unwrap property
    level = getattr(target, _CONTRACT_ATTR, None)
    if level is None:
        return None
    label = getattr(level, "label", None) or str(level).title()
    detail = getattr(level, "rfc2119", "")
    return label, detail


def _inject_contract_badge(app, what, name, obj, options, lines):
    """autodoc-process-docstring: prepend a contract badge to a member's docs.

    Runs for every autodoc'd object. If the object carries a contract-level tag,
    insert a bold badge line (e.g. **[Required]** MUST be implemented …) at the
    top of its rendered docstring, so the auto-generated API reference shows the
    same Required/Recommended/Optional/Provided classification the source
    declares.
    """
    if what not in ("method", "function", "attribute", "property"):
        return
    contract = _contract_of(obj)
    if contract is None:
        return
    label, detail = contract
    badge = f"**[{label}]** {detail}".rstrip()
    # Insert at the very top, followed by a blank line to keep RST/MyST happy.
    lines.insert(0, "")
    lines.insert(0, badge)


# Order the contract groups are rendered in, with their headings/blurbs. The
# keys are the ``.label`` values a subpackage's contract levels expose.
_CONTRACT_GROUPS = [
    ("Required", "**MUST** be implemented — the class is abstract without these."),
    ("Recommended", "**SHOULD** be implemented — a default exists, but most personas override these."),
    ("Optional", "**MAY** be implemented — a safe default covers personas that don't need these."),
    ("Available to subclasses", "Provided by the base class for a persona to **call** from inside itself; may be overridden."),
    ("Available to consumers", "Provided by the base class for **consumers** (e.g. the ``PersonaManager``) to call on a persona; generally not overridden."),
]


class ContractApiDirective(Directive):
    """``.. contract-api:: pkg.mod.Class`` — grouped, auto-generated API reference.

    Introspects the class's public members, partitions them by their contract
    level tag (``__contract_level__``), and emits an ``autoclass`` for the class
    followed by one grouped section per level (Required / Recommended / Optional
    / Provided), each listing only its members via ``automethod`` /
    ``autoattribute``. Members without a tag fall into an "Other" group so
    nothing is silently dropped.

    This gives the same category separation the source declares, generated — no
    hand-maintained member lists.
    """

    required_arguments = 1
    has_content = False

    def run(self):
        target = self.arguments[0]
        module_name, _, class_name = target.rpartition(".")
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("contract-api: cannot import %s (%s)", target, exc)
            return []

        # Partition public members by contract label, preserving source order.
        groups: dict[str, list[tuple[str, bool]]] = {}
        for name, obj in vars(cls).items():
            if name.startswith("_"):
                continue
            if not (inspect.isfunction(obj) or isinstance(obj, property)):
                continue
            contract = _contract_of(obj)
            label = contract[0] if contract else "Other"
            is_attr = isinstance(obj, property)
            groups.setdefault(label, []).append((name, is_attr))

        # Class header (signature, class docstring, source link) without members.
        result: list[nodes.Node] = []
        result += self._parse_rst([f".. autoclass:: {target}", "   :no-members:", ""])

        ordered = _CONTRACT_GROUPS + [("Other", "")]
        for label, blurb in ordered:
            members = groups.get(label)
            if not members:
                continue
            # Build a real section per contract group so it becomes a navigable
            # "On this page" sidebar entry, while the individual members below it
            # stay out of the TOC (see toc_object_entries=False). Section nodes
            # need an id + a title child; we construct them explicitly because
            # nested_parse of an RST underline doesn't promote to a title here.
            section = nodes.section()
            section_id = nodes.make_id(f"contract-{label}")
            section["ids"].append(section_id)
            section["names"].append(section_id)
            section += nodes.title(text=label)
            self.state.document.note_implicit_target(section, section)

            body: list[str] = []
            if blurb:
                body += [blurb, ""]
            for name, is_attr in members:
                directive = "autoattribute" if is_attr else "automethod"
                body += [f".. {directive}:: {target}.{name}", ""]
            section += self._parse_rst(body)
            result.append(section)

        return result

    def _parse_rst(self, lines: list[str]) -> list[nodes.Node]:
        """Parse a block of generated RST and return its child nodes."""
        container = nodes.section()
        container.document = self.state.document
        self.state.nested_parse(StringList(lines), self.content_offset, container)
        return container.children


def setup(app: Sphinx) -> dict:
    for ext in _BUNDLED_EXTENSIONS:
        app.setup_extension(ext)

    app.connect("autodoc-process-docstring", _inject_contract_badge)
    app.add_directive("contract-api", ContractApiDirective)

    # confdir is docs/source; submodules root is <repo>/submodules.
    submodules_root = Path(app.confdir).parent.parent / "submodules"

    # Register linkcode_resolve. linkcode reads it from config at build time.
    app.config.linkcode_resolve = _make_linkcode_resolve(submodules_root)

    # Apply our defaults without clobbering anything already set in conf.py.
    for key, value in _CONFIG_DEFAULTS.items():
        if getattr(app.config, key, None) in (None, "", [], {}):
            try:
                app.config[key] = value
            except Exception:
                pass

    # `toc_object_entries` defaults to True, so the "only if falsy" rule above
    # can't turn it off. We keep autodoc'd members out of the page TOC
    # unconditionally (unless conf.py explicitly opts back in) — this is what
    # keeps the API page's right sidebar to a handful of section entries instead
    # of one per member.
    if "toc_object_entries" not in app.config.overrides:
        app.config.toc_object_entries = False

    return {"parallel_read_safe": True, "parallel_write_safe": True}
