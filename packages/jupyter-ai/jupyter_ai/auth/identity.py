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
    """IdentityProvider that determines username from system user."""

    def get_user(self, handler):
        try:
            username = getpass.getuser()
            user = User(
                username=username,
                name=username,
                initials=create_initials(username),
                color=None,
            )
            return user
        except OSError:
            self.log.debug(
                "Could not determine username from system. Falling back to anonymous"
                f"user."
            )
            return self._get_user(handler)
