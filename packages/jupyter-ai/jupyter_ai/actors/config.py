import json
import os
from jupyter_ai.actors.base import ACTOR_TYPE, Logger
from jupyter_ai.models import GlobalConfig
import ray
from jupyter_core.paths import jupyter_data_dir


@ray.remote
class ConfigActor():
    """Provides model and embedding provider id along 
    with the credentials to authenticate providers.
    """

    def __init__(self, log: Logger):
        self.log = log
        self.save_dir = os.path.join(jupyter_data_dir(), 'jupyter_ai')
        self.save_path = os.path.join(self.save_dir, 'config.json')
        self.config = None
        self._load()

    def update(self, config: GlobalConfig, save_to_disk: bool = True):
        self._update_chat_provider(config)
        self._update_embeddings_provider(config)
        if save_to_disk:
            self._save()
        self.config = config
    
    def _update_chat_provider(self, config: GlobalConfig):
        actor = ray.get_actor(ACTOR_TYPE.CHAT_PROVIDER)
        handle = actor.update.remote(config)
        ray.get(handle)

    def _update_embeddings_provider(self, config: GlobalConfig):
        actor = ray.get_actor(ACTOR_TYPE.EMBEDDINGS_PROVIDER)
        handle = actor.update.remote(config)
        ray.get(handle)

    def _save(self, config: GlobalConfig):
        if not os.path.exists:
            os.makedirs(self.save_dir)
        
        with open(self.save_path, 'w') as f:
                f.write(json.dumps(config))

    def _load(self):
        if os.path.exists(self.save_path):
            with open(self.save_path, 'r', encoding='utf-8') as f:
                config = GlobalConfig(**json.loads(f.read()))
                self.update(config, False)

    def get_config(self):
        return self.config