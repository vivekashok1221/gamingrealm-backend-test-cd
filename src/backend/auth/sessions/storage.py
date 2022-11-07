from abc import ABCMeta, abstractmethod
from uuid import UUID

from .. import AuthError
from .session import Session


class SessionDoesNotExistError(AuthError):
    """The specified session did not exist in the storage backend."""


class AbstractSessionStorage(metaclass=ABCMeta):
    """An abstract session storage.

    Classes that implement this ABC will be used to store user session details.
    """

    @abstractmethod
    async def get_session(self, id: UUID) -> Session | None:
        """Gets a session from the storage. Returns None if the session doesn't exist.

        Args:
            id: The session ID to get
        Returns:
            Session: The session data
            None: The session didn't exist.
        """
        ...

    @abstractmethod
    async def create_session(self, user_id: UUID) -> Session:
        """Creates a session for the provided user and stores it.

        Args:
            user_id: The user to create the session for.
        Returns:
            The session that was created.
        """
        ...

    @abstractmethod
    async def delete_session(self, id: UUID) -> None:
        """Deletes a session from the storage.

        Args:
            id: The session ID to delete
        Raises:
            SessionDoesNotExistError: The specified session does not exist.
        """
        ...


class InMemorySessionStorage(AbstractSessionStorage):  # noqa: D101
    def __init__(self) -> None:
        self._sessions = dict[Session.id, Session]()
        self._logged_in_users = dict[Session.user_id, Session.id]()

    async def get_session(self, id: UUID) -> Session | None:  # noqa: D102
        return self._sessions.get(id)

    async def create_session(self, user_id: UUID) -> Session:  # noqa: D102
        if user_id in self._logged_in_users:
            session_id = self._logged_in_users[user_id]
            del self._sessions[session_id]
        session = Session(user_id=user_id)
        self._sessions[session.id] = session
        self._logged_in_users[user_id] = session.id
        return session

    async def delete_session(self, id: UUID) -> None:  # noqa: D102
        try:
            session = self._sessions.pop(id)
        except KeyError as e:
            raise SessionDoesNotExistError(f"Session {id} does not exist.") from e
        else:
            self._logged_in_users.pop(session.user_id)
