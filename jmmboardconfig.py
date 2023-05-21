import asyncio
import logging
import traceback

import discord
from discord.ext import commands

#This is essentially a Jmmith-specific fork of Maximilian's config cog (cogs/config.py)

class settings(commands.Cog):
    '''Change Jmmith\'s settings'''
    def __init__(self, bot, load=False):
        self.bot = bot
        self.bot.settings = {}
        #mapping of setting name to description
        self.settingdescmapping = {"sort by jmms":"Sort 'leaderboard' by total golden jmms recieved", "show draobmmj":"Show draobmmj information in 'stats' and 'leaderboard'", "sort by jmmscore":"Sort 'leaderboard' by jmmscore", "sort by positivity":"Sort 'leaderboard' by percent of positive reactions on messages"}
        self.unusablewithmapping = {"sort by jmms":["sort by jmmscore", "sort by positivity"], "show draobmmj":None, "sort by jmmscore":["sort by jmms", "sort by positivity"], "sort by positivity":["sort by jmms", "sort by jmmscore"]}
        self.logger = logging.getLogger(name="cogs.config")
        self.unusablewithmessage = ""
        if load:
            asyncio.create_task(self.fill_settings_cache())
            self.logger.debug("Created a task for filling the setting cache")

    async def fill_settings_cache(self):
        '''Fills the settings cache with data'''
        self.logger.info("Filling settings cache...")
        await self.bot.wait_until_ready()
        try:
            data = self.bot.dbinst.exec_safe_query(self.bot.database, 'select * from jmmboardconfig', (), fetchall=True)
        except:
            traceback.print_exc()
            self.logger.warning('An error occurred while filling the setting cache, falling back to every setting disabled')
            data = []
            #if something went wrong, fall back to everything off to prevent console spam
            for name in list(self.settingdescmapping.keys()):
                for guild in self.bot.guilds:
                    data.append({'setting':name, 'guild_id':guild.id, 'enabled':False})
        else:
            if not data:
                self.logger.info("No settings are in the database for some reason. Creating an entry for each setting and falling back to every setting disabled")
                data = []
                for name in list(self.settingdescmapping.keys()):
                    self.bot.dbinst.exec_safe_query(self.bot.database, 'insert into jmmboardconfig values(%s, %s, %s)', (self.bot.guilds[0].id, name, False))
                    for guild in self.bot.guilds:
                        data.append({'setting':name, 'guild_id':guild.id, 'enabled':False})
        tempsettings = {}
        for setting in data:
            #initialize settings to blank dicts to prevent keyerrors
            tempsettings[setting['setting']] = {}
        for setting in data:
            for guild in self.bot.guilds:
                if setting['guild_id'] == guild.id:
                    if setting['enabled'] is not None:
                        tempsettings[setting['setting']][guild.id] = bool(setting['enabled'])
                    else:
                        tempsettings[setting['setting']][guild.id] = False
        self.bot.settings = tempsettings
        self.logger.info("Done filling settings cache.")
        
    async def update_setting(self, ctx, setting):
        '''Updates a setting's state in both the database and cache'''
        if not self.bot.dbinst.exec_safe_query(self.bot.database, "select * from jmmboardconfig where guild_id=%s", (ctx.guild.id)):
                self.bot.dbinst.exec_safe_query(self.bot.database, "insert into jmmboardconfig values(%s, %s, %s)", (ctx.guild.id, setting, True))
        else:
            self.bot.dbinst.exec_safe_query(self.bot.database, "update jmmboardconfig set enabled=%s where guild_id=%s and setting=%s", (not self.bot.settings[setting][ctx.guild.id], ctx.guild.id, setting))
        self.bot.settings[setting][ctx.guild.id] = not self.bot.settings[setting][ctx.guild.id]

    async def prepare_conflict_string(self, conflicts):
        '''Prepares a string of conflicts from a list (e.g `*show draobmmj* and *sort by jmms*`)'''
        q = "'"
        if not isinstance(conflicts, list):
            return f"{q}*{conflicts}*{q}"
        return f"{', '.join([f'{q}*{i}*{q}' for i in conflicts[:-1]])} and '*{conflicts[-1]}*'"

    async def resolve_conflicts(self, ctx, setting):
        '''Resolves conflicts between settings'''
        if isinstance(self.unusablewithmapping[setting], list):
            resolved = []
            for conflict in self.unusablewithmapping[setting]:
                if self.bot.settings[conflict][ctx.guild.id]:
                    await self.update_setting(ctx, conflict)
                    resolved.append(conflict)
        else:
            if self.unusablewithmapping[setting] and self.bot.settings[self.unusablewithmapping[setting]][ctx.guild.id]:
                await self.update_setting(ctx, self.unusablewithmapping[setting])
                resolved = self.unusablewithmapping[setting]
            else:
                self.unusablewithmessage = ""
                return
        if not resolved:
            self.unusablewithmessage = ""
            return
        if len(resolved) == 1:
            resolved = resolved[0]
        self.unusablewithmessage = f"**Automatically disabled** {await self.prepare_conflict_string(resolved)} due to a conflict."

    def is_enabled(self, setting, guild_id):
        '''Returns whether a setting is enabled'''
        try:
            return self.bot.settings[setting][guild_id]
        except KeyError:
            return False

    #customizable permissions when
    @commands.command()
    async def config(self, ctx, *, setting=None):
        '''Toggles the specified setting. Settings are off by default.'''
        if not setting:
            embed = discord.Embed(title="Settings", color=0xFDFE00)
            for key, value in list(self.bot.settings.items()):
                if ctx.guild.id in list(value.keys()):
                    unusablewith = self.unusablewithmapping[key]
                    if unusablewith:
                        unusablewithwarning = f"Cannot be enabled at the same time as {await self.prepare_conflict_string(unusablewith)}"
                    else:
                        unusablewithwarning = ""
                    embed.add_field(name=f"{discord.utils.remove_markdown(self.settingdescmapping[key].capitalize())} ({key})", value=f"{f'<:red_x:813135049083191307> Disabled' if not value[ctx.guild.id] else '✅ Enabled'}\n{unusablewithwarning} ", inline=True)
            embed.set_footer(text="If you want to toggle a setting, run this command again and specify the name of the setting. Setting names are shown above in parentheses. Settings that change the sorting of 'leaderboard' also affect 'stats'.")
            return await ctx.send(embed=embed)
        try:
            self.bot.settings[setting]
        except KeyError:
            return await ctx.send("That setting doesn't exist. Check the spelling.")
        try:
            #update setting state
            await self.update_setting(ctx, setting)
            #check for conflicts and resolve them
            await self.resolve_conflicts(ctx, setting)
        except:
            await self.bot.get_user(self.bot.owner_id).send(traceback.format_exc())
            return await ctx.send(f"Something went wrong while changing that setting. Try again in a moment. \nI've reported this error to my owner.")
        await ctx.send(embed=discord.Embed(title="Changes saved.", description=f"**{'Disabled' if not self.bot.settings[setting][ctx.guild.id] else 'Enabled'}** *{self.settingdescmapping[setting]}*.\n{self.unusablewithmessage}", color=0xFDFE00).set_footer(text=f"Send this command again to turn this back {'off' if self.bot.settings[setting][ctx.guild.id] else 'on'}."))

async def setup(bot):
    await bot.add_cog(settings(bot, True))

async def teardown(bot):
    await bot.remove_cog(settings(bot))
