import sqlite3

from logger import logger
from commands import command_module
from user import user
from irc import irc_client
from data.config import config

"""
The main bot class!

Instantiating this as an object will set up the IRC connection and make the bot
start listening for commands, et cetera
"""
class snekbot(irc_client):
    nickname_retries = 0
    nickname = ""

    def __init__(self):
        super().__init__()

        self.credits()
        self.db = sqlite3.connect(config.dbfile, check_same_thread=False)
        self.db.text_factory = str
        self.db.row_factory = sqlite3.Row
        self.load_modules()

    def load_modules(self, channel=False):
        """
        Load main modules

        :param channel:  Channel to send error message to if things go wrong - can also be a nickname
        """
        self.command_module = command_module(self)
        self.logger = logger(self)

    def process(self, msg, sender):
        """
        Process an IRC update

        This is the heart of the bot - depending on the command that was received, we call the appropriate methods
        to process it.

        :param msg:  Message that was received
        :param sender:  Hostname of sender
        :return:
        """
        recv_user = user(self, sender)
        if not recv_user.is_valid():
            self.on_servermsg(msg)
            return False

        message = " ".join(msg[3:])[1:]

        if msg[1] == "PRIVMSG":
            channel = msg[2]
            self.on_privmsg(message, channel, recv_user)
        elif msg[1] == "NOTICE":
            self.on_notice(message, recv_user)
        elif msg[1] == "NICK":
            self.on_nick(msg[2][1:], recv_user)
        elif msg[1] == "JOIN":
            channel = msg[2]
            self.on_join(channel, recv_user)
        elif msg[1] == "PART":
            channel = msg[2]
            self.on_part(message, channel, recv_user)
        elif msg[1] == "KICK":
            channel = msg[2]
            self.on_kick(msg[3] + " " + " ".join(msg[4:])[1:], channel, recv_user)
        elif msg[1] == "QUIT":
            self.on_quit(" ".join(msg[2:])[1:], recv_user)
        elif msg[1] == "TOPIC":
            channel = msg[2]
            self.on_topic(message, channel, recv_user)
        elif msg[1] == "MODE":
            self.on_mode(message, recv_user)
        elif self.debugmode == "verbose":
            self.debug("Unrecognized command %s from %s" % (msg[1], recv_user.nickname))

    def on_privmsg(self, msg, channel, sender):
        """
        Handle PRIVMSG command

        These are not just private messages, but also anything said inside a channel.

        :param msg:  Message
        :param channel:  Channel or nickname
        :param sender:  Who sent the message (user object)
        :return:
        """
        self.logger.log(msg, channel, sender)

        if channel == self.nickname:
            channel = sender.info("lastnick")

        self.command_module.process(msg, channel, sender)
        self.debug("[" + channel.rjust(14) + "] " + sender.nickname.rjust(14) + ": " + msg)

    def on_servermsg(self, msg):
        """
        Handle server messages

        These use numeric codes!
        :param msg:  Message that was sent
        """
        msgcode = msg[1]

        if msgcode == "376":  # log on
            self.nick(config.nickname)
            for channel in config.preferredchannels:
                self.join(channel)

        elif msgcode == "311":  # whois reply
            hostmask = "%s!%s@%s" % (msg[3], msg[4], msg[5])

            # this registers the user in the database
            user(self, hostmask)

        elif msgcode == "353":  # NAMES reply
            nicknames = msg[5:]
            for nickname in nicknames:
                nickname = nickname.replace("@", "").replace("+", "")
                self.sendCmd("WHOIS %s" % nickname)

        elif msgcode == "433":  # nickname already in use
            if self.nickname_retries == 0:
                self.sendCmd("NICK :%s" % config.altnickname)
                self.nickname = config.altnickname
                self.nickname_retries += 1
            else:
                lame_nickname = config.altnickname + str(self.nickname_retries)
                self.sendCmd("NICK :%s" % lame_nickname)
                self.nickname = lame_nickname
                self.nickname_retries += 1

    def on_notice(self, msg, sender):
        """
        Handle notices

        Just debug them... nothing to process for now

        :param msg:  Message
        :param sender:  Who sent the message (user object)
        :return:
        """
        # if sender.level == user.LEVEL_SERVICE and sender.nickname == "NickServ":
        if sender.nickname == "NickServ":
            if config.nickserv_curse in msg:
                if config.nickserv_password != "" and self.nickname == config.nickserv_nickname:  # logon
                    self.sendCmd("PRIVMSG NickServ :IDENTIFY %s" % config.nickserv_password)
            elif config.nickserv_magic in msg:
                # we're logged in
                pass

        self.debug("[" + str("NOTICE").rjust(14) + "] " + sender.nickname.rjust(14) + ": " + msg)

    def on_topic(self, msg, channel, sender):
        """
        Log topic changes

        :param msg:  New topic
        :param channel:  Channel
        :param sender:  Who set the topic
        """
        self.logger.log(msg, channel, sender, "TOPIC")

    def on_nick(self, msg, sender):
        """
        Handle nickname changes

        :param msg:  New nickname
        :param sender:  Who changed their nickname (user object)
        """
        sender.rename(msg)

        self.logger.log(msg, "", sender, "NICK")

    def on_join(self, channel, sender):
        """
        Handle people joining the channel

        Tries to auto-op any bot admins

        :param channel:  Channel that was joined
        :param sender:  Who joined (user object)
        """
        if sender.level >= user.LEVEL_ADMIN:
            sender.add_mode(channel, "o")

        self.logger.log("", channel, sender, "JOIN")

    def on_quit(self, msg, sender):
        """
        Log people quitting IRC

        :param msg:  Quit message
        :param sender:  Who quit (user object)
        :return:
        """
        self.logger.log(msg, "", sender, "QUIT")

    def on_part(self, msg, channel, sender):
        """
        Log people departing a channel

        :param msg:  Part message
        :param channel:  Channel that was parted
        :param sender:  Who parted (user object)
        :return:
        """
        self.logger.log(msg, channel, sender, "PART")

    def on_kick(self, msg, channel, sender):
        """
        Log people being kicked from a channel

        :param msg:  Kick message
        :param channel:  Channel that person was kicked from
        :param sender:  Who parted (user object)
        """
        self.logger.log(msg, channel, sender, "KICK")

    def on_mode(selfself, msg, sender):
        """
        Log mode changes

        :param msg:  Mode update
        :param sender:  Who parted (user object)
        """
        pass

    def die(self, quitmsg="brb!"):
        """
        Quit IRC

        :param quitmsg:  Quit message
        """
        self.db.close()
        self.alive = False
        self.sendCmd("QUIT :%s" % quitmsg)

    def credits(self):
        """
        Print credits to console
        """
        print("+------------------------------------------------+")
        print("| ssssssssssssssssssssssssssssssssssssssssssssss |")
        print("|                        __   __          __     |")
        print("|       _________  ___  / /__/ /_  ____  / /_    |")
        print("|      / ___/ __ \/ _ \/ //_/ __ \/ __ \/ __/    |")
        print("|     (__  ) / / /  __/ ,< / /_/ / /_/ / /_      |")
        print("|    /____/_/ /_/\___/_/|_/_.___/\____/\__/      |")
        print("|                                                |")
        print("| ssssssssssssssssssssssssssssssssssss v2.0 ssss |")
        print("+------------------------------------------------+")

