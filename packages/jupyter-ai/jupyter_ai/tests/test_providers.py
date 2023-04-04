from pydantic import ValidationError

from jupyter_ai.providers import AI21Provider

def test_model_id_required():
    try:
        AI21Provider(ai21_api_key="asdf")
        assert False
    except ValidationError as e:
        assert "1 validation error" in str(e)
        assert "model_id" in str(e)
