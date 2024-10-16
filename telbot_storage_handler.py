# telbot_storage_handler module
import sqlite3
import logging
import telebot
from pathlib import Path

logger = logging.getLogger(__name__)

# Class for handling with bot database users, messages and other
class StorageHandler:
    # Out connection to the sqlite db
    connection_db = None

    # db_pass - pass to out database, we'll check if it's exists, and create if it's not
    def __init__(self, db_pass: Path):
        logger.info("__init__ StoreHandler")
        try:
            db_pass.resolve(strict=True)
        except FileNotFoundError as e:
            logger.exception("Database not found, trying to create a new one.", e.__repr__(), e.args)

        try:
            self.connection_db = sqlite3.connect(db_pass, check_same_thread=False)
            self.connection_db.execute("pragma journal_mode=wal;")
            cursor = self.connection_db.cursor()
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS users 
                    (user_id DOUBLE PRIMARY KEY,
                     first_name text,
                     last_name text,
                     username text,
                     chat_name text,
                     allowed_commands integer)
                     ''')
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS messages 
                    (message_id integer not null,
                     message_thread_id integer,
                     date integer,
                     from_user_id DOUBLE,
                     chat_id DOUBLE not null,
                     reply_to_message_id integer,
                     message_photo text,
                     message_voice text,
                     message_text text,
                     PRIMARY KEY(chat_id, message_id))
                    ''')
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS chats 
                    (chat_id DOUBLE,
                     chat_name text,
                     thread_id integer,
                     used_model text,
                     system_message text,
                     allow_text integer,
                     allow_voice integer,
                     allow_boobs integer,
                     allow_commands integer,
                     PRIMARY KEY(chat_id, thread_id))
                    ''')
            self.connection_db.commit()
        except Exception as e:
            logger.exception("Error when creating/connecting database: %s", e.__repr__(), e.args)
            pass
        else:
            logger.info("DB " + str(db_pass) + " connection success.")

    # Closing connection for no memory licks
    def __del__(self):
        logger.info("__del__ StoreHandler")
        self.connection_db.close()

    # store info about user, chat and message
    def log_message(self, message: telebot.types.Message, photo_path, voice_path, voice_text):
        logger.info("log_message StoreHandler")
        # adding user info if new
        answer = ""
        exist_users = None
        cursor = self.connection_db.cursor()
        try:
            exist_users = cursor.execute('SELECT * FROM users WHERE user_id=?', (message.from_user.id,))
        except Exception as e:
            logger.exception("Cannot SELECT user_id from database: %s", e.__repr__(), e.args)
            pass
        if exist_users.fetchone() is None:
            try:
                if message.from_user.first_name is not None:
                    chat_name = message.from_user.first_name
                elif message.from_user.username is not None:
                    chat_name = message.from_user.username
                else:
                    chat_name = "Гость"
                cursor.execute('INSERT INTO users '
                               '(user_id, '
                               'first_name, '
                               'last_name, '
                               'username, '
                               'chat_name, '
                               'allowed_commands) '
                               'VALUES (?, ?, ?, ?, ?, ?)',
                               (message.from_user.id,
                                message.from_user.first_name,
                                message.from_user.last_name,
                                message.from_user.username,
                                chat_name,
                                0))
                self.connection_db.commit()
                logger.info("New user " + str(message.from_user.id) + " added")
                answer = ("New user: \n" + str(message.from_user.id) + "\n" + chat_name)
            except Exception as e:
                logger.exception("Cannot INSERT user_id to database: %s", e.__repr__(), e.args)
        else:
            logger.info("User " + str(message.from_user.id) + " exists")
        # adding chat info if new
        exist_chats = None
        try:
            if message.is_topic_message:
                exist_chats = cursor.execute('SELECT * FROM chats WHERE chat_id=? and thread_id=?',
                                             (message.chat.id, message.message_thread_id, ))
            else:
                exist_chats = cursor.execute('SELECT * FROM chats WHERE chat_id=? and thread_id is Null',
                                             (message.chat.id,))
        except Exception as e:
            logger.exception("Cannot SELECT chat_id from database: %s", e.__repr__(), e.args)
            pass
        if exist_chats.fetchone() is None:
            try:
                cursor.execute('INSERT INTO chats '
                               '(chat_id, '
                               'chat_name, '
                               'thread_id, '
                               'used_model, '
                               'system_message, '
                               'allow_text, '
                               'allow_voice,'
                               'allow_boobs, '
                               'allow_commands) '
                               'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (message.chat.id,
                                message.chat.title,
                                message.message_thread_id,
                                "default",
                                "default",
                                0,
                                0,
                                0,
                                0))
                self.connection_db.commit()
                logger.info("New chat " + str(message.chat.id) + " added")
                answer = ("New chat: \n" + str(message.chat.id))
            except Exception as e:
                logger.exception("Cannot INSERT chat_id to database: %s", e.__repr__(), e.args)
        else:
            logger.info("Chat " + str(message.chat.id) + " exists")
        # adding message info
        rep_mes_id = 0
        mes_text = message.text
        if voice_text is not None:
            mes_text = voice_text
        if message.reply_to_message is not None:
            rep_mes_id = message.reply_to_message.id
        try:
            cursor.execute('INSERT INTO messages '
                           '(message_id, '
                           'message_thread_id, '
                           'date, '
                           'from_user_id, '
                           'chat_id, '
                           'reply_to_message_id, '
                           'message_photo, '
                           'message_voice, '
                           'message_text) '
                           'VALUES (?,?,?,?,?,?,?,?,?)',
                           (message.id,
                            message.message_thread_id,
                            message.date,
                            message.from_user.id,
                            message.chat.id,
                            rep_mes_id,
                            photo_path,
                            voice_path,
                            mes_text))
            self.connection_db.commit()
            logger.info("New messaage ", message.id, " added")
        except Exception as e:
            logger.exception("Cannot INSERT message to database: %s", e.__repr__(), e.args)
        return answer

    def getmessagegptthread(self, message: telebot.types.Message, bot_id: str, sys_mes: str):
        logger.info("getmessagegptthread StoreHandler")
        dialog = [
            {
                "role": "user",
                "content": self.getchatnamebyid(message.from_user.id) + ": " + message.text,
            }
        ]
        rows = None
        cursor = self.connection_db.cursor()
        if message.reply_to_message is not None:
            prev_msg_id = message.reply_to_message.id
            counter = 10
            while prev_msg_id != 0 and counter > 0:
                try:
                    prev_msg = cursor.execute('SELECT reply_to_message_id,'
                                              ' message_text, '
                                              'from_user_id '
                                              'FROM messages '
                                              'WHERE chat_id=? '
                                              'AND message_id=?',
                                              (message.chat.id,
                                               prev_msg_id,))
                    rows = prev_msg.fetchall()
                except Exception as e:
                    logger.exception("No such message in stored dialogs: %s", e.__repr__(), e.args)

                if len(rows) != 0:
                    role = "user"
                    if rows[0][2] == int(bot_id):
                        role = "assistant"
                        dialog.insert(0,
                                      {
                                          "role": role,
                                          "content": rows[0][1],
                                      }
                                      )
                    else:
                        dialog.insert(0,
                                      {
                                          "role": role,
                                          "content": self.getchatnamebyid(int(rows[0][2])) + ": " + rows[0][1],
                                      }
                                      )
                    prev_msg_id = rows[0][0]
                    counter = counter - 1
                else:
                    prev_msg_id = 0
        if message.message_thread_id is not None:
            chat_sys_message = cursor.execute('SELECT system_message FROM chats WHERE chat_id=? and thread_id=?',
                                              (message.chat.id, message.message_thread_id, ))
        else:
            chat_sys_message = cursor.execute('SELECT system_message FROM chats WHERE chat_id=? and thread_id is NULL',
                                              (message.chat.id, ))
        rows = chat_sys_message.fetchall()
        if rows[0] != "default":
            sys_mes = str(rows[0])
        dialog.insert(0,
                      {
                          "role": "system",
                          "content": sys_mes,
                      }
                      )

        return dialog

    @staticmethod
    def checkgptstory(message: telebot.types.Message, bot_id: str):
        logger.info("checkgptstory StoreHandler")
        if "@бармен" in message.text.lower() or "@bartender_kabak_bot" in message.text.lower():
            return True
        if message.reply_to_message is not None:
            if message.reply_to_message.from_user.id == int(bot_id):
                return True
        return False

    def getchatnamebymessage(self, message: telebot.types.Message):
        logger.info("getchatnamebymessage StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            row = cursor.execute('SELECT chat_name '
                                 'FROM users '
                                 'WHERE user_id=? ',
                                 (message.from_user.id,
                                  ))
            return str(row.fetchall()[0])
        except Exception as e:
            logger.exception("Cannot find user in DB: %s", e.__repr__(), e.args)
            return "Гость"

    def getchatnamebyid(self, user_id: int):
        logger.info("getchatnamebyid StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            row = cursor.execute('SELECT chat_name '
                                 'FROM users '
                                 'WHERE user_id=? ',
                                 (user_id,
                                  ))
            return str(row.fetchall()[0])
        except Exception as e:
            logger.exception("Cannot find user in DB: %s", e.__repr__(), e.args)
            return "Гость"

    # Getting list of chats where text messaging is allowed
    def get_allowed_chat_text(self):
        logger.info("get_allowed_chat_text StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            resp = cursor.execute('SELECT chat_id, thread_id FROM chats WHERE allow_text=1')
            return [str(item[0]) + str(item[1]) for item in resp.fetchall()]
        except Exception as e:
            logger.exception("Cannot get allow text chats in database: %s", e.__repr__(), e.args)
            return []

    # Getting list of chats where voice messaging is allowed
    def get_allowed_chat_voice(self):
        logger.info("get_allowed_chat_voice StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            resp = cursor.execute('SELECT chat_id, thread_id FROM chats WHERE allow_voice=1')
            return [str(item[0]) + str(item[1]) for item in resp.fetchall()]
        except Exception as e:
            logger.exception("Cannot get allow text chats in database: %s", e.__repr__(), e.args)
            return []

    # Getting list of chats where send boobs is allowed
    def get_allowed_chat_boobs(self):
        logger.info("get_allowed_chat_boobs StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            resp = cursor.execute('SELECT chat_id, thread_id FROM chats WHERE allow_boobs=1')
            return [str(item[0]) + str(item[1]) for item in resp.fetchall()]
        except Exception as e:
            logger.exception("Cannot get allow text chats in database: %s", e.__repr__(), e.args)
            return []

    def get_allowed_command_users(self):
        logger.info("get_allowed_command_users StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            resp = cursor.execute('SELECT user_id FROM users WHERE allowed_commands=1')
            return [item[0] for item in resp.fetchall()]
        except Exception as e:
            logger.exception("Cannot get allow text chats in database: %s", e.__repr__(), e.args)
            return []

    def get_allowed_chat_commands(self):
        logger.info("get_allowed_chat_commands StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            resp = cursor.execute('SELECT chat_id, thread_id FROM chats WHERE allow_commands=1')
            return [str(item[0]) + str(item[1]) for item in resp.fetchall()]
        except Exception as e:
            logger.exception("Cannot get allow text chats in database: %s", e.__repr__(), e.args)
            return []

    def execute_command(self, command: str):
        logger.info("execute_command StoreHandler")
        cursor = self.connection_db.cursor()
        try:
            resp = cursor.execute(command)
            answer = '\n'.join(str(item) for item in resp.fetchall())
            if answer == "":
                return "Command success"
            return answer

        except Exception as e:
            logger.exception("Cannot execute command: %s" + command + "\n", e.__repr__(), e.args)
            return "Cannot execute command: " + command + "\n"
