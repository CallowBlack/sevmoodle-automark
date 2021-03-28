from src.moodle_session import MoodleSession

session: MoodleSession = MoodleSession.get_session("hello")
session.update_password("zero")
assert not session.is_logged_in(), "is_logged_in test without login failed"

session.login()
assert not session.is_logged_in(), "is_logged_in test with login failed"

session = MoodleSession.get_session("00-010670")
session.update_password("WDD7tves")

session.login()
assert session.is_logged_in(), "login with correct credentials failed"
print("All tests was passed.")