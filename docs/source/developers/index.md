# Developers

The developer documentation is for authors who want to enhance
the functionality of Jupyter AI.

If you are interested in contributing to Jupyter AI,
please see our {doc}`contributor's guide </contributors/index>`.

## Pydantic compatibility

Jupyter AI internally uses **Pydantic v1** and should work with either Pydantic
version 1 or version 2. For compatibility, developers using Pydantic version 2
should import classes using the `pydantic.v1` package. See the
[LangChain Pydantic migration plan](https://python.langchain.com/docs/guides/pydantic_compatibility)
for advice about how developers should use `v1` to avoid mixing v1 and v2
classes in their code.

If you build an application that depends on LangChain, you can import from
`langchain.pydantic_v1`, which exposes Pydantic v1 classes from both Pydantic v1 and v2.
