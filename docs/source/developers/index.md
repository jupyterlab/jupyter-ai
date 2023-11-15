# Developers

The developer documentation is for authors who want to enhance
the functionality of Jupyter AI.

If you are interested in contributing to Jupyter AI,
please see our {doc}`contributor's guide </contributors/index>`.

## Pydantic compatibility

Jupyter AI is fully compatible with Python environments using Pydantic v1
or Pydantic v2. Jupyter AI imports Pydantic classes from the
`langchain.pydantic_v1` module. Developers should do the same when they extend
Jupyter AI classes.

For more details about using `langchain.pydantic_v1` in an environment with
Pydantic v2 installed, see the
[LangChain documentation on Pydantic compatibility](https://python.langchain.com/docs/guides/pydantic_compatibility).
