import sqlite3
import time

from data.config import config


class logger:
    def __init__(self, irc):
        self.irc = irc
        self.dbconn = self.irc.db
        self.database_setup()

    def database_setup(self):
        """
        Make sure we have a database connection to work with, and create user table if it does not exist yet
        """
        self.db = self.dbconn.cursor()

        try:
            self.db.execute("SELECT * FROM log LIMIT 1")
        except sqlite3.OperationalError:
            self.db.execute(
                "CREATE TABLE log (hostname TEXT, nickname TEXT, channel TEXT, server TEXT, time INT, type TEXT, message TEXT)")
            self.dbconn.commit()

    def log(self, message, channel, user, msgtype="text"):
        self.db.execute(
            "INSERT INTO log (hostname, nickname, channel, server, time, type, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.hostname, user.nickname, channel, config.host, int(time.time()), msgtype, message))
        self.dbconn.commit()
