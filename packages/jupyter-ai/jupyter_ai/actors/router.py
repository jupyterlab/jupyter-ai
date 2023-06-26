import ray
from jupyter_ai.actors.base import ACTOR_TYPE, COMMANDS, BaseActor, Logger
from ray.util.queue import Queue


@ray.remote
class Router(BaseActor):
    def _process_message(self, message):
        # assign default actor
        default = ray.get_actor(ACTOR_TYPE.DEFAULT)

        if message.body.startswith("/"):
            command = message.body.split(" ", 1)[0]
            if command in COMMANDS.keys():
                actor = ray.get_actor(COMMANDS[command].value)
                actor.process_message.remote(message)
            if command == "/clear":
                actor = ray.get_actor(ACTOR_TYPE.DEFAULT)
                actor.clear_memory.remote()
        else:
            default.process_message.remote(message)
