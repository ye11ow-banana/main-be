from social.orm import Team
from tests.helpers import create_user


async def test_success(client, authenticated_user, db):
    other = await create_user(db)

    response = await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    assert response.status_code == 200

    data = response.json()["data"]
    assert data["requester_id"] == str(authenticated_user.id)
    assert data["addressee_id"] == str(other.id)


async def test_self_request_fails(client, authenticated_user, db):
    response = await client.post(
        "/social/team/request",
        json={"user_id": str(authenticated_user.id)},
    )

    assert response.status_code == 400


async def test_duplicate_request_fails(client, authenticated_user, db):
    other = await create_user(db)

    await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    response = await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    assert response.status_code == 400


async def test_reverse_duplicate_request_fails(client, authenticated_user, db):
    other = await create_user(db)

    await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    response = await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    assert response.status_code == 400


async def test_request_persists_in_db(client, authenticated_user, db):
    other = await create_user(db)

    response = await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    assert response.status_code == 200

    async with db() as session:
        result = await session.execute(
            Team.__table__.select().where(
                Team.requester_id == authenticated_user.id,
                Team.addressee_id == other.id,
            )
        )
        row = result.first()
        assert row is not None


async def test_duplicate_request_does_not_create_second_row(client, authenticated_user, db):
    other = await create_user(db)

    await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    response = await client.post(
        "/social/team/request",
        json={"user_id": str(other.id)},
    )

    assert response.status_code == 400

    async with db() as session:
        result = await session.execute(
            Team.__table__.select().where(
                Team.requester_id == authenticated_user.id,
                Team.addressee_id == other.id,
            )
        )
        rows = result.fetchall()
        assert len(rows) == 1