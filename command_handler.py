import telebot.types
from telbot_storage_handler import StorageHandler


class CommandHandler:
    def __init__(self):
        self.command_list = {
            '/system': self.__com_system,
            '/status': self.__com_status
        }
        self.super_command_list = {
            '/text': self.__com_text,
            '/voice': self.__com_voice,
            '/boobs': self.__com_boobs,
            '/commands': self.__com_commands,
            '/god': self.__com_god
        }
        self.disable_commands = {
            "0",
            "off",
            "disable"
        }
        self.enable_commands = {
            "1",
            "on",
            "enable"
        }

    def is_command(self, message: telebot.types.Message, admin: float):
        command = message.text.strip().split()[0].lower()
        if command in self.command_list or (command in self.super_command_list and message.from_user.id == admin):
            return True
        else:
            return False

    def handle(self, message: telebot.types.Message, admin: float, storage: StorageHandler):
        command = message.text.strip().split()[0].lower()
        args = message.text.strip().split()[1:]
        text_args = ' '.join(str(item) for item in args)
        if command in self.command_list:
            return self.command_list[command](message, text_args, storage)
        elif command in self.super_command_list and message.from_user.id == admin:
            return self.super_command_list[command](message, text_args, storage)
        return "Bad command"

    @staticmethod
    def __com_system(message: telebot.types.Message, args: str, storage: StorageHandler):
        if message.message_thread_id is None:
            where_val = "WHERE chat_id=" + str(message.chat.id)+" AND " + "thread_id is NULL"
        else:
            where_val = "WHERE chat_id=" + str(message.chat.id)+" AND " + "thread_id="+str(message.message_thread_id)
        if args == "":
            request = "SELECT system_message FROM chats " + where_val
            answer = storage.execute_command(request)
        else:
            request = "UPDATE chats SET system_message=\""+args+"\" " + where_val
            answer = storage.execute_command(request)
        return answer

    @staticmethod
    def __com_status(message: telebot.types.Message, args: str, storage: StorageHandler):
        return "Online"

    def __com_text(self, message: telebot.types.Message, args: str, storage: StorageHandler):
        if message.message_thread_id is None:
            where_val = "WHERE chat_id="+str(message.chat.id)+" AND " + "thread_id is NULL"
        else:
            where_val = "WHERE chat_id="+str(message.chat.id)+" AND " + "thread_id="+str(message.message_thread_id)
        if args is None:
            request = "SELECT allow_text FROM chats " + where_val
            answer = storage.execute_command(request)
        elif args in self.disable_commands:
            request = "UPDATE chats SET allow_text=0 " + where_val
            answer = storage.execute_command(request)
        elif args in self.enable_commands:
            request = "UPDATE chats SET allow_text=1 " + "\" " + where_val
            answer = storage.execute_command(request)
        else:
            answer = "Bad command arguments"
        return answer

    def __com_voice(self, message: telebot.types.Message, args: str, storage: StorageHandler):
        if message.message_thread_id is None:
            where_val = "WHERE chat_id=" + str(message.chat.id) + " AND " + "thread_id is NULL"
        else:
            where_val = "WHERE chat_id=" + str(message.chat.id) + " AND " + "thread_id="+str(message.message_thread_id)
        if args is None:
            request = "SELECT allow_voice FROM chats " + where_val
            answer = storage.execute_command(request)
        elif args in self.disable_commands:
            request = "UPDATE chats SET allow_voice=0 " + where_val
            answer = storage.execute_command(request)
        elif args in self.enable_commands:
            request = "UPDATE chats SET allow_voice=1 " + where_val
            answer = storage.execute_command(request)
        else:
            answer = "Bad command arguments"
        return answer

    def __com_boobs(self, message: telebot.types.Message, args: str, storage: StorageHandler):
        if message.message_thread_id is None:
            where_val = "WHERE chat_id="+str(message.chat.id)+" AND "+"thread_id is NULL"
        else:
            where_val = "WHERE chat_id="+str(message.chat.id)+" AND " + "thread_id="+str(message.message_thread_id)
        if args is None:
            request = "SELECT allow_boobs FROM chats " + where_val
            answer = storage.execute_command(request)
        elif args in self.disable_commands:
            request = "UPDATE chats SET allow_boobs=0 " + where_val
            answer = storage.execute_command(request)
        elif args in self.enable_commands:
            request = "UPDATE chats SET allow_boobs=1 " + where_val
            answer = storage.execute_command(request)
        else:
            answer = "Bad command arguments"
        return answer

    def __com_commands(self, message: telebot.types.Message, args: str, storage: StorageHandler):
        if message.message_thread_id is None:
            where_val = "WHERE chat_id="+str(message.chat.id)+" AND "+"thread_id is NULL"
        else:
            where_val = "WHERE chat_id="+str(message.chat.id)+" AND " + "thread_id="+str(message.message_thread_id)
        if args is None:
            request = "SELECT allow_commands FROM chats " + where_val
            answer = storage.execute_command(request)
        elif args in self.disable_commands:
            request = "UPDATE chats SET allow_commands=0 " + where_val
            answer = storage.execute_command(request)
        elif args in self.enable_commands:
            request = "UPDATE chats SET allow_commands=1 " + where_val
            answer = storage.execute_command(request)
        else:
            answer = "Bad command arguments"
        return answer

    @staticmethod
    def __com_god(message: telebot.types.Message, args: str, storage: StorageHandler):
        answer = storage.execute_command(args)
        return answer
