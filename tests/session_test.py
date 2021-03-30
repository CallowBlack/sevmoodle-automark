import asyncio
from src.moodle_session import MoodleSession


async def main():
    tasks = [asyncio.create_task(test_1()), asyncio.create_task(test_2())]
    await asyncio.gather(*tasks)
    print("All tests was passed.")


async def test_1():
    session: MoodleSession = MoodleSession.get_session("hello")
    session.update_password("zero")
    assert not (session.is_logged_in()), "is_logged_in test without login failed"

    try:
        await session.login()
    except ValueError:
        print("incorrect login test passed")
    else:
        assert False, "incorrect login test failed"
    await session.close()


async def test_2():
    session = MoodleSession.get_session("00-010670")
    session.update_password("WDD7tves")

    # await session.login()
    # result = await session.is_logged_in()
    # assert result, "login with correct credentials failed"

    await session.update_calendar()
    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
