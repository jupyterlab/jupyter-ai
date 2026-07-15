"""Integration tests for the subpackage-docs aggregation.

Every test runs a real ``sphinx-build`` (via the ``make_site`` fixture in
``conftest.py``) against a synthesized filesystem fixture with warnings promoted
to errors (``-W``). Each case asserts the build exits 0 and that the fixture's
own H1 / nav entry appears in the rendered HTML — proving the subpage was staged
*and* wired into the correct aggregation toctree.

Cases (from the design):
  * contributors-only  -> appears under Contributing, not Developers
  * developers-only    -> mirror
  * both               -> appears under both
  * neither / missing index.md -> silently skipped, build still green
  * full subtree with a nested page + an image -> all renders, links resolve
  * baseline: no fixtures -> build succeeds unchanged
"""

from __future__ import annotations

import base64

# A 1x1 transparent PNG — a real, valid image so Sphinx's image handling is
# genuinely exercised (not a placeholder that would warn/error).
_PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def test_contributors_only(make_site):
    """A subpackage shipping only contributor docs appears under Contributing."""
    build = make_site(
        submodules={
            "my-contrib": {
                "contributors": {"index.md": "# My Contrib Guide\n\nHello contrib.\n"}
            }
        }
    )
    assert build.returncode == 0, build.stderr

    # Subpage rendered and its H1 present.
    assert build.exists("contributors/my-contrib/index")
    assert "My Contrib Guide" in build.html("contributors/my-contrib/index")
    # Nav entry injected into the Contributing index (links to the subpage).
    assert "my-contrib/index.html" in build.html("contributors/index")

    # Not staged under Developers, and the Developers index has no toctree link
    # to it. (The title may appear in the global nav sidebar on every page; we
    # assert on the staged path, which is unambiguous.)
    assert not build.exists("developers/my-contrib/index")
    assert "developers/my-contrib" not in build.html("developers/index")


def test_developers_only(make_site):
    """Mirror: developer-only docs appear under Developers, not Contributing."""
    build = make_site(
        submodules={
            "my-dev": {"developers": {"index.md": "# My Dev API\n\nHello dev.\n"}}
        }
    )
    assert build.returncode == 0, build.stderr

    assert build.exists("developers/my-dev/index")
    assert "My Dev API" in build.html("developers/my-dev/index")
    assert "my-dev/index.html" in build.html("developers/index")

    assert not build.exists("contributors/my-dev/index")
    assert "contributors/my-dev" not in build.html("contributors/index")


def test_both_sections(make_site):
    """A subpackage shipping both sections appears under both indexes."""
    build = make_site(
        submodules={
            "full-pkg": {
                "contributors": {"index.md": "# Full Pkg Contributing\n\nc\n"},
                "developers": {"index.md": "# Full Pkg Developing\n\nd\n"},
            }
        }
    )
    assert build.returncode == 0, build.stderr

    assert "Full Pkg Contributing" in build.html("contributors/full-pkg/index")
    assert "full-pkg/index.html" in build.html("contributors/index")
    assert "Full Pkg Developing" in build.html("developers/full-pkg/index")
    assert "full-pkg/index.html" in build.html("developers/index")


def test_neither_and_missing_index_skipped(make_site):
    """Subpackages with no sections, or a section lacking index.md, are skipped.

    The build must still succeed (green) and stage nothing.
    """
    build = make_site(
        submodules={
            # Ships no docs sections at all (only a stray unrelated file).
            "empty-pkg": {"contributors": {}},
            # Ships a contributors section but with no index.* — not stageable.
            "no-index-pkg": {"contributors": {"random.md": "# Orphan\n\nno index\n"}},
        }
    )
    assert build.returncode == 0, build.stderr

    assert not build.exists("contributors/empty-pkg/index")
    assert not build.exists("contributors/no-index-pkg/index")
    # The orphan page must not have been staged either.
    assert not build.exists("contributors/no-index-pkg/random")
    assert "Orphan" not in build.html("contributors/index")


def test_full_subtree_with_nested_page_and_image(make_site):
    """A full subtree (nested page + image) renders and links resolve.

    The subpackage's own index toctree structures the nested page; the image is
    referenced from the nested page. With ``-W`` in effect, any unresolved
    reference or missing image would fail the build.
    """
    index_md = (
        "# Rich Pkg\n\n"
        "Root page.\n\n"
        "```{toctree}\n:maxdepth: 1\n\nsubdir/nested\n```\n"
    )
    nested_md = (
        "# Nested Page\n\n"
        "A nested contributor page with an image.\n\n"
        "![diagram](../_static/diagram.png)\n"
    )
    build = make_site(
        submodules={
            "rich-pkg": {
                "contributors": {
                    "index.md": index_md,
                    "subdir/nested.md": nested_md,
                    "_static/diagram.png": _PNG_1x1,
                }
            }
        }
    )
    assert build.returncode == 0, build.stderr

    # Root + nested pages both rendered.
    assert "Rich Pkg" in build.html("contributors/rich-pkg/index")
    assert build.exists("contributors/rich-pkg/subdir/nested")
    assert "Nested Page" in build.html("contributors/rich-pkg/subdir/nested")
    # The image was copied into the build output.
    assert (build.outdir / "_images").is_dir()
    # Nav entry for the subpackage present on the aggregation index.
    assert "rich-pkg/index.html" in build.html("contributors/index")


def test_baseline_no_submodules(make_site):
    """With no subpackage docs, the build succeeds and adds no subpages."""
    build = make_site(submodules={})
    assert build.returncode == 0, build.stderr

    assert build.exists("contributors/index")
    assert build.exists("developers/index")
    # No injected "Subpackages" caption when nothing was staged.
    assert "Subpackages" not in build.html("contributors/index")
    assert "Subpackages" not in build.html("developers/index")
