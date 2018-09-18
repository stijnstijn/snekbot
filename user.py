import sqlite3
import time


class user:
    """
    Class representing an IRC user

    These objects are not persistent - that is, anytime something is said a new
    user object is instantiated for the user that said it. The object rather is
    an interface with the database, where various bits of user data are stored.

    Users are identified by their full hostname (i.e. realname@hostname.com)
    """
    LEVEL_BANNED = 0
    LEVEL_USER = 1
    LEVEL_SERVICE = 2
    LEVEL_ADMIN = 5

    nickname = ""
    hostname = ""
    ident = ""

    data = {}
    init = False

    def __init__(self, irc, ident=""):
        """
        Set up user object

        :param irc:  IRC connection
        :param ident:  Full hostname for user
        """
        self.irc = irc
        self.dbconn = irc.db
        self.db = None  # will be set up later

        if ident != "" and "@" not in ident:  # no @ = server message
            return

        self.database_setup()
        self.setup(ident)

    def database_setup(self):
        """
        Make sure we have a database connection to work with, and create user table if it does not exist yet
        """
        self.db = self.dbconn.cursor()

        try:
            self.db.execute("SELECT * FROM user LIMIT 1")
        except sqlite3.OperationalError:
            self.db.execute(
                "CREATE TABLE user (hostname TEXT UNIQUE, nickname TEXT, server TEXT, level INT, activity INT)")
            self.dbconn.commit()

    def setup(self, ident=""):
        """
        Get database ID for current user

        If the user (identified by their hostname) is not known, add to database

        :param ident: Full hostname for user
        :return: Database ID
        """
        if self.data == {}:
            if ident != "":
                address = ident.split("!")
                self.hostname = address[1]
                self.nickname = address[0]
                self.ident = ident

            dbuser = self.db.execute("SELECT * FROM user WHERE hostname = ?", (self.hostname,)).fetchone()

            if not dbuser:
                self.db.execute("INSERT INTO user (nickname, hostname, level) VALUES (?, ?, ?)",
                                (self.nickname, self.hostname, self.LEVEL_USER))
                self.dbconn.commit()

                self.db.execute("SELECT * FROM user WHERE hostname = ?", (self.hostname,))
                dbuser = self.db.fetchone()

            else:
                self.db.execute("UPDATE user SET nickname = ?, activity = ? WHERE hostname = ?",
                                (self.nickname, time.time(), dbuser[0]))
                self.dbconn.commit()

            self.data = dict(dbuser)
            self.level = int(self.info("level"))
            self.init = True

    def is_valid(self):
        """
        Check if this is a "real" user

        This check only fails if the "user" is actually the server sending us things, or in case of some kind of
        database failure.

        :return:  Whether this is a valid object representing a user
        """
        return self.init

    def rename(self, nickname):
        """
        Set new nickname for user

        :param nickname:  New nickname
        """
        self.nickname = nickname
        self.set_info("nickname", nickname)

    def info(self, field):
        """
        Get user info

        :param field:  User info to get
        :return: The value, or `False` if the field does not exist.
        """
        try:
            index = self.data[field]
        except KeyError:
            return False

        return self.data[field]

    def set_info(self, field, value):
        """
        Set user info

        :param field:
        :param value:
        :return:
        """
        current = self.info(field)
        if not current:
            return False

        if value == current:
            # no need to update
            return True

        self.data[field] = value

        self.db.execute("UPDATE user SET " + field + " = ? WHERE hostname = ?", (value, self.hostname))
        return self.dbconn.commit()

    def add_mode(self, channel, mode):
        """
        Try to set a new user mode

        :param channel: Channel to try and set the mode on
        :param mode: Mode to set
        """
        self.irc.sendCmd("MODE %s +%s %s" % (channel, mode, self.nickname))

    def remove_mode(self, channel, mode):
        """
        Try to remove a user mode

        :param channel: Channel to try and set the mode on
        :param mode: Mode to set
        """
        self.irc.sendCmd("MODE %s -%s %s" % (channel, mode, self.nickname))

    def debug(self, msg):
        """
        Log debug message

        :param msg:  Message to log
        """
        print("[" + str("USER").rjust(14) + "] %s" % msg)
