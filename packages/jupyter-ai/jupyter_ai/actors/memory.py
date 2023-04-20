from typing import Dict, Any, List

import ray
from langchain.schema import BaseMemory
from pydantic import PrivateAttr

from jupyter_ai.actors.base import Logger

@ray.remote
class MemoryActor(object):
    """Turns any LangChain memory into a Ray actor.
    
    The resulting actor can be used as LangChain memory in chains
    running in different actors by using RemoteMemory (below).
    """
    
    def __init__(self, log: Logger, memory: BaseMemory):
        self.memory = memory
        self.log = log
    
    def get_chat_memory(self):
        return self.memory.chat_memory
    
    def get_output_key(self):
        return self.memory.output_key
    
    def get_input_key(self):
        return self.memory.input_key

    def get_return_messages(self):
        return self.memory.return_messages
    
    def get_memory_variables(self):
        return self.memory.memory_variables

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        return self.memory.save_context(inputs, outputs)
    
    def clear(self):
        return self.memory.clear()
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return self.memory.load_memory_variables(inputs)
    

    

class RemoteMemory(BaseMemory):
    """Wraps a MemoryActor into a LangChain memory class.
    
    This enables you to use a single distributed memory across multiple
    Ray actors running different chains.
    """
    
    actor_name: str
    _actor: Any = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._actor = ray.get_actor(self.actor_name)
        
    @property
    def memory_variables(self) -> List[str]:
        o = self._actor.get_memory_variables.remote()
        return ray.get(o)
    
    @property
    def output_key(self):
        o = self._actor.get_output_key.remote()
        return ray.get(o)
    
    @property
    def input_key(self):
        o = self._actor.get_input_key.remote()
        return ray.get(o)
    
    @property
    def return_messages(self):
        o = self._actor.get_return_messages.remote()
        return ray.get(o)
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        o = self._actor.save_context.remote(inputs, outputs)
        return ray.get(o)
    
    def clear(self):
        self._actor.clear.remote()
        
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        o = self._actor.load_memory_variables.remote(inputs)
        return ray.get(o)