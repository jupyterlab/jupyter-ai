# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest
from jupyter_ai_magics.utils import get_lm_providers

KNOWN_LM_A = "openai"
KNOWN_LM_B = "huggingface_hub"


@pytest.mark.parametrize(
    "restrictions",
    [
        {"allowed_providers": None, "blocked_providers": None},
        {"allowed_providers": [], "blocked_providers": []},
        {"allowed_providers": [], "blocked_providers": [KNOWN_LM_B]},
        {"allowed_providers": [KNOWN_LM_A], "blocked_providers": []},
    ],
)
def test_get_lm_providers_not_restricted(restrictions):
    a_not_restricted = get_lm_providers(None, restrictions)
    assert KNOWN_LM_A in a_not_restricted


@pytest.mark.parametrize(
    "restrictions",
    [
        {"allowed_providers": [], "blocked_providers": [KNOWN_LM_A]},
        {"allowed_providers": [KNOWN_LM_B], "blocked_providers": []},
    ],
)
def test_get_lm_providers_restricted(restrictions):
    a_not_restricted = get_lm_providers(None, restrictions)
    assert KNOWN_LM_A not in a_not_restricted
