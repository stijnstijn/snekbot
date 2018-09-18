import importlib
import inspect
import glob
import sys
import gc

import os.path as path
from data.config import config


class command_module:
    """
    Command module

    Interprets commands and calls the appropriate methods to process and reply to them
    """
    commands = []
    plugins = {}

    def __init__(self, irc):
        """
        Set up command module

        :param irc_client irc:  IRC interface
        """
        self.irc = irc
        self.lastcommand = ""

        self.setup_database()
        self.load_plugins()

    def setup_database(self):
        """
        Set up database connection

        We have no table to set up here, so not much to do
        """
        self.dbconn = self.irc.db
        self.db = self.dbconn.cursor()

    def load_plugins(self):
        """
        Load plugins

        Plugins are python files in the `plugins/` folder. Any classes defined in those python files
        that implement a "command" method are registered as plugins. They can then be called by users
        as a chat command.

        For example, if there's a plugin.py which contains a class named "hello" that has a `command` method, that
        class will be instantiated, with a database cursor as the first constructor argument, and its `command()` method
        called with `message`, `channel` and `user` as arguments when someone says "!hello".
        """
        if self.plugins != {}:
            self.plugins = {}
            gc.collect()

        # get all python files in the plugin folder
        plugin_paths = glob.glob(path.dirname(__file__) + "/plugins/*.py")
        plugin_files = [path.basename(file) for file in plugin_paths if path.isfile(file) is True]

        for plugin_file in plugin_files:
            # try to force reloading
            module_name = "plugins." + plugin_file[:-3]
            if module_name in sys.modules:
                del sys.modules[module_name]
                gc.collect()

            # import the file and see if it has a class in it
            try:
                module = importlib.import_module(module_name)
                importlib.reload(module)
            except ModuleNotFoundError:
                continue

            plugin_classes = inspect.getmembers(module, inspect.isclass)
            for plugin_class in plugin_classes:
                # check if class has a "command" method
                plugin_caller = getattr(plugin_class[1], "command", None)

                # add that class as a hook that can be called!
                if not inspect.isabstract(plugin_class[1]) and callable(plugin_caller):
                    self.plugins[plugin_class[0]] = plugin_class[1](self)

    def process(self, message, channel, user):
        """
        Process user input

        Pretty much the most important method! If the method called for the command returns `True`, the
        command will be saved as the last succesful command, and may be called again easily via `!2`.

        :param string message:  The message to process
        :param string channel:  The channel the message was said on
        :param user user:  User object
        """
        command = message.split(" ")[0][len(config.command_prefix):]
        if len(message) > 0 and message[:len(config.command_prefix)] == config.command_prefix:
            done = False

            if command == "2" and self.lastcommand != "":
                self.process(self.lastcommand, channel, user)
            elif command in self.plugins:
                # plugin commands (could be anything!)
                done = self.plugins[command].command(message, channel, user)

            if done:
                self.lastcommand = message
