import discord
from discord.ext import commands
import contextlib

class info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.AWARDS = {1:'<:gold_bimm:896479698878615552> (1)', 2:':second_place:', 3:':third_place:'}
    
    async def convert_to_member(self, ctx, arg):
        try:
            return await commands.MemberConverter().convert(ctx, arg)
        except commands.errors.MemberNotFound:
            return None

    async def get_jmms(self):
        jmmmapping = {}
        for message in self.bot.messages:
            try:
                jmmmapping[str(message.author)]
            except KeyError:
                jmmmapping[str(message.author)] = {'reactions':0, 'messages':0, 'draobmmjmessages':0, 'draobmmjreactions':0, 'jmmscore':0, 'positivity':0}
            for i in message.reactions:
                if hasattr(i.emoji, 'id'):
                    if i.emoji.id == 774445538409054218:
                        if i.count >= 4:
                            jmmmapping[str(message.author)]['messages'] += 1
                        jmmmapping[str(message.author)]['reactions'] += i.count
                    elif i.emoji.id == 776612785647910933:
                        if i.count >= 3:
                            jmmmapping[str(message.author)]['draobmmjmessages'] += 1
                        jmmmapping[str(message.author)]['draobmmjreactions'] += i.count
        for i in list(jmmmapping.keys()):
            jmmmapping[i]['jmmscore'] = jmmmapping[i]['reactions']-jmmmapping[i]['draobmmjreactions']
            if jmmmapping[i]['reactions'] == 0:
                jmmmapping[i]['positivity'] = 0
            else:
                jmmmapping[i]['positivity'] = round((jmmmapping[i]['reactions']/(jmmmapping[i]['reactions']+jmmmapping[i]['draobmmjreactions']))*100,1)
        return jmmmapping

    def get_messages(self, m):
        return m[1]['messages']
    
    def get_reactions(self, m):
        return m[1]['reactions']

    def get_jmmscore(self, m):
        return m[1]['jmmscore']
    
    def get_positivity(self, m):
        return m[1]['positivity']

    def get_award(self, num):
        '''Gets the award corresponding to a place on the leaderboard'''
        try:
            award = self.bot.AWARDS[num+1]
        except KeyError:
            award = num+1
        return award

    def is_enabled(self, setting, guild_id):
        '''Returns whether a setting is enabled'''
        try:
            return self.bot.settings[setting][guild_id]
        except KeyError:
            return False

    def get_key(self, guild_id):
        '''Returns a key to sort jmmmapping by. The key returned is determined by what settings are enabled.'''
        if self.is_enabled('sort by jmms', guild_id):
            return self.get_reactions
        elif self.is_enabled('sort by jmmscore', guild_id):
            return self.get_jmmscore
        elif self.is_enabled('sort by positivity', guild_id):
            return self.get_positivity
        return self.get_messages

    @commands.command(hidden=True, aliases=['leaderboard', 'jmmleaderboards'])
    async def jmmleaderboard(self, ctx, limit=10):
        if limit < 2:
            return await ctx.send("I can't show less than 2 people on the leaderboard. sorry.")
        if self.bot.cache_lock.locked() and self.bot.initial_caching == True:
            return await ctx.send(f"The message cache isn't ready yet. Try again later. \n{self.bot.itercount}/{len(self.bot.guilds[0].text_channels)+len(self.bot.guilds[0].threads)} channels have been cached.")
        key = self.get_key(ctx.guild.id)
        jmmmapping = await self.get_jmms()
        desc = ""
        for count, value in enumerate(sorted(list(jmmmapping.items()), key=lambda m: (key(m), self.get_messages(m)), reverse=True)[:limit]):
            award = self.get_award(count)
            if not self.is_enabled('show draobmmj', ctx.guild.id):
                desc += f"{award}: {value[0]} ({value[1]['messages']} {'messages' if value[1]['messages'] != 1 else 'message'} on the jmmboard, {value[1]['reactions']} golden {'jmms' if value[1]['reactions'] != 1 else 'jmm'} recieved, a jmmscore of {value[1]['reactions']-value[1]['draobmmjreactions']}, and {value[1]['positivity']}% positive reactions)\n"
            else:
                desc += f"{award}: {value[0]} ({value[1]['messages']} messages on the jmmboard, {value[1]['reactions']} golden jmms recieved, {value[1]['draobmmjmessages']} messages on the draobmmj, {value[1]['draobmmjreactions']} nogoldjmms recieved, a jmmscore of {value[1]['reactions']-value[1]['draobmmjreactions']}, and {value[1]['positivity']}% positive reactions)\n"
        leaderboard = discord.Embed(title="Jmmboard leaderboard:", description=desc, color=0xFDFE00)
        await ctx.send(embed=leaderboard)

    @commands.command(hidden=True, aliases=['stats', 'jmmboardstats'])
    async def jmmstats(self, ctx, *, user=None):
        if self.bot.cache_lock.locked() and self.bot.initial_caching == True:
            return await ctx.send(f"The message cache isn't ready yet. Try again later. \n{self.bot.itercount}/{len(self.bot.guilds[0].text_channels)+len(self.bot.guilds[0].threads)} channels have been cached.")
        if user:
            ret = await self.convert_to_member(ctx, user)
            if not ret:
                return await ctx.send("I can't find that user.")
            user = ret
        else:
            user = ctx.author
        key = self.get_key(ctx.guild.id)
        jmmmapping = await self.get_jmms()
        leaderboard = sorted(list(jmmmapping.items()), key=lambda m: (key(m), self.get_messages(m)), reverse=True)
        current = (str(user), jmmmapping[str(user)])
        place = leaderboard.index(current)
        embed = discord.Embed(title=f"Jmmboard stats for {user}", color=0xFDFE00)
        award = self.get_award(place)
        embed.add_field(name="Place on the leaderboard:", value=award)
        embed.add_field(name="Messages on the jmmboard:", value=f"{current[1]['messages']} {'messages' if len(current[1]['messages']) != 1 else 'message'}")
        embed.add_field(name="Golden jmms recieved:", value=str(current[1]['reactions']))
        embed.add_field(name="jmmscore (goldjmms - nogoldjmms):", value=f"{current[1]['jmmscore']} ({current[1]['positivity']}% positive)")
        if self.is_enabled('show draobmmj', ctx.guild.id):
            embed.add_field(name="Messages on the draobmmj:", value=f"{current[1]['draobmmjmessages']} {'messages' if len(current[1]['draobmmjmessages']) != 1 else 'message'}")
            embed.add_field(name="nogoldjmms recieved:", value=str(current[1]['draobmmjreactions']))
        with contextlib.suppress(IndexError):
            if place <= len(leaderboard)+1:
                embed.add_field(name="Ahead of:", value=f"{leaderboard[place+1][0]} (with {leaderboard[place+1][1]['messages']} {'messages' if len(leaderboard[place-1][1]['messages']) != 1 else 'message'} on the jmmboard, {leaderboard[place+1][1]['reactions']} golden jmms recieved, a jmmscore of {leaderboard[place+1][1]['jmmscore']}, and {leaderboard[place+1][1]['positivity']}% positive reactions)", inline=False)
            if place > 0:
                embed.add_field(name="Behind:", value=f"{leaderboard[place-1][0]} (with {leaderboard[place-1][1]['messages']} {'messages' if len(leaderboard[place-1][1]['messages']) != 1 else 'message'} on the jmmboard, {leaderboard[place-1][1]['reactions']} golden jmms recieved, a jmmscore of {leaderboard[place-1][1]['jmmscore']}, and {leaderboard[place-1][1]['positivity']}% positive reactions)", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(info(bot))

def teardown(bot):  
    bot.remove_cog(info(bot))