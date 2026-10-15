from social.models import TeamStatus
from social.orm import Team
from tests.helpers import create_user


async def test_success(client, authenticated_user, db):
    other = await create_user(db)

    async with db() as session:
        team = Team(
            requester_id=other.id,
            addressee_id=authenticated_user.id,
            status=TeamStatus.PENDING,
        )
        session.add(team)
        await session.commit()
        team_id = team.id

    response = await client.post(
        "/social/team/accept",
        json={"team_id": str(team_id)},
    )

    assert response.status_code == 200

    async with db() as session:
        updated = await session.get(Team, team_id)
        assert updated is not None
        assert updated.status == TeamStatus.ACCEPTED
