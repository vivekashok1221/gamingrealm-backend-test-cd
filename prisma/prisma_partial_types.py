# Add instructions to create partial types here
# https://prisma-client-py.readthedocs.io/en/stable/getting_started/partial-types/

from prisma.models import User

User.create_partial("UserProfile", include={"id", "username", "email", "created_at"})
