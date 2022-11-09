from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class Session:
    """A user session.

    Whenever a user logs in successfully, a Session object
    is created and stored in a session storage backend.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID
    # default factory for a timezone-aware datetime
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
