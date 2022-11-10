import asyncio
import random
from argparse import ArgumentParser
from datetime import timezone

from faker import Faker
from faker.providers import date_time, internet, lorem, profile
from loguru import logger
from passlib.hash import argon2

from prisma import Prisma
from prisma.errors import PrismaError
from prisma.models import Follower, Post, PostComment, PostMedia, PostRating, PostReport, Tag, User

fake = Faker()
Faker.seed(0)
fake.add_provider(profile)
fake.add_provider(internet)
fake.add_provider(lorem)
fake.add_provider(date_time)
prisma = Prisma(auto_register=True)


async def hash_password(password: str) -> str:
    """Returns hash of the password."""
    logger.trace("Creating password hash.")
    return argon2.using(rounds=4).hash(password)


async def _clear_database() -> None:
    models = [User, Post, Tag, Follower, PostMedia, PostComment, PostRating, PostReport]
    for model in models:
        await model.prisma().delete_many()
    logger.info("Cleared the database")


async def _create_users(n: int = 20) -> list[User]:
    fake_profiles = []
    for _ in range(n):
        profile = fake.simple_profile()
        fake_profiles.append(
            {
                "username": profile["username"],
                "email": profile["mail"],
                "password": await hash_password("abcdefg"),
            }
        )
    await User.prisma().create_many(fake_profiles)
    logger.info(f"Created {n} users")
    users = await User.prisma().find_many()
    count = 0
    for _ in range(3 * n):
        try:
            u1, u2 = random.choices(users, k=2)
            await Follower.prisma().create(
                {"user": {"connect": {"id": u1.id}}, "follows": {"connect": {"id": u2.id}}}
            )
            count += 1
        except PrismaError as e:
            logger.warning(f"Follower not made; Error={e}")
    logger.info(f"Attempted making {3 * n} followers; made {count}")
    return users


async def _create_tags() -> list[str]:
    tags = [
        "pubg",
        "cod",
        "amongus",
        "valorant",
        "fortnite",
        "forza",
        "godofwar",
        "witcher",
        "rust",
        "minecraft",
        "fifa",
        "f1",
    ]
    await Tag.prisma().create_many([{"tag_name": i} for i in tags])
    logger.info(f"Created {len(tags)} tags")
    return tags


async def _create_posts(users: list[User], tags: list[str], n: int = 50) -> None:
    for i in range(1, n + 1):
        author = random.choice(users)
        p = await Post.prisma().create(
            {
                "title": fake.text(50),
                "text_content": fake.paragraph(),
                "created_at": fake.date_time(tzinfo=timezone.utc),
                "media": {"create": {"object_url": fake.image_url()}},
                "author": {"connect": {"id": author.id}},
                "tags": {"connect": {"tag_name": random.choice(tags)}},
            }
        )
        logger.debug(f"Creating {n//2} comments and ratings for post number {i}")
        users_copy = users.copy()
        for _ in range(n // 2):
            random_user = random.choice(users_copy)
            users_copy.remove(random_user)
            await _create_comment(p, random_user)
            await _create_rating(p, random_user)
    logger.info(f"Created {n} posts, with each post having {n//2} comments and ratings.")


async def _create_comment(p: Post, author: User) -> None:
    content = fake.sentence()
    await PostComment.prisma().create(
        {
            "content": content,
            "author": {"connect": {"id": author.id}},
            "post": {"connect": {"id": p.id}},
        }
    )


async def _create_rating(p: Post, author: User) -> None:
    rating = random.randint(0, 5)
    try:
        await PostRating.prisma().create(
            {
                "value": rating,
                "post": {"connect": {"id": p.id}},
                "author": {"connect": {"id": author.id}},
            }
        )
    except PrismaError as e:
        logger.warning(f"Could not make rating: {e}")


async def _main(user_count: int, post_count: int) -> None:
    logger.info("[Step 0]: Connecting to the database")
    await prisma.connect()
    logger.info("[Step 1]: Clearing database")
    await _clear_database()
    logger.info("[Step 2]: Creating users")
    users = await _create_users(user_count)
    logger.info("[Step 3]: Creating tags")
    tags = await _create_tags()
    logger.info(f"[Step 4]: Creating {post_count} posts")
    await _create_posts(users, tags, post_count)
    logger.info("Dummy data created")
    await prisma.disconnect()


if __name__ == "__main__":
    parser = ArgumentParser(prog="dummydatagen")
    parser.add_argument("--users", type=int, default=10, help="Number of users to create")
    parser.add_argument("--posts", type=int, default=30, help="Number of posts to create")
    args = parser.parse_args()
    if (args.posts // 2) > args.user:
        logger.warning(f"User count {args.users} less than half of post count {args.posts // 2}")
        logger.warning(f"Setting user count to {args.posts // 2}")
        args.users = args.posts // 2
    asyncio.run(_main(args.users, args.posts))
