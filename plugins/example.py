from plugin import base_plugin


class example(base_plugin):
    """
    Example IRC bot plugin

    The name of the class is the name of the command. So in this case, the command
    `!example` is added to the bot by this file. A plugin file can contain multiple
    commands.
    """

    def command(self, message, channel, user):
        """Respond to the '!example' command

        Echoes back what the user said. The `command` method is called when the command is
        given by a user.

        :param string message: Full command message
        :param string channel: Channel the command was given on
        :param user.user user: User object
        :return:
        """
        self.cmd.irc.sendMsg(channel, "Your nickname is %s and you said: %s" % (user.nickname, message))
