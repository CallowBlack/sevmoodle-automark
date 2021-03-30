import asyncio
from src.moodle_session import MoodleSession
import src.session_manager as session_manager
import src.data_manager as data_manager
import aioconsole


async def terminal_loop():
    print_command_list(None)
    while True:
        command_args = (await aioconsole.ainput("> ")).split()
        if len(command_args) == 0:
            continue

        command = command_args[0]
        args = command_args[1:]
        for command_name, command_info in command_list.items():
            if command_name == command:
                if len(args) < command_info["args"]:
                    print("Too few arguments.")
                    break
                _ = command_info["func"](args)
                break
        else:
            print("Unknown command:", command)


def print_command_list(_):
    for command_name, command_info in command_list.items():
        print(command_name, command_info["usage"])


def print_user_list(_):
    for username, password in data_manager.get_users().items():
        print(f"{username}:{password}")


def print_prefs_list(_):
    for pref_name, pref_value in data_manager.get_preferences()["DEFAULT"].items():
        print(pref_name + " = " + pref_value)


async def main():
    await asyncio.gather(session_manager.session_loop(), terminal_loop())

command_list = {
    "user_add": {
        "usage": "<name> <password>",
        "args": 2,
        "func": lambda args: data_manager.add_user(args[0], args[1])
    },

    "user_get_calendar": {
        "usage": "<name>",
        "args": 1,
        "func": lambda args: MoodleSession.get_session(args[0]).calendar.show()
    },

    "user_remove": {
        "usage": "<name>",
        "args": 1,
        "func": lambda args: data_manager.remove_user(args[0])
    },

    "user_list": {
        "usage": "",
        "args": 0,
        "func": print_user_list
    },

    "pref_change": {
        "usage": "<name> <value>",
        "args": 2,
        "func": lambda args: data_manager.change_preference(args[0], args[1])
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
    asyncio.run(main())
