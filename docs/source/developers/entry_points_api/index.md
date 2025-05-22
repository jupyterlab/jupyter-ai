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

The entry points API currently includes the following entry point groups:

- `'jupyter_ai.personas'`: allows developers to add AI personas.

- `'jupyter_ai.model_providers'`: allows developers to add model providers.

- `'jupyter_ai.embeddings_model_providers'`: allows developers to add embedding model providers.

Each entry point group used by Jupyter AI is documented in a section below,
which describes the type of object expected and how to define a custom
implementation.

At the end, we describe how to provide an entry point using a custom
implementation in your package.

```{toctree}
:caption: Contents

personas_group.md
model_providers_group.md
embeddings_providers_group.md
providing_entry_points.md
```

[entry_points]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html