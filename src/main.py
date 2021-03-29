import asyncio
import src.session_manager as session_manager
import src.data_manager as data_manager
import aioconsole


async def terminal_loop():
    print_command_list()
    while True:
        command_args = (await aioconsole.ainput("> ")).split()
        if len(command_args) == 0:
            continue

        command = command_args[0]
        args = command_args[1:]
        if command == "user_add":
            if len(args) < 2:
                print("To few arguments.")
                continue
            data_manager.add_user(args[0], args[1])
        elif command == "user_remove":
            if len(args) < 1:
                print("To few arguments.")
                continue
            data_manager.remove_user(args[0])
        elif command == "user_list":
            for username, password in data_manager.get_users():
                print(f"{username}:{password}")
        elif command == "pref_change":
            if len(args) < 2:
                print("To few arguments.")
                continue
            data_manager.change_preference(args[0], args[1])
        elif command == "pref_list":
            for pref_name, pref_value in data_manager.get_preferences()["DEFAULT"].items():
                print(pref_name + " = " + pref_value)
        elif command == "command_list":
            print_command_list()
        else:
            print("Unknown command:", command)


def print_command_list():
    print("Commands:")
    print("\tuser_add <name> <password>")
    print("\tuser_remove <name>")
    print("\tuser_list")
    print("\tpref_change <name> <value>")
    print("\tpref_list")
    print("\tcommand_list")


async def main():
    await asyncio.gather(session_manager.session_loop(), terminal_loop())


if __name__ == "__main__":
    asyncio.run(main())