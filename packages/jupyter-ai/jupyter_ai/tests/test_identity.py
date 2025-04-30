import logging
from unittest.mock import Mock, patch

import pytest
from jupyter_ai.auth.identity import LocalIdentityProvider, create_initials
from jupyter_server.auth.identity import User


@pytest.fixture
def log():
    log = logging.getLogger()
    log.addHandler(logging.NullHandler())
    return log


@pytest.fixture
def handler():
    return Mock()


@patch("getpass.getuser")
def test_get_user_successful(getuser, log, handler):

    getuser.return_value = "johndoe"
    provider = LocalIdentityProvider(log=log)

    user = provider.get_user(handler)

    assert isinstance(user, User)
    assert user.username == "johndoe"
    assert user.name == "johndoe"
    assert user.initials == "JH"
    assert user.color is None


@pytest.mark.parametrize(
    "username,expected_initials",
    [
        ("johndoe", "JH"),
        ("alice", "LC"),
        ("xy", "XY"),
        ("a", "A"),
        ("SARAH", "SR"),
        ("john-smith", "JH"),
        ("john123", "JH"),
        ("", ""),
    ],
)
def test_create_initials(username, expected_initials):
    """Test various initials generation scenarios."""
    assert create_initials(username) == expected_initials.upper()
