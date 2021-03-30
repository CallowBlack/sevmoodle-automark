import pprint
import os
import pickle
import configparser
import re
import json
import requests
import threading
import time
from datetime import datetime


class CalendarManager:

    def __init__(self):
        # Calendar format:
        # year:int -> {
        #   month:int -> {
        #       day:int -> {
        #           "link": (start_time, duration), ...
        #       }
        #   }
        # }
        self.__calendar = {}

    def show(self):
        pprint.pprint(self.__calendar)

    def clear(self):
        self.__calendar.clear()

    def add_event(self, start_timestamp: int, duration: int, link: str):
        year, month, day = time_to_date(start_timestamp)
        if year not in self.__calendar:
            self.__calendar[year] = {}
        if month not in self.__calendar[year]:
            self.__calendar[year][month] = {}
        if day not in self.__calendar[year][month]:
            self.__calendar[year][month][day] = {}
        current_events = self.__calendar[year][month][day]
        current_events[link] = (start_timestamp, duration)

    def get_active_events(self, target_timestamp: int = None) -> list:
        events = []

        if target_timestamp is None:
            target_timestamp = int(datetime.now().timestamp())
        year, month, day = time_to_date(target_timestamp)

        if not self.__has_calendar_date(year, month, day):
            return events

        current_events = self.__calendar[year][month][day]
        for link, event_data in current_events.items():
            start_timestamp, duration = event_data
            if start_timestamp < target_timestamp < start_timestamp + duration:
                events.append(link)
        return events

    def remove_event(self, event_timestamp: int, link: str = None):
        year, month, day = time_to_date(event_timestamp)
        if not self.__has_calendar_date(year, month, day):
            return

        current_events: dict = self.__calendar[year][month][day]
        if link is not None:
            current_events.pop(link, None)
        else:
            for link, event_data in current_events.items():
                start_timestamp, duration = event_data
                if start_timestamp == event_timestamp:
                    del current_events[link]

    def __has_calendar_date(self, year, month, day) -> bool:
        return year in self.__calendar and \
                month in self.__calendar[year] and \
                day in self.__calendar[year][month]


__loaded = False
__users_filename = "../users.pyo"
__preferences_filename = "../preferences.ini"
__default_preferences = {"attendance_check_period": 60,
                         "calendar_update_period": 60*60}

__users = {}
__preferences = configparser.ConfigParser(__default_preferences)


def add_user(username: str, password: str):
    if not __loaded:
        load()
    __users[username] = password
    print(f"[+] Added user {username}")
    save()


def remove_user(username: str):
    if not __loaded:
        load()
    __users.pop(username)
    print(f"[-] Remove user {username}")
    save()


def get_users():
    if not __loaded:
        load()
    return __users


def change_preference(name, value):
    if name not in __default_preferences:
        print("[-] Unknown preference")
    __preferences.set("DEFAULT", name, value)


def get_preferences():
    if not __loaded:
        load()
    return __preferences


def save():
    if not __loaded:
        return
    with open(__users_filename, "wb") as users_file:
        pickle.dump(__users, users_file)
    with open(__preferences_filename, "w") as preferences_file:
        __preferences.write(preferences_file)


def load():
    global __users
    global __loaded
    global __preferences
    if os.path.exists(__users_filename):
        with open(__users_filename, "rb") as users_file:
            __users = pickle.load(users_file)
    if os.path.exists(__preferences_filename):
        with open(__preferences_filename, "r") as preferences_file:
            __preferences.read_file(preferences_file.readlines())
    __loaded = True


