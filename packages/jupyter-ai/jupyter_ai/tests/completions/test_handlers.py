import json
from types import SimpleNamespace
from typing import Union

import pytest
from jupyter_ai.completions.handlers.default import DefaultInlineCompletionHandler
from jupyter_ai.completions.models import (
    InlineCompletionReply,
    InlineCompletionRequest,
    InlineCompletionStreamChunk,
)
from jupyter_ai_magics import BaseProvider
from langchain_community.llms import FakeListLLM
from pytest import fixture
from tornado.httputil import HTTPServerRequest
from tornado.web import Application


class MockProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model"]
    raise_exc: bool = False

    def __init__(self, **kwargs):
        if "responses" not in kwargs:
            kwargs["responses"] = ["Test response"]
        super().__init__(**kwargs)

    async def _acall(self, *args, **kwargs):
        if self.raise_exc:
            raise Exception("Test exception")
        else:
            return super()._call(*args, **kwargs)


class MockCompletionHandler(DefaultInlineCompletionHandler):
    def __init__(self, lm_provider=None, lm_provider_params=None, raise_exc=False):
        self.request = HTTPServerRequest()
        self.application = Application()
        self.messages = []
        self.tasks = []
        self.settings["jai_config_manager"] = SimpleNamespace(
            completions_lm_provider=lm_provider or MockProvider,
            completions_lm_provider_params=lm_provider_params or {"model_id": "model"},
        )
        self.settings["jai_event_loop"] = SimpleNamespace(
            create_task=lambda x: self.tasks.append(x)
        )
        self.settings["model_parameters"] = {}
        self._llm_params = {}
        self._llm = None

    def reply(
        self, message: Union[InlineCompletionReply, InlineCompletionStreamChunk]
    ) -> None:
        self.messages.append(message)


@fixture
def inline_handler() -> MockCompletionHandler:
    return MockCompletionHandler()


async def test_on_message(inline_handler):
    request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=False
    )
    # Test end to end, without checking details of the replies,
    # which are tested in appropriate method unit tests.
    await inline_handler.on_message(json.dumps(dict(request)))
    assert len(inline_handler.tasks) == 1
    await inline_handler.tasks[0]
    assert len(inline_handler.messages) == 1


async def test_on_message_stream(inline_handler):
    stream_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=True
    )
    # Test end to end, without checking details of the replies,
    # which are tested in appropriate method unit tests.
    await inline_handler.on_message(json.dumps(dict(stream_request)))
    assert len(inline_handler.tasks) == 1
    await inline_handler.tasks[0]
    assert len(inline_handler.messages) == 3


async def test_handle_request(inline_handler):
    dummy_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=False
    )
    await inline_handler.handle_request(dummy_request)
    # should write a single reply
    assert len(inline_handler.messages) == 1
    # reply should contain a single suggestion
    suggestions = inline_handler.messages[0].list.items
    assert len(suggestions) == 1
    # the suggestion should include insert text from LLM
    assert suggestions[0].insertText == "Test response"


expected_suggestions_cases = [
    ("```python\nTest python code\n```", "Test python code"),
    ("```\ntest\n```\n   \n", "test"),
    ("```hello```world```", "hello```world"),
    (" ```\nprint(test)\n```", "print(test)"),
    ("``` \nprint(test)\n```", "print(test)"),
]


@pytest.mark.parametrize(
    "response,expected_suggestion",
    expected_suggestions_cases,
)
async def test_handle_request_with_spurious_fragments(response, expected_suggestion):
    inline_handler = MockCompletionHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "responses": [response],
        },
    )
    dummy_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=False
    )

    await inline_handler.handle_request(dummy_request)
    # should write a single reply
    assert len(inline_handler.messages) == 1
    # reply should contain a single suggestion
    suggestions = inline_handler.messages[0].list.items
    assert len(suggestions) == 1
    # the suggestion should include insert text from LLM without spurious fragments
    assert suggestions[0].insertText == expected_suggestion


@pytest.mark.parametrize(
    "response,expected_suggestion",
    expected_suggestions_cases,
)
async def test_handle_request_with_spurious_fragments_stream(
    response, expected_suggestion
):
    inline_handler = MockCompletionHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "responses": [response],
        },
    )
    dummy_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=True
    )

    await inline_handler.handle_stream_request(dummy_request)
    assert len(inline_handler.messages) == 3
    # the streamed fragment should not include spurious fragments
    assert inline_handler.messages[1].response.insertText == expected_suggestion
    # the final state should not include spurious fragments either
    assert inline_handler.messages[2].response.insertText == expected_suggestion


async def test_handle_stream_request():
    inline_handler = MockCompletionHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "responses": ["test"],
        },
    )
    dummy_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=True
    )
    await inline_handler.handle_stream_request(dummy_request)

    # should write three replies
    assert len(inline_handler.messages) == 3

    # first reply should be empty to start the stream
    first = inline_handler.messages[0].list.items[0]
    assert first.insertText == ""
    assert first.isIncomplete is True

    # second reply should be a chunk containing the token
    second = inline_handler.messages[1]
    assert second.type == "stream"
    assert second.response.insertText == "test"
    assert second.done is False

    # third reply should be a closing chunk
    third = inline_handler.messages[2]
    assert third.type == "stream"
    assert third.response.insertText == "test"
    assert third.done is True


async def test_handle_request_with_error(inline_handler):
    inline_handler = MockCompletionHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "responses": ["test"],
            "raise_exc": True,
        },
    )
    dummy_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=True
    )
    await inline_handler.on_message(json.dumps(dict(dummy_request)))
    await inline_handler.tasks[0]
    error = inline_handler.messages[-1].model_dump().get("error", None)
    assert error is not None
