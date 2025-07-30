from __future__ import annotations
from traitlets.config import LoggingConfigurable
from typing import TYPE_CHECKING
from dotenv import load_dotenv, dotenv_values
from io import StringIO
import asyncio
from tornado.web import HTTPError
import os

from .secrets_utils import build_updated_dotenv
from .secrets_types import SecretsList

if TYPE_CHECKING:
    from typing import Any, Optional
    import logging
    import datetime
    from ..extension import AiExtension
    from jupyter_server.services.contents.filemanager import AsyncFileContentsManager

class EnvSecretsManager(LoggingConfigurable):

    parent: AiExtension
    """
    The parent `AiExtension` class.

    NOTE: This attribute is automatically set by the `LoggingConfigurable`
    parent class. This annotation exists only to help type checkers like `mypy`.
    """

    log: logging.Logger
    """
    The logger used by by this instance.

    NOTE: This attribute is automatically set by the `LoggingConfigurable`
    parent class. This annotation exists only to help type checkers like `mypy`.
    """

    _last_modified: Optional[datetime.datetime]
    """
    The 'last modified' timestamp on the '.env' file retrieved in the previous
    tick of the `_watch_dotenv()` background task.
    """

    _initial_env: dict[str, str]
    """
    Dictionary containing the initial environment variables passed to this
    process. Set to `dict(os.environ)` exactly once on init.

    This attribute should not be set more than once, since secrets loaded from
    the `.env` file are added to `os.environ` after this class initializes.
    """

    _dotenv_env: dict[str, str]
    """
    Dictionary containing the environment variables defined in the `.env` file.
    If no `.env` file exists, this will be an empty dictionary. This attribute
    is continuously updated via the `_watch_dotenv()` background task.
    """

    _dotenv_lock: asyncio.Lock
    """
    Lock which must be held while reading or writing to the `.env` file from the
    `ContentsManager`.
    """

    @property
    def contents_manager(self) -> AsyncFileContentsManager:
        return self.parent.serverapp.contents_manager
    
    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        return self.parent.event_loop

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set instance attributes
        self._last_modified = None
        self._initial_env = dict(os.environ)
        self._dotenv_env = {}
        self._dotenv_lock = asyncio.Lock()

        # Start `_watch_dotenv()` task to automatically update the environment
        # variables when `.env` is modified
        self._watch_dotenv_task = self.event_loop.create_task(self._watch_dotenv())
    

    async def _watch_dotenv(self) -> None:
        """
        Watches the `.env` file and automatically responds to changes.
        """
        while True:
            await asyncio.sleep(1)

            # Fetch file content and its last modified timestamp
            try:
                async with self._dotenv_lock:
                    dotenv_file = await self.contents_manager.get(".env", content=True)
                dotenv_content = dotenv_file.get("content")
                assert isinstance(dotenv_content, str)
            except HTTPError as e:
                # Continue if file does not exist, otherwise re-raise
                if e.status_code == 404:
                    self._handle_dotenv_notfound()
                    continue
                raise e
            except Exception as e:
                self.log.exception("Unknown exception in `_watch_dotenv()`:")
                continue

            # Continue if the `.env` file was already processed and its content
            # is unchanged.
            if self._last_modified == dotenv_file['last_modified']:
                continue

            # When this line is reached, the .env file needs to be applied.
            # Log a statement accordingly, ensure the new `.env` file is listed
            # in `.gitignore`, and store the latest last modified timestamp.
            if self._last_modified:
                # Statement when .env file was modified:
                self.log.info("Detected changes to the '.env' file. Re-applying '.env' to the environment...")
            else:
                # Statement when the .env file was just created, or when this is
                # the first iteration and a .env file already exists:
                self.log.info("Detected '.env' file at the workspace root. Applying '.env' to the environment...")
                self.event_loop.create_task(self._ensure_dotenv_gitignored())
            self._last_modified = dotenv_file['last_modified']

            # Apply the latest `.env` file to the environment.
            # See `self._apply_dotenv()` for more info.
            self._apply_dotenv(dotenv_content)
    

    def _apply_dotenv(self, content: str) -> None:
        """
        Applies a `.env` file to the environment given its content. This method:

        1. Resets any variables removed from the `.env` file. See
           `self._reset_envvars()` for more info.

        2. Stores the parsed `.env` file as a dictionary in `self._dotenv_env`.

        3. Sets the environment variables in `os.environ` as defined in the
           `.env` file.
        """
        # Parse the latest `.env` file and store it in `self._dotenv_env`,
        # tracking deleted environment variables in `deleted_envvars`.
        new_dotenv_env = dotenv_values(stream=StringIO(content))
        new_dotenv_env = {
            k: v for k, v in new_dotenv_env.items() if v != None
        }
        deleted_envvars = [k for k in self._dotenv_env if k not in new_dotenv_env]
        self._dotenv_env = new_dotenv_env

        # Apply the new `.env` file to the environment and reset all
        # environment variables in `deleted_envvars`.
        if deleted_envvars:
            self._reset_envvars(deleted_envvars)
            self.log.info(
                f"Removed {len(deleted_envvars)} variables from the environment as they were removed from '.env'."
            )
        load_dotenv(stream=StringIO(content), override=True)
        self.log.info("Applied '.env' to the environment.")

    

    async def _ensure_dotenv_gitignored(self) -> bool:
        """
        Ensures the `.env` file is listed in the `.gitignore` file at the
        workspace root, creating/updating the `.gitignore` file to list `.env`
        if needed.

        This method is called by the `_watch_dotenv()` background task either on
        the first iteration when the `.env` file already exists, or when the
        `.env` file was created on a subsequent iteration.
        """
        # Fetch `.gitignore` file.
        gitignore_file: dict[str, Any] | None = None
        try:
            gitignore_file = await self.contents_manager.get(".gitignore", content=True)
        except HTTPError as e:
            # Continue if file does not exist, otherwise re-raise
            if e.status_code == 404:
                pass
            raise e
        except Exception as e:
            self.log.exception("Unknown exception raised when fetching `.gitignore`:")
            pass
            
        # Return early if the `.gitignore` file exists and already lists `.env`.
        old_content: str = (gitignore_file or {}).get("content", "")
        if ".env\n" in old_content:
            return

        # Otherwise, log something and create/update the `.gitignore` file to
        # list `.env`.
        self.log.info("Updating `.gitignore` file to include `.env`...")
        new_lines = "# Ignore secrets in '.env'\n.env\n"
        new_content = old_content + "\n" + new_lines if old_content else new_lines
        try:
            gitignore_file = await self.contents_manager.save({
                    "type": "file",
                    "format": "text",
                    "mimetype": "text/plain",
                    "content": new_content
                },
                ".gitignore"
            )
        except Exception as e:
            self.log.exception("Unknown exception raised when updating `.gitignore`:")
            pass
        self.log.info("Updated `.gitignore` file to include `.env`.")
        

    def _reset_envvars(self, names: list[str]) -> None:
        """
        Resets each environment variable in the given list. Each variable is
        restored to its initial value in `self._initial_env` if present, and
        deleted from `os.environ` otherwise.
        """
        for ev_name in names:
            if ev_name in self._initial_env:
                os.environ[ev_name] = self._initial_env.get(ev_name)
            else:
                del os.environ[ev_name]
    

    def _handle_dotenv_notfound(self) -> None:
        """
        Method called by the `_watch_dotenv()` task when the `.env` file is
        not found.
        """
        if self._last_modified:
            self._last_modified = None
        if self._dotenv_env:
            self._reset_envvars(list(self._dotenv_env.keys()))
            self._dotenv_env = {}


    def list_secrets(self) -> SecretsList:
        """
        Lists the names of each environment variable from the workspace `.env`
        file and the environment variables passed to the Python process. Notes:

        1. For envvars from the Python process (not set in `.env`), only
        environment variables whose names contain "KEY" or "TOKEN" or "SECRET"
        are included.

        2. Each envvar listed in `.env` is included in the returned list.
        """
        dotenv_secrets_names = set()
        process_secrets_names = set()

        # Add secrets from the initial environment
        for name in self._initial_env.keys():
            if "KEY" in name or "TOKEN" in name or "SECRET" in name:
                process_secrets_names.add(name)
        
        # Add secrets from .env, if any
        for name in self._dotenv_env:
            dotenv_secrets_names.add(name)
        
        return SecretsList(
            editable_secrets=sorted(list(dotenv_secrets_names)),
            static_secrets=sorted(list(process_secrets_names))
        )


    async def update_secrets(
            self,
            updated_secrets: dict[str, str | None],
        ) -> None:
        """
        Accepts a dictionary of secrets to update, adds/updates/deletes them
        from `.env` accordingly, and applies the updated `.env` file to the
        environment. Notes:

        - A new `.env` file is created if it does not exist.

        - If the value of a secret in `updated_secrets` is `None`, then the
        secret is deleted from `.env`.

        - Otherwise, the secret is added/updated in `.env`.

        - A best effort is made at preserving the formatting in the `.env`
        file. However, inline comments following a environment variable
        definition on the same line will be deleted.
        """
        # Return early if passed an empty dictionary
        if not updated_secrets:
            return

        # Hold the lock during the entire duration of the update
        async with self._dotenv_lock:
            # Fetch `.env` file content, storing its raw content in
            # `dotenv_content` and its parsed value as a dict in `dotenv_env`.
            dotenv_content: str = ""
            try:
                dotenv_file = await self.contents_manager.get(".env", content=True)
                if "content" in dotenv_file:
                    dotenv_content = dotenv_file["content"]
                    assert isinstance(dotenv_content, str)
            except HTTPError as e:
                # Continue if file does not exist, otherwise re-raise
                if e.status_code == 404:
                    pass
                raise e
            except Exception as e:
                self.log.exception("Unknown exception raised when reading `.env` in response to an update:")
            
            # Build the new `.env` file using these variables.
            # See `build_updated_dotenv()` for more info on how this is done.
            new_dotenv_content = build_updated_dotenv(dotenv_content, updated_secrets)

            # Return early if no changes are needed in `.env`.
            if new_dotenv_content is None:
                return
            
            # Save new content
            try:
                dotenv_file = await self.contents_manager.save({
                    "type": "file",
                    "format": "text",
                    "mimetype": "text/plain",
                    "content": new_dotenv_content
                }, ".env")
                last_modified = dotenv_file.get('last_modified')
                assert isinstance(last_modified, datetime.datetime)
            except Exception as e:
                self.log.exception("Unknown exception raised when updating `.env`:")

            # Update last modified timestamp and apply the new environment.
            self._last_modified = last_modified
            # This automatically sets `self._dotenv_env`.
            self._apply_dotenv(new_dotenv_content)
    

    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Returns the value of a secret given its name. The returned secret must
        NEVER be shared with frontend clients!
        """
        # TODO
        pass

    
    def stop(self) -> None:
        """
        Stops this instance and any background tasks spawned by this instance.
        This method should be called if and only if the server is shutting down.
        """
        self._watch_dotenv_task.cancel()
