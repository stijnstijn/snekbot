import importlib
import sys

from plugin import admin_plugin


class reload(admin_plugin):
    def admin_command(self, message, channel, user):
        self.cmd.load_plugins()
        importlib.reload(sys.modules["config"])  # does this work?
