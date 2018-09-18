
                               __   __          __     
              _________  ___  / /__/ /_  ____  / /_    
             / ___/ __ \/ _ \/ //_/ __ \/ __ \/ __/    
            (__  ) / / /  __/ ,< / /_/ / /_/ / /_      
           /____/_/ /_/\___/_/|_/_.___/\____/\__/      
                                                       
                                                       v2.0
                                                        
# Snekbot 🐍
Snekbot is an IRC bot, or rather an IRC bot framework. It has
no dependencies, apart from the Python 3 standard library.

Run it this way:

`python3 run.py`

## Configuration
The bot can be configured using `data/config.py`. Most options 
are self-explanatory, but these may need some details:

- `nickserv_curse`: If a NOTICE containing this phrase is 
  received from a user with the name `NickServ` and a user
  level (see below) of `LEVEL_ADMIN`, the bot will try to
  identify itself if a password is known.
- `nickserv_magic`: If a phrase containing this phrase is
  received from the same NickServ, this will be interpreted
  as having succesfully logged in.
- `command_prefix`: What goes in front of commands. For
  example, if this is `!`, and a command `seen` is known,
  the bot will recognize a message beginning with `!seen`
  as an invocation of that command.
  
## Plugins/adding commands
You can add bot commands by adding python files to the
`plugins` folder. See `example.py` in that folder for an
example.

The admin command `!reload` (one of the only commands
available by default) reloads plugins and can be used to
add commands while the bot is running.

## User levels
People are assigned user levels by the bot. Everyone has the
level `LEVEL_USER` by default. There are two other levels 
that may be useful:

- `LEVEL_ADMIN`: These people can use admin commands
  (plugins built on top of the `admin_command` class).
- `LEVEL_SERVICE`: These users are recognized as IRC services.
  Currently this is only useful for NickServ; a user will
  only be recognized as the "true" NickServ if they have this
  level.
  
It is recommended that you add an admin command through which
people may be assigned a new user level. There is currently
no way to create the "first admin" through the bot; you'll have
to manually edit `data/snekbot.db` for that. Simply change
the value of the `level` column of the appropriate person to
`5`.

## Contact
By [Stijn](https://www.github.com/stijnstijn). 
  
