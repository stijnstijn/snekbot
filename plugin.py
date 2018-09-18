import inspect
import abc

class base_plugin:
    """
    Plugin base class. All plugins classes need to extend from this class to function.
    """
    cmd = None

    def __init__(self, cmd):
        """
        :param commands.command_module cmd:  Command module
        """
        self.cmd = cmd


class admin_plugin(base_plugin):
    """
    Admin plugin base class.

    This allows child classes to implement an `admin_command` method rather than the normal `command` method; it
    functions the same as the `command` method, but is only called if the user's level is at least equal to
    `LEVEL_ADMIN`.
    """
    def command(self, message, channel, user):
        """Checks if the user has a sufficient user level, and calls the `admin_command` class method, if it exists.

        :param string message:  Full command message
        :param string channel:  Channel the command was given on (can also be a nickname)
        :param user.user user:  User that gave the command
        :return bool: `True` if the command was valid, `False` if it could not be processed
        """
        if user.level < user.LEVEL_ADMIN:
            return False

        if getattr(self, "admin_command") and not inspect.isabstract(self.admin_command):
            return self.admin_command(message, channel, user)
        else:
            return False

    @abc.abstractmethod
    def admin_command(self, message, channel, user):
        """
        This method will be called if the user is an admin.

        :param string message:  Full command message
        :param string channel:  Channel the command was given on (can also be a nickname)
        :param user.user user:  User that gave the command
        :return bool: `True` if the command was valid, `False` if it could not be processed
        """
        return False
