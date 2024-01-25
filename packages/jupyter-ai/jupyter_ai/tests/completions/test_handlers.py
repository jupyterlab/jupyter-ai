import json
from types import SimpleNamespace

from jupyter_ai.completions.handlers.default import DefaultInlineCompletionHandler
from jupyter_ai.completions.models import InlineCompletionRequest
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

    def __init__(self, **kwargs):
        kwargs["responses"] = ["Test response"]
        super().__init__(**kwargs)


class MockCompletionHandler(DefaultInlineCompletionHandler):
    def __init__(self):
        self.request = HTTPServerRequest()
        self.application = Application()
        self.messages = []
        self.tasks = []
        self.settings["jai_config_manager"] = SimpleNamespace(
            lm_provider=MockProvider, lm_provider_params={"model_id": "model"}
        )
        self.settings["jai_event_loop"] = SimpleNamespace(
            create_task=lambda x: self.tasks.append(x)
        )
        self.settings["model_parameters"] = {}
        self.llm_params = {}
        self.create_llm_chain(MockProvider, {"model_id": "model"})

    def write_message(self, message: str) -> None:  # type: ignore
        self.messages.append(message)

    async def handle_exc(self, e: Exception, _request: InlineCompletionRequest):
        # raise all exceptions during testing rather
        raise e


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


async def test_handle_stream_request(inline_handler):
    inline_handler.llm_chain = FakeListLLM(responses=["test"])
    dummy_request = InlineCompletionRequest(
        number=1, prefix="", suffix="", mime="", stream=True
    )
    await inline_handler.handle_stream_request(dummy_request)

    # should write three replies
    assert len(inline_handler.messages) == 3

    # first reply should be empty to start the stream
    first = inline_handler.messages[0].list.items[0]
    assert first.insertText == ""
    assert first.isIncomplete == True

    # second reply should be a chunk containing the token
    second = inline_handler.messages[1]
    assert second.type == "stream"
    assert second.response.insertText == "Test response"
    assert second.done == False

    # third reply should be a closing chunk
    third = inline_handler.messages[2]
    assert third.type == "stream"
    assert third.response.insertText == "Test response"
    assert third.done == True
