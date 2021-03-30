import asyncio

from aiohttp import ClientOSError

import src.data_manager as data_manager
from src.moodle_session import MoodleSession, LoginError


async def session_loop():
    sessions = []
    while len(sessions) == 0:
        sessions = __get_sessions()
        await asyncio.sleep(1)
    await asyncio.gather(*[asyncio.create_task(__login_user(session)) for session in sessions])
    await asyncio.gather(__update_calendar_pool(), __mark_attendance_pool())


async def __update_calendar_pool():
    while True:
        await asyncio.gather(*[__update_calendar(session) for session in __get_sessions()])
        await asyncio.sleep(int(data_manager.get_preferences().get("DEFAULT", "calendar_update_period")))


async def __update_calendar(session: MoodleSession):
    # print(f"[\\] Try to update calendar for '{session.username}'")
    try:
        await session.update_calendar()
    except LoginError:
        if await __login_user(session):
            await __update_calendar(session)
    except ClientOSError:
        print("[!] Network Error. Failed to try update calendar.")
    else:
        pass
        # print(f"[+] Updated calendar for '{session.username}'")


async def __mark_attendance_pool():
    while True:
        await asyncio.gather(*[__mark_attendance(session) for session in __get_sessions()])
        await asyncio.sleep(int(data_manager.get_preferences().get("DEFAULT", "attendance_check_period")))


async def __mark_attendance(session: MoodleSession):
    # print(f"[\\] Try to mark available attendance for {session.username}")
    try:
        await session.mark_available_attendance()
    except LoginError:
        if await __login_user(session):
            await __mark_attendance(session)
    except ClientOSError:
        print("[!] Network Error. Failed to try mark attendance.")
    else:
        pass
        # print(f"[+] Marked available attendance for '{session.username}'")


async def __login_user(session: MoodleSession):
    try:
        await session.login()
    except ValueError:
        print("[!] User with incorrect credentials:", session.username)
        data_manager.remove_user(session.username)
        return False
    except ClientOSError:
        print("[!] Network Error. Failed to login:", session.username)
        return False
    return True


def __get_sessions():
    users = data_manager.get_users()
    sessions = []
    for username, password in users.items():
        session: MoodleSession = MoodleSession.get_session(username)
        session.update_password(password)
        sessions.append(session)
    return sessions
