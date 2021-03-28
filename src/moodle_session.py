import urllib3
import requests
import re
import json
from datetime import datetime

from src.calendar_manager import CalendarManager


class MoodleSession:
    # Username: MoodleSession
    __sessions = {}

    @staticmethod
    def get_session(username):
        if username not in MoodleSession.__sessions:
            MoodleSession.__sessions[username] = MoodleSession(username)
        return MoodleSession.__sessions[username]

    def __init__(self, username):
        self.calendar = CalendarManager()
        self.session_key = None
        self.username = username
        self.password = None
        self.session = requests.Session()

    def update_password(self, password: str):
        self.password = password

    def is_logged_in(self) -> bool:
        if self.session_key is not None:
            url = "https://do.sevsu.ru/my/"
            main_page_response = self.session.get(url)
            return url == main_page_response.url
        return False

    def login(self, password: str = None):
        if password is None:
            if self.password is None:
                raise Exception(
                    "You must to determine password in 'login' function or with 'update_password' function.")
            else:
                password = self.password
        # if debug:
        #     proxies = {
        #         'http': 'http://127.0.0.1:8080',
        #         'https': 'http://127.0.0.1:8080',
        #     }
        #     session.proxies.update(proxies)
        #     session.headers.update(
        #         {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"})
        #     session.verify = False
        #     urllib3.disable_warnings()

        auth_site = self.session.get("https://do.sevsu.ru/auth/saml2/login.php",
                                     params={"wants": "https://do.sevsu.ru/?",
                                             "idp": "64044bc53c749f0a74e4a4f13b1c0884",
                                             "passive": "off"})

        auth_link_regex = re.compile(
            r"<form id=\"login-form\" onsubmit=\"login.disabled = true; return true;\" action=\"([^\"]+)\"")
        auth_link = re.search(auth_link_regex, auth_site.text).group(1)
        auth_link = auth_link.replace("&amp;", "&")  # Replacing url encoded "&"
        login_data = {"username": self.username,
                      "password": password,
                      "rememberMe": "on", "credentialId": ""}

        login_response_content = self.session.post(auth_link, data=login_data).text
        if re.search(auth_link_regex, login_response_content):
            print(f"Incorrect username or password. -> {self.username}")
            return

        print(f"Successfully logged in. -> {self.username}")
        saml_login_link_regex = re.compile(r"<form name=\"saml-post-binding\" method=\"post\" action=\"([^\"]+)\"")
        saml_login_data_regex = re.compile(r"<input type=\"hidden\" name=\"(\w+)\" value=\"([^\"]+)\"")

        saml_login_link = saml_login_link_regex.search(login_response_content).group(1)
        saml_login_data = {}
        for match in saml_login_data_regex.finditer(login_response_content):
            saml_login_data[match.group(1)] = match.group(2)

        main_page_content = self.session.post(saml_login_link, data=saml_login_data).content.decode()

        session_key_regex = re.compile(r"\"sesskey\":\"([^\"]+)\"")

        self.session_key = session_key_regex.search(main_page_content).group(1)

    def update_calendar(self):
        if not self.is_logged_in():
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
        calendar_response = self.session.post("https://do.sevsu.ru/lib/ajax/service.php",
                                              params={"sesskey": self.session_key, "info": method_name},
                                              data=request_data)

        day_data = calendar_response.json()[0]
        if day_data["error"]:
            raise Exception("Have got error in calendar day info response.")

        day_events = day_data["data"]["events"]
        for event in day_events:
            if event["eventtype"] == "attendance":
                self.calendar.add_event(event["timestart"], event["timeduration"], event["url"])