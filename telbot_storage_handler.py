# telbot_storage_handler module
import sqlite3
import logging
import sys
import telebot
import re
from pathlib import Path


# Class for handling with bot database users, messages and other
class StorageHandler:
    # Out connection to the sqlite db
    connection_db = None

    # db_pass - pass to out database, we'll check if it's exists, and create if it's not
    def __init__(self, db_pass: Path):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        try:
            db_pass.resolve(strict=True)
        except FileNotFoundError:
            logging.debug("Database not found, trying to create a new one.")

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
                     chat_name text)
                     ''')
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS text_messages 
                    (message_id integer PRIMARY KEY,
                     date integer,
                     from_user_id DOUBLE,
                     chat_id DOUBLE,
                     reply_to_message_id integer,
                     message_text text)
                    ''')
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS chats 
                    (chat_id DOUBLE primary key,
                     used_model text,
                     system_message text)
                    ''')
            self.connection_db.commit()
        except Exception as e:
            logging.debug("Error when creating/connecting database: ", e.__repr__(), e.args)
            pass
        else:
            logging.debug("DB " + str(db_pass) + " connection success.")

    # Closing connection for no memory licks
    def __del__(self):
        self.connection_db.close()

    # store info about user, chat and message
    def logtextmessage(self, message: telebot.types.Message):
        # adding user info if new
        answer = ""
        exist_users = None
        cursor = self.connection_db.cursor()
        try:
            exist_users = cursor.execute('SELECT * FROM users WHERE user_id=?', (message.from_user.id,))
        except Exception as e:
            logging.debug("Cannot SELECT user_id from database: ", e.__repr__(), e.args)
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
                               'chat_name) '
                               'VALUES (?, ?, ?, ?, ?)',
                               (message.from_user.id,
                                message.from_user.first_name,
                                message.from_user.last_name,
                                message.from_user.username,
                                chat_name))
                self.connection_db.commit()
                logging.debug("New user " + str(message.from_user.id) + " added")
                answer = ("New user: \n" + str(message.from_user.id) + "\n" + chat_name)
            except Exception as e:
                logging.debug("Cannot INSERT user_id to database: ", e.__repr__(), e.args)
        else:
            logging.debug("User " + str(message.from_user.id) + " exists")
        # adding chat info if new
        exist_chats = None
        try:
            exist_chats = cursor.execute('SELECT * FROM chats WHERE chat_id=?', (message.chat.id,))
        except Exception as e:
            logging.debug("Cannot SELECT chat_id from database: ", e.__repr__(), e.args)
            pass
        if exist_chats.fetchone() is None:
            try:
                cursor.execute('INSERT INTO chats '
                               '(chat_id, '
                               'used_model, '
                               'system_message) '
                               'VALUES (?, ?, ?)',
                               (message.chat.id,
                                "default",
                                "default"))
                self.connection_db.commit()
                logging.debug("New chat " + str(message.chat.id) + " added")
                answer = ("New chat: \n" + str(message.chat.id))
            except Exception as e:
                logging.debug("Cannot INSERT chat_id to database: ", e.__repr__(), e.args)
        else:
            logging.debug("Chat " + str(message.chat.id) + " exists")
        # adding message info
        rep_mes_id = 0
        if message.reply_to_message is not None:
            rep_mes_id = message.reply_to_message.id
        try:
            cursor.execute('INSERT INTO text_messages '
                           '(message_id, '
                           'date, '
                           'from_user_id, '
                           'chat_id, '
                           'reply_to_message_id, '
                           'message_text) '
                           'VALUES (?,?,?,?,?,?)',
                           (message.id,
                            message.date,
                            message.from_user.id,
                            message.chat.id,
                            rep_mes_id,
                            message.text))
            self.connection_db.commit()
            logging.debug("New messaage ", message.id, " added")
        except Exception as e:
            logging.debug("Cannot INSERT message to database: ", e.__repr__(), e.args)
        return answer

    def getmessagegptthread(self, message: telebot.types.Message, bot_id: str, sys_mes: str):
        dialog = [
            {
                "role": "user",
                "content": self.getchatnamebyid(message.from_user.id) + ": " + message.text,
            }
        ]

        cursor = self.connection_db.cursor()
        if message.reply_to_message is not None:
            prev_msg_id = message.reply_to_message.id
            counter = 10
            while prev_msg_id != 0 and counter > 0:
                try:
                    prev_msg = cursor.execute('SELECT reply_to_message_id,'
                                              ' message_text, '
                                              'from_user_id '
                                              'FROM text_messages '
                                              'WHERE chat_id=? '
                                              'AND message_id=?',
                                              (message.chat.id,
                                               prev_msg_id,))
                    rows = prev_msg.fetchall()
                except Exception as e:
                    logging.debug("No such message in stored dialogs: ", e.__repr__(), e.args)

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

        chat_sys_message = cursor.execute('SELECT system_message FROM chats WHERE chat_id=?',
                                          (message.chat.id,))
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
        if "@бармен" in message.text.lower() or "@bartender_kabak_bot" in message.text.lower():
            return True
        if message.reply_to_message is not None:
            if message.reply_to_message.from_user.id == int(bot_id):
                return True
        return False

    def getchatnamebymessage(self, message: telebot.types.Message):
        cursor = self.connection_db.cursor()
        try:
            row = cursor.execute('SELECT chat_name '
                                 'FROM users '
                                 'WHERE user_id=? ',
                                 (message.from_user.id,
                                  ))
            return str(row.fetchall()[0])
        except Exception as e:
            logging.debug("Cannot find user in DB: ", e.__repr__(), e.args)
            return "Гость"

    def getchatnamebyid(self, user_id: int):
        cursor = self.connection_db.cursor()
        try:
            row = cursor.execute('SELECT chat_name '
                                 'FROM users '
                                 'WHERE user_id=? ',
                                 (user_id,
                                  ))
            return str(row.fetchall()[0])
        except Exception as e:
            logging.debug("Cannot find user in DB: ", e.__repr__(), e.args)
            return "Гость"

    def command_set_chat_system_message(self, message: telebot.types.Message):
        chat_id = message.chat.id
        sys_message = "default"
        cursor = self.connection_db.cursor()
        try:
            act_chat = re.search("(?<=chat=)(.*)(?=message=)", message.text).group().strip()
            if act_chat != "this":
                chat_id = act_chat
            sys_message = re.search(r"(?<=message=).*", message.text).group().strip()
        except Exception as e:
            logging.debug("Regular expression bug: ", e.__repr__(), e.args)
            return "regexp bug"

        try:
            exist_chats = cursor.execute('SELECT * FROM chats WHERE chat_id=?', (chat_id, ))
        except Exception as e:
            logging.debug("Cannot SELECT chat_id from database: ", e.__repr__(), e.args)
            return "error finding chat"
        if exist_chats.fetchone() is None:
            return "chat does not exists"
        else:
            try:
                cursor.execute('UPDATE chats '
                               'SET system_message=?'
                               'WHERE chat_id=?',
                               (sys_message,
                                chat_id,
                                ))
                return "System message set: " + sys_message
            except Exception as e:
                logging.debug("Cannot UPDATE system_message in database: ", e.__repr__(), e.args)

