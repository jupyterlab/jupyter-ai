# Entry points API

The [**entry points API**][entry_points] allows other packages to add custom
objects to Jupyter AI's backend. Jupyter AI defines a set of **entry point
groups**. Each entry point group is reserved for a specific type of object, e.g.
one group may be reserved for personas and another may be reserved for model
providers.

A package can *provide* an **entry point** to an entry point group to add an
object of the type reserved by the group. For example, providing an entry point
to the personas group will add a new AI persona to Jupyter AI. A package can
also provide multiple entry points to the same group.

The entry points API currently includes the Personas group, see the repository 
[`jupyter-ai-persona-manager`](https://github.com/jupyter-ai-contrib/jupyter-ai-persona-manager) which allows developers to add AI personas.

The entry point group for personas is `jupyter-ai.personas`.

Here, we describe how to provide an entry point using a custom
implementation in your package.

```{toctree}
:caption: Contents

personas_group.md
<!-- model_providers_group.md
embeddings_providers_group.md -->
providing_entry_points.md
```

[entry_points]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
