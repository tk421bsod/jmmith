# jmmith
Jmmith is a starboard bot I made for a friend's server.

## selfhosting
I'm not sure why anyone would want to run their own instance.
For now, Jmmith is **not** designed to be selfhostable. It requires multiple custom emoji and a specific channel to send starboard messages in.
If you're really determined, take a look at the add_to_jmmboard method in main.py. You'll need to replace the id for `starboardchannel` and the different custom emojis with the correct ones.
After doing that, run setup.sh and follow the prompts.
I'm working on building proper support for selfhosting -- please be patient as I'm currently busy with a lot of stuff, both for school and other projects.
