from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient

from prisma.models import User
from src.backend.models import UserInLogin, UserInSignup
from src.backend.routers.user import hash_password

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="package")
@pytest.mark.anyio
async def user1() -> AsyncGenerator[User, None]:
    user = await User.prisma().create(
        {
            "username": "johndoe",
            "email": "johndoe@company.org",
            "password": await hash_password("password12"),
        }
    )
    yield user
    await User.prisma().delete(where={"id": user.id})


@pytest.fixture(scope="package")
@pytest.mark.anyio
async def user2() -> AsyncGenerator[User, None]:
    user = await User.prisma().create(
        {
            "username": "genericuser",
            "email": "user@megacorp.org",
            "password": await hash_password("supersafe!"),
        }
    )
    yield user
    await User.prisma().delete(where={"id": user.id})


@pytest.fixture(scope="package")
@pytest.mark.anyio
async def logged_in_user(
    client: AsyncClient, user1: User
) -> AsyncGenerator[tuple[User, str], None]:
    data = UserInLogin(username=user1.username, password="password12")
    res = await client.post("/user/login", data=data.dict())
    response_data = res.json()
    yield user1, response_data["session_id"]
    await client.post("/user/logout", headers={"session-id": response_data["session_id"]})


async def test_new_user_sign_up(client: AsyncClient):
    # we can safely just forget about this user - none of the other tests should depend on it
    # otherwise we'd need to do cleanup here (call signout) but that's for another test
    data = UserInSignup(username="newusuer", password="i<3blockchain", email="foo@bar.com")
    # the email field in the UserInSignup is type hinted as EmailStr as it is a pydantic validator
    # so passing in a string here is making pyright complain.
    res = await client.post("/user/signup", data=data.dict())
    assert res.status_code == 200
    response_data = res.json()
    assert response_data.get("session_id")


async def test_existing_user_cant_signup(client: AsyncClient, user1: User):
    data = UserInSignup(username=user1.username, password="password12", email=user1.email)
    res = await client.post("/user/signup", data=data.dict())
    assert res.status_code == 409


async def test_existing_user_can_login(client: AsyncClient, user1: User):
    data = UserInLogin(username=user1.username, password="password12")
    res = await client.post("/user/login", data=data.dict())
    assert res.status_code == 200
    response_data = res.json()
    assert response_data.get("session_id")
    await client.post("/user/logout", headers={"session-id": response_data["session_id"]})


async def test_non_existent_user_cant_login(client: AsyncClient):
    data = UserInLogin(username="nonexistent", password="bruhwhat?")
    res = await client.post("/user/login", data=data.dict())
    assert res.status_code == 404


async def test_get_non_existent_user(client: AsyncClient):
    res = await client.get("/user/notavaliduserid")
    assert res.status_code == 404


async def test_get_user(client: AsyncClient, user1: User):
    res = await client.get(f"/user/{user1.id}")
    assert res.status_code == 200
    data = res.json()
    assert data.get("id") == user1.id
    assert data.get("is_following") is None


async def test_get_user_while_logged_in(
    client: AsyncClient, logged_in_user: tuple[User, str], user2: User
):
    # get user2 data while logged in as user1
    # here the is_following field should be set to False
    user, session = logged_in_user
    res = await client.get(f"/user/{user2.id}", headers={"session-id": session})
    assert res.status_code == 200
    assert res.json()["is_following"] is False
