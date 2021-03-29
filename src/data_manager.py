import os
import pickle
import configparser

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
