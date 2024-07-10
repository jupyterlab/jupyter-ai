import os
import stat
from unittest import mock

from jupyter_ai.chat_handlers import learn


class MockLearnHandler(learn.LearnChatHandler):
    def __init__(self):
        pass


def test_learn_index_permissions(tmp_path):
    test_dir = tmp_path / "test"
    with mock.patch.object(learn, "INDEX_SAVE_DIR", new=test_dir):
        handler = MockLearnHandler()
        handler._ensure_dirs()
        mode = os.stat(test_dir).st_mode
        assert stat.filemode(mode) == "drwx------"


# TODO
# import json


# async def test_get_example(jp_fetch):
#     # When
#     response = await jp_fetch("jupyter-ai", "get_example")

#     # Then
#     assert response.code == 200
#     payload = json.loads(response.body)
#     assert payload == {
#         "data": "This is /jupyter-ai/get_example endpoint!"
#     }
