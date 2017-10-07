# GMR Client Py

#### Cross-platform (I hope so) GMR (http://multiplayerrobot.com) client written in Python.

I simply had trouble finding a GMR client that works on Linux, so I've written one myself.

#### Killer feature (On Linux, at least):

* It can not only automatically download save file and start Civ5, but **also load the save automatically** once Civ5 is done starting up.
* After you've finished your turn, it can **automatically save the game** before closing Civ5 and submitting your turn.

It does that by manipulating LUA scripts that control Civ5's UI behavior. If it gets stuck like that, just run `./fix_autoload.py`.

For now the only frontend is CLI. Start it as `./gmr_cli.py AUTH_KEY` for the first time.
After that, drop the key. If needed, change it in `~/.local/share/gmr_client_py/config`.

### Notes

All the heavy lifting is done by `gmr_lib.py`. Frontends only implement UI.

The official API documentation (http://multiplayerrobot.com/About/Api) does not seem to be quite correct
(I didn't manage to upload save game using it at least), so I had to look through HTTP traffic of the official client.
I mostly mimic its behavior, except I cut out some unnecessary and/or irrelevant bits.

I use Python3 but it shoud brobably work with Python2 too.
