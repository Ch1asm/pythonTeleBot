import re

__all__ = ["parse"]

# command format:
# start with "$bot"
# next word table: user, chat
# next word "set" or "get"
# next word interested param
# next word if set value

command_list = ["get", "set"]
table_list = ["user", "chat"]
get_chat_param_list = ["all", "chat_name", "allow_text", "allow_voice", "allow_boobs", "system_message", "used_model"]
set_chat_param_list = ["allow_text", "allow_voice", "allow_boobs", "system_message", "model"]
get_user_param_list = ["chat_name", "allowed_commands"]
set_user_param_list = ["chat_name", "allowed_commands"]

all_param_list = get_chat_param_list + set_chat_param_list + get_user_param_list + set_user_param_list
all_param_list = list(dict.fromkeys(all_param_list))


def parse(text_line: str, super_user_mod: bool, user_id: int, chat_id: int):
    if not (text_line.startswith("$bot")):
        return "Not a command"
    text_line = re.sub(" +", " ", text_line.replace("\t", " "))
    if text_line.startswith("$bot god ") and super_user_mod:
        return god_commands(text_line)
    command = text_line.split(" ")
    if len(command) < 4:
        return "Not enough command arguments"
    if super_user_mod:  # superuser can override user_id and chat_id
        if command[3] not in all_param_list:  # if it's not a command than override?
            if check_number(command[3]):  # must be an override
                if command[2] == table_list[0]:  # user
                    user_id = int(command[3])
                elif command[2] == table_list[1]:  # chat
                    chat_id = int(command[3])
                command.pop(3)

    if command[1] in command_list:
        if command[1] == command_list[0]:  # get
            return parse_get(command, user_id, chat_id)
        elif command[1] == command_list[1]:  # set
            return parse_set(command, user_id, chat_id)
    else:
        return command[1] + " not in " + str(command_list)
    return "Bad command"


def parse_get(command: [], user_id: int, chat_id: int):
    if command[2] in table_list:
        if command[2] == table_list[0]:  # user
            return parse_get_user(command, user_id)
        elif command[2] == table_list[1]:  # chat
            return parse_get_chat(command, chat_id)
    else:
        return command[2] + " not in " + str(table_list)


def parse_get_user(command: [], user_id: int):
    if command[3] in get_user_param_list:
        return "SELECT " + command[3] + " FROM users WHERE user_id=" + str(user_id)
    return command[3] + " not in " + str(get_user_param_list)


def parse_get_chat(command: [], chat_id: int):
    if command[3] in get_chat_param_list:
        if command[3] == get_chat_param_list[0]:  # all
            command[3] = "*"
        return "SELECT " + command[3] + " FROM chats WHERE chat_id=" + str(chat_id)
    return command[3] + " not in " + str(get_chat_param_list)


def parse_set(command: [], user_id: int, chat_id: int):
    if command[2] in table_list:
        if command[2] == table_list[0]:  # user
            return parse_set_user(command, user_id)
        elif command[2] == table_list[1]:  # chat
            return parse_set_chat(command, chat_id)
    else:
        return command[2] + " not in " + str(table_list)


def parse_set_user(command: [], user_id: int):
    if command[3] in set_user_param_list:
        return ("UPDATE users SET " +
                command[3] + "=\"" +
                ' '.join(str(elem) for elem in command[4:])
                + "\" WHERE user_id="
                + str(user_id))
    return command[3] + " not in " + str(set_user_param_list)


def parse_set_chat(command: [], chat_id: int):
    if command[3] in set_chat_param_list:
        return ("UPDATE chats SET " +
                command[3] + "=\"" +
                ' '.join(str(elem) for elem in command[4:]) +
                "\" WHERE chat_id=" +
                str(chat_id))
    return command[3] + " not in " + str(set_chat_param_list)


def check_number(s: str):
    try:
        int(s)
        return True
    except ValueError:
        return False


def god_commands(text_command: str):
    command = text_command[9:].strip()
    return command