class LoginError(Exception):
    pass


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
        return self.session_key is not None

    def login(self, password: str = None):
        if password is None:
            if self.password is None:
                raise ValueError(
                    "You must to determine password in 'login' function or update it in 'update_password' function.")
            else:
                password = self.password

        to_auth_params = {"wants": "https://do.sevsu.ru/?", "idp": "64044bc53c749f0a74e4a4f13b1c0884",
                          "passive": "off"}
        to_auth_resp = self.session.get("https://do.sevsu.ru/auth/saml2/login.php", params=to_auth_params,
                                        allow_redirects=True)
        auth_link_regex = re.compile(
            r"<form id=\"login-form\" onsubmit=\"login.disabled = true; return true;\" action=\"([^\"]+)\"")
        auth_link = re.search(auth_link_regex, to_auth_resp.text).group(1)
        auth_link = clear_html_url(auth_link)

        login_data = {"username": self.username,
                      "password": password,
                      "rememberMe": "on", "credentialId": ""}
        login_response = self.session.post(auth_link, data=login_data)
        login_response_text = login_response.text
        if re.search(auth_link_regex, login_response_text):
            raise ValueError(f"Incorrect username or password. -> {self.username}")
        print(f"[+] Successfully logged in. -> {self.username}")

        saml_login_link_regex = re.compile(r"<form name=\"saml-post-binding\" method=\"post\" action=\"([^\"]+)\"")
        saml_login_data_regex = re.compile(r"<input type=\"hidden\" name=\"(\w+)\" value=\"([^\"]+)\"")
        saml_login_link = saml_login_link_regex.search(login_response_text).group(1)
        saml_login_data = {}
        for match in saml_login_data_regex.finditer(login_response_text):
            saml_login_data[match.group(1)] = match.group(2)

        main_page_response = self.session.post(saml_login_link, data=saml_login_data)
        session_key_regex = re.compile(r"\"sesskey\":\"([^\"]+)\"")
        self.session_key = session_key_regex.search(main_page_response.text).group(1)

    def update_calendar(self):
        if not self.is_logged_in():
            raise LoginError("You must login before update_calendar.")

        # self.calendar.clear()
        date_now = datetime.now()
        method_name = "core_calendar_get_calendar_day_view"
        request_dict = {
            "index": 0,
            "methodname": method_name,
            "args": {
                "year": date_now.year, "month": date_now.month, "day": date_now.day, "courseid": 1, "categoryid": 0,
            }
        }
        request_data = json.dumps([request_dict])
        calendar_response = self.session.post("https://do.sevsu.ru/lib/ajax/service.php",
                                              params={"sesskey": self.session_key, "info": method_name},
                                              data=request_data)
        day_data = calendar_response.json()[0]

        if day_data["error"]:
            raise LoginError("Have got error in calendar day info response.")

        day_events = day_data["data"]["events"]
        for event in day_events:
            if event["eventtype"] == "attendance":
                self.calendar.add_event(event["timestart"], event["timeduration"], event["url"])

    def mark_available_attendance(self):
        if not self.is_logged_in():
            raise LoginError()
        active_links = self.calendar.get_active_events()
        for link in active_links:
            attendance_calendar_resp = self.session.get(link)
            attendance_links_regex = re.compile("colspan=\"3\"><a href=\"([^\"]+)\"")
            attendance_text = attendance_calendar_resp.text
            attendance_links = attendance_links_regex.findall(attendance_text)

            for attendance_link in attendance_links:
                attendance_link = clear_html_url(attendance_link)
                sess_id_regex = re.compile(r"sessid=(\d+)&")
                sess_id = sess_id_regex.search(attendance_link).group(1)

                get_attendance_page_resp = self.session.get(attendance_link)
                status_id_regex = re.compile(r"name=\"status\"\s+id=\"id_status_(\d+)\"")
                text = get_attendance_page_resp.text
                status_id = status_id_regex.search(text).group(1)

                attendance_data = {"sessid": sess_id, "sesskey": self.session_key,
                                   "_qf__mod_attendance_form_studentattendance": 1,
                                   "mform_isexpanded_id_session": 1,
                                   "status": status_id,
                                   "submitbutton": "Сохранить"}

                mark_attendance_resp = self.session.post("https://do.sevsu.ru/mod/attendance/attendance.php",
                                                         data=attendance_data)
                text = mark_attendance_resp.text
                if text.find("Ошибка") != -1:
                    print(f"[-] Error while marking attendance. Link: {attendance_link}")
                else:
                    print(f"[+] Attendance was marked successfully. Link: {attendance_link}")


