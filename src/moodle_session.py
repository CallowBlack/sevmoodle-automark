import re
import json
import aiohttp
from datetime import datetime

from src.calendar_manager import CalendarManager


class MoodleSession:
    # Username: MoodleSession
    __sessions = {}

    @staticmethod
    async def get_session(username):
        if username not in MoodleSession.__sessions:
            MoodleSession.__sessions[username] = MoodleSession(username,
                                                               aiohttp.ClientSession(requote_redirect_url=False))
        return MoodleSession.__sessions[username]

    def __init__(self, username, session: aiohttp.ClientSession):
        self.calendar = CalendarManager()
        self.session_key = None
        self.username = username
        self.password = None
        self.session = session

    def update_password(self, password: str):
        self.password = password

    async def is_logged_in(self) -> bool:
        if self.session_key is not None:
            url = "https://do.sevsu.ru/my/"
            main_page_response = await self.session.get(url)
            return url == main_page_response.url.__str__()
        return False

    async def login(self, password: str = None):
        if password is None:
            if self.password is None:
                raise Exception(
                    "You must to determine password in 'login' function or with 'update_password' function.")
            else:
                password = self.password

        to_auth_params = {"wants": "https://do.sevsu.ru/?", "idp": "64044bc53c749f0a74e4a4f13b1c0884",
                          "passive": "off"}
        async with self.session.get("https://do.sevsu.ru/auth/saml2/login.php",
                                    params=to_auth_params, allow_redirects=True) as to_auth_resp:
            auth_link_regex = re.compile(
                r"<form id=\"login-form\" onsubmit=\"login.disabled = true; return true;\" action=\"([^\"]+)\"")
            auth_link = re.search(auth_link_regex, await to_auth_resp.text()).group(1)
            auth_link = auth_link.replace("&amp;", "&")  # Replacing url encoded "&"

        login_data = {"username": self.username,
                      "password": password,
                      "rememberMe": "on", "credentialId": ""}
        async with self.session.post(auth_link, data=login_data) as login_response:
            login_response_text = await login_response.text()
            if re.search(auth_link_regex, login_response_text):
                raise ValueError(f"Incorrect username or password. -> {self.username}")
            print(f"Successfully logged in. -> {self.username}")

        saml_login_link_regex = re.compile(r"<form name=\"saml-post-binding\" method=\"post\" action=\"([^\"]+)\"")
        saml_login_data_regex = re.compile(r"<input type=\"hidden\" name=\"(\w+)\" value=\"([^\"]+)\"")
        saml_login_link = saml_login_link_regex.search(login_response_text).group(1)
        saml_login_data = {}
        for match in saml_login_data_regex.finditer(login_response_text):
            saml_login_data[match.group(1)] = match.group(2)

        async with self.session.post(saml_login_link, data=saml_login_data) as main_page_response:
            session_key_regex = re.compile(r"\"sesskey\":\"([^\"]+)\"")
            self.session_key = session_key_regex.search(await main_page_response.text()).group(1)

    async def update_calendar(self):
        if not (await self.is_logged_in()):
            raise Exception("You must login before update_calendar.")

        # self.calendar.clear()
        date_now = datetime.now()
        method_name = "core_calendar_get_calendar_day_view"
        request_dict = {
            "index": 0,
            "methodname": method_name,
            "args": {
                "year": date_now.year, "month": date_now.month, "day": 30, "courseid": 1, "categoryid": 0,
            }
        }
        request_data = json.dumps([request_dict])
        async with self.session.post("https://do.sevsu.ru/lib/ajax/service.php",
                                     params={"sesskey": self.session_key, "info": method_name},
                                     data=request_data) as calendar_response:

            day_data = (await calendar_response.json())[0]

        if day_data["error"]:
            raise ValueError("Have got error in calendar day info response.")

        day_events = day_data["data"]["events"]
        for event in day_events:
            if event["eventtype"] == "attendance":
                self.calendar.add_event(event["timestart"], event["timeduration"], event["url"])

    async def mark_available_attendance(self):
        active_links = self.calendar.get_active_events()
        for link in active_links:
            pass

    async def close(self):
        await self.session.close()
