import getpass

from jupyter_server.auth.identity import IdentityProvider, User


def create_initials(username):
    """Creates initials combining first 2 consonants"""

    username = username.lower()

    # Default: return first two unique consonants
    consonants = [c for c in username if c in "bcdfghjklmnpqrstvwxyz"]
    if len(consonants) >= 2:
        return (consonants[0] + consonants[1]).upper()

    # Fallback: first two characters
    return username[:2].upper()


class LocalIdentityProvider(IdentityProvider):

    def get_user(self, handler):
        username = getpass.getuser()
        user = User(
            username=username,
            name=username,
            initials=create_initials(username),
            color="#039BE5",
        )
        return user