def session_loop():
    sessions = []
    while len(sessions) == 0:
        sessions = __get_sessions()
        time.sleep(1)

    while True:
        for session in sessions:
            __update_calendar(session)
            __mark_attendance(session)
            time.sleep(int(get_preferences().get("DEFAULT", "attendance_check_period")))

        sessions = __get_sessions()


def __update_calendar(session: MoodleSession):
    # print(f"[\\] Try to update calendar for '{session.username}'")
    try:
        session.update_calendar()
    except LoginError:
        if __login_user(session):
            __update_calendar(session)
    except requests.ConnectionError:
        print("[-] Network Error. Failed to try update calendar.")
    else:
        print(f"[+] {datetime.now()} Updated calendar for '{session.username}'")


def __mark_attendance(session: MoodleSession):
    # print(f"[\\] Try to mark available attendance for {session.username}")
    try:
        session.mark_available_attendance()
    except LoginError:
        if __login_user(session):
            __mark_attendance(session)
    except requests.ConnectionError:
        print("[-] Network Error. Failed to try mark attendance.")
    else:
        pass
        # print(f"[+] Marked available attendance for '{session.username}'")


def __login_user(session: MoodleSession):
    try:
        session.login()
    except ValueError:
        print("[!] User with incorrect credentials:", session.username)
        remove_user(session.username)
        return False
    except requests.ConnectionError:
        print("[!] Network Error. Failed to login:", session.username)
        return False
    return True


def __get_sessions():
    users = get_users()
    sessions = []
    for username, password in users.items():
        session: MoodleSession = MoodleSession.get_session(username)
        session.update_password(password)
        sessions.append(session)
    return sessions


def time_to_date(timestamp: int) -> (int, int, int):
    date = datetime.fromtimestamp(timestamp)
    return date.year, date.month, date.day


def clear_html_url(url: str) -> str:
    return url.replace("&amp;", "&")


def terminal_loop():
    print_command_list(None)
    while True:
        command_args = input("> ").split()
        if len(command_args) == 0:
            continue

        command = command_args[0]
        args = command_args[1:]
        for command_name, command_info in command_list.items():
            if command_name == command:
                if len(args) < command_info["args"]:
                    print("Too few arguments.")
                    break
                command_info["func"](args)
                break
        else:
            print("Unknown command:", command)


def print_command_list(_):
    for command_name, command_info in command_list.items():
        print(command_name, command_info["usage"])


def print_user_list(_):
    for username, password in get_users().items():
        print(f"{username}:{password}")


def print_prefs_list(_):
    for pref_name, pref_value in get_preferences()["DEFAULT"].items():
        print(pref_name + " = " + pref_value)


def main():
    session_loop_thread = threading.Thread(target=session_loop)
    session_loop_thread.start()
    terminal_loop()


command_list = {
    "user_add": {
        "usage": "<name> <password>",
        "args": 2,
        "func": lambda args: add_user(args[0], args[1])
    },

    "user_get_calendar": {
        "usage": "<name>",
        "args": 1,
        "func": lambda args: MoodleSession.get_session(args[0]).calendar.show()
    },

    "user_remove": {
        "usage": "<name>",
        "args": 1,
        "func": lambda args: remove_user(args[0])
    },

    "user_list": {
        "usage": "",
        "args": 0,
        "func": print_user_list
    },

    "pref_change": {
        "usage": "<name> <value>",
        "args": 2,
        "func": lambda args: change_preference(args[0], args[1])
    },

    "pref_list": {
        "usage": "",
        "args": 0,
        "func": print_prefs_list
    },

    "command_list": {
        "usage": "<name> <password>",
        "args": 0,
        "func": print_command_list
    }
}

if __name__ == "__main__":
    main()
