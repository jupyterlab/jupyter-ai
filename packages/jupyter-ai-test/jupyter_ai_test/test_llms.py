import time
from typing import Any, Iterator, List, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs.generation import GenerationChunk


class TestLLM(LLM):
    model_id: str = "test"

    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        time.sleep(3)
        return f"Hello! This is a dummy response from a test LLM."


class TestLLMWithStreaming(LLM):
    model_id: str = "test"

    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        time.sleep(3)
        return f"Hello! This is a dummy response from a test LLM."

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        time.sleep(5)
        yield GenerationChunk(
            text="Hello! This is a dummy response from a test LLM. I will now count from 1 to 100.\n\n"
        )
        for i in range(1, 101):
            time.sleep(0.5)
            yield GenerationChunk(text=f"{i}, ")
