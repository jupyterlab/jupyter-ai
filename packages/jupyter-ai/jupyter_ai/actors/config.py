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
            self._save(config)
        self.config = config
    
    def _update_chat_provider(self, config: GlobalConfig):
        if not config.model_provider_id:
            return

        actor = ray.get_actor(ACTOR_TYPE.CHAT_PROVIDER)
        ray.get(actor.update.remote(config))

    def _update_embeddings_provider(self, config: GlobalConfig):
        if not config.embeddings_provider_id:
            return

        actor = ray.get_actor(ACTOR_TYPE.EMBEDDINGS_PROVIDER)
        ray.get(actor.update.remote(config))

    def _save(self, config: GlobalConfig):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        with open(self.save_path, 'w') as f:
            f.write(config.json())

    def _load(self):
        if os.path.exists(self.save_path):
            with open(self.save_path, 'r', encoding='utf-8') as f:
                config = GlobalConfig(**json.loads(f.read()))
                self.update(config, False)
            return
        
        # otherwise, create a new empty config file
        self.update(GlobalConfig(), True)

    def get_config(self):
        return self.config