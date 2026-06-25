"""App-level command registry.

Frappe's bench helper imports ``<app>.commands`` and reads the module-level
``commands`` list to register CLI commands. We aggregate per-module commands here.
"""

from awbix.project.commands import commands as project_commands

commands = [*project_commands]
