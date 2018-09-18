import time
import socket

from data.config import config


class irc_client:
    ircbuffer = ""
    ircsocket = ""
    alive = False
    channels = []
    debugmode = "verbose"

    def __init__(self):
        self.ircsocket = socket.socket()
        self.ircsocket.connect((config.host, config.port))
        self.alive = True
        time.sleep(2)
        self.ident()

    def nick(self, nickname=False):
        """
        Set our nickname

        Thin wrapper around sendCmd() that send the proper NICK command

        :param nickname:
        """
        if not nickname:
            nickname = config.nickname
        self.sendCmd("NICK %s\r\n" % nickname)

    def ident(self, identid=False, realname=False):
        """
        Identify ourselves to the IRC server

        :param identid:  Identity
        :param realname:  Real name to send
        """
        if not identid:
            identid = config.identid
        if not realname:
            realname = config.realname

        self.nick()
        self.sendCmd("USER %s %s snekbot :%s\r\n" % (identid, config.host, realname))
        self.nickname = config.nickname

    def join(self, channel):
        """
        Join a channel, but only if we're not in it already

        :param channel:  Channel to join
        """
        if channel not in self.channels:
            self.sendCmd("JOIN %s\r\n" % channel)
            self.channels += [channel]

    def part(self, channel=False):
        """
        Depart a channel, or all channels

        :param channel:  Channel to depart - if left empty, depart all channels
        """
        if not channel:
            for channel in self.channels:
                self.ircsocket.send("PART %s\r\n" % channel)
        else:
            self.ircsocket.send("PART %s\r\n" % channel)
            try:
                self.channels.remove(channel)
            except ValueError:
                pass

    def listen(self):
        """
        Main loop
        """
        while self.alive:
            try:
                self.ircbuffer = self.ircbuffer + self.ircsocket.recv(1024).decode("ascii")
            except socket.error as message:
                self.debug("/!\ Socket error '%s', halting script" % message)
                self.die()

            lines = self.ircbuffer.split("\n")
            self.ircbuffer = lines.pop()

            for line in lines:
                line = line.strip().split(" ")

                if line[0][0] == ":":
                    sender = line[0][1:]
                    try:
                        self.process(line, sender)
                    except Exception as error_message:
                        # keep the bot running at all costs!!
                        self.debug("Error during processing: %s" % error_message)
                elif line[0] == "PING":
                    line[1] = line[1][1:]
                    self.sendCmd("PONG %s\r\n" % line[1])
                elif line[0] == "ERROR":
                    msg = " ".join(line[1:])[1:]
                    self.debug("/!\ Server returned error message '%s', halting script" % msg)
                    if "Ping timeout" in msg or "Ping Timeout" in msg:
                        time.sleep(5)
                        self.__init__()
                    elif "Closing link" in msg:
                        time.sleep(5)
                        self.__init__()
                    else:
                        self.die()

        # hopefully we never get out of the above while loop - if we do, it's over
        self.debug("Disconnected from server. Bye!")

    def debug(self, msg):
        """
        Print debug message in console

        :param msg:  Debug message
        :return:
        """
        print("%s" % str(msg).strip())

    def process(self, msg, sender):
        """
        Dummy function - this should not be called, but just in case the server uses some esoteric commands...

        :param msg:  Message to process
        :param sender:  User object of sender
        :return:
        """
        print("Received message %s from %s. processing method not implemented." % (msg, sender))

    def sendCmd(self, cmd):
        """
        Send raw IRC command

        :param cmd:  Command to send
        """
        cmd = cmd.strip() + "\r\n"
        try:
            self.ircsocket.send(cmd.encode("ascii"))
        except UnicodeEncodeError:
            self.debug(">>> Could not send command, invalid ascii characters: %s" % cmd)

    def sendMsg(self, channel, msg):
        """
        Send message to channel or user

        :param channel:  Channel to send to - can also be a username
        :param msg:  Message to send
        """
        self.sendCmd("PRIVMSG %s :%s" % (channel, msg))

    def sendErrorMsg(self, channel, msg):
        """
        Send error message

        Thin wrapper around sendMsg() - just prefixes it with an indication that there's an error

        :param channel:  Channel to send to - can also be a username
        :param msg:  Error message to send
        :return:
        """
        self.sendMsg(channel, "GURU MEDITATION: %s" % msg)

    def die(self):
        """
        End main loop, wrap up connection

        We can suffice by simply setting the variable the main loop relies on to False
        """
        self.alive = False
