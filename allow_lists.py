from telbot_storage_handler import StorageHandler


class AllowedLists:

    allowed_chat_list_text = []
    allowed_chat_list_voice = []
    allowed_command_user_list = []

    def __init__(self, storage: StorageHandler, admin_id: int):
        self.allowed_chat_list_text.append(admin_id)
        self.allowed_chat_list_text.extend(storage.get_allowed_chat_text())
        self.allowed_chat_list_text = list(dict.fromkeys(self.allowed_chat_list_text))

        self.allowed_chat_list_voice.append(admin_id)
        self.allowed_chat_list_voice.extend(storage.get_allowed_chat_voice())
        self.allowed_chat_list_voice = list(dict.fromkeys(self.allowed_chat_list_voice))

        self.allowed_command_user_list.append(admin_id)
        self.allowed_command_user_list.extend(storage.get_allowed_command_users())
        self.allowed_command_user_list = list(dict.fromkeys(self.allowed_command_user_list))

    def update(self, storage: StorageHandler):
        self.allowed_chat_list_text.extend(storage.get_allowed_chat_text())
        self.allowed_chat_list_text = list(dict.fromkeys(self.allowed_chat_list_text))

        self.allowed_chat_list_voice.extend(storage.get_allowed_chat_voice())
        self.allowed_chat_list_voice = list(dict.fromkeys(self.allowed_chat_list_voice))

        self.allowed_command_user_list.extend(storage.get_allowed_command_users())
        self.allowed_command_user_list = list(dict.fromkeys(self.allowed_command_user_list))
