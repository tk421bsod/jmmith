import asyncio
import typing
import discord
from discord.ext import commands
import contextlib
import time

class info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.AWARDS = {1:'<:gold_bimm:896479698878615552> (1)', 2:':second_place:', 3:':third_place:'}
        self.delay = 0
        #if self.bot.config['USE_CUSTOM_EMOJI']:
            #self.bot.AWARDS[1] = '<:gold_bimm:896479698878615552> (1)'

    async def convert(self, ctx, arg):
        return await commands.MemberConverter().convert(ctx, arg)

    async def convert_to_member(self, ctx, user):
        if user:
            user = await self.convert(ctx, user)
        else:
            user = ctx.author
        return user

    async def await_delete(self, message):
        await message.channel.send(message)
        await message.add_reaction("\U0001f5d1")
        await asyncio.sleep(0.5)
        start = time.time()
        while True:
            if time.time() - start >= 120:
                return await message.clear_reaction("\U0001f5d1")
            try:
                reaction = await self.bot.wait_for('reaction_add', timeout=120.0)
            except asyncio.TimeoutError:
                return await message.clear_reaction("\U0001f5d1")
            users = await reaction[0].users().flatten()
            if message.author in users and reaction[0].message.id == message.id:
                return await message.delete()

#TODO: cache jmmmapping so we don't need to do this on demand (it's slow)
    async def get_jmmmapping(self):
        '''Gets jmmboard data for every user'''
        jmmmapping = {}
        start = time.time()
        #step one: calculate total messages and reactions
        for message in self.bot.messages:
            try:
                jmmmapping[str(message.author)]
            except KeyError:
                jmmmapping[str(message.author)] = {'reactions':0, 'messages':0, 'draobmmjmessages':0, 'draobmmjreactions':0, 'jmmscore':0}
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
        #step two: calculate stats based on those reactions
        for i in list(jmmmapping.keys()):
            jmmmapping[i]['jmmscore'] = jmmmapping[i]['reactions']-jmmmapping[i]['draobmmjreactions']
            if not jmmmapping[i]['reactions'] and not jmmmapping[i]['draobmmjreactions']:
                jmmmapping.pop(i)
            elif jmmmapping[i]['draobmmjreactions'] and not jmmmapping[i]['reactions']:
                jmmmapping[i]['positivity'] = 0
            else:
                jmmmapping[i]['positivity'] = round((jmmmapping[i]['reactions']/(jmmmapping[i]['reactions']+jmmmapping[i]['draobmmjreactions']))*100,1)
        self.delay = time.time()-start    
        return jmmmapping

    async def get_most_jmms(self, user, draobmmj=False):
        start = time.time()
        jmms = []
        for message in self.bot.messages:
            if str(message.author) != user:
                continue
            for i in message.reactions: 
                if hasattr(i.emoji, 'id'):
                    if i.emoji.id == 774445538409054218 and not draobmmj:
                        if i.count >= 1:
                            jmms.append({'message':message, 'reactions':i.count})
                    if i.emoji.id == 776612785647910933 and draobmmj:
                        if i.count >= 1:
                            jmms.append({'message':message, 'reactions':i.count})
        self.delay = time.time()-start
        return jmms

    def get_messages(self, m):
        return m[1]['messages']
    
    def get_jmms(self, m):
        return m[1]['reactions']

    def get_jmmscore(self, m):
        return m[1]['jmmscore']
    
    def get_positivity(self, m):
        return m[1]['positivity']

    def get_jmms_alt(self, m):
        return m['reactions']

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
            return self.get_jmms
        elif self.is_enabled('sort by jmmscore', guild_id):
            return self.get_jmmscore
        elif self.is_enabled('sort by positivity', guild_id):
            return self.get_positivity
        return self.get_messages

    @commands.command(hidden=True, aliases=['mostjmms'])
    async def mostjmmed(self, ctx, *, user=None):
        if self.bot.cache_lock.locked() and self.bot.initial_caching == True:
            total = len(self.bot.guilds[0].text_channels)
            if self.bot.IS_DPY_2:
                total += len(self.bot.guilds[0].threads)
            return await ctx.send(f"The message cache isn't ready yet. Try again later. \n{self.bot.itercount}/{total} channels have been cached.")
        try:
            user = await self.convert_to_member(ctx, user)
        except:
            return await ctx.send("I can't find that user.")
        if self.delay > 1:
            await ctx.send("Fetching jmmboard data...")
        most_jmmed = await self.get_most_jmms(str(user))
        most_jmmed.sort(key=self.get_jmms_alt, reverse=True)
        if not most_jmmed:
            return await ctx.send("It doesn't look like you have any golden jmms on your messages.")
        desc = ""
        for i in most_jmmed[:10]:
            if len(desc+f"{i['reactions']} gold jmms: [Go to message]({i['message'].jump_url})") >= 4096:
                break
            desc += f"{i['reactions']} gold jmms: [Go to message]({i['message'].jump_url})\n"
        response = await ctx.send(embed=discord.Embed(title=f"{user}'s most golden jmmed messages:", description=desc, color=0xFDFE00))
        await self.await_delete(response)

    @commands.command(hidden=True, aliases=['demmjtsom', 'negativegoldjmms', 'mostjmmednt', 'mostcursed'])
    async def mostunjmmed(self, ctx, *, user=None):
        if self.bot.cache_lock.locked() and self.bot.initial_caching == True:
            total = len(self.bot.guilds[0].text_channels)
            if self.bot.IS_DPY_2:
                total += len(self.bot.guilds[0].threads)
            return await ctx.send(f"The message cache isn't ready yet. Try again later. \n{self.bot.itercount}/{total} channels have been cached.")
        try:
            user = await self.convert_to_member(ctx, user)
        except:
            return await ctx.send("I can't find that user.")
        if self.delay >= 1:
            await ctx.send("Fetching draobmmj data...")
        most_jmmed = await self.get_most_jmms(str(user), True)
        most_jmmed.sort(key=self.get_jmms_alt, reverse=True)
        if not most_jmmed:
            return await ctx.send("It doesn't look like you have any nogoldjmms on your messages.")
        desc = ""
        for i in most_jmmed[:10]:
            if len(desc+f"{i['reactions']} nogoldjmms: [Go to message]({i['message'].jump_url})") >= 4096:
                break
            desc += f"{i['reactions']} nogoldjmms: [Go to message]({i['message'].jump_url})\n"
        response = await ctx.send(embed=discord.Embed(title=f"{user}'s most nogoldjmmed messages:", description=desc, color=discord.Color.dark_red()))
        await self.await_delete(response)

    @commands.command(hidden=True, aliases=['leaderboard', 'jmmleaderboards'])
    async def jmmleaderboard(self, ctx, limit:typing.Optional[str]=None):
        if isinstance(limit, str):
            if ':' in limit:
                limit = [int(i) for i in limit.split(':')]
                if limit[1] < limit[0]:
                    return await ctx.send("the limit can't be less than the start!")
                if limit[0] > 0:
                    limit[0] -= 1
            else:
                limit = [0, int(limit)]
        else:
            limit = [0, 10]
        if limit[1] < 2 or limit[1]-limit[0] < 2:
            return await ctx.send("I can't show less than 2 people on the leaderboard. sorry.")
        if self.bot.cache_lock.locked() and self.bot.initial_caching == True:
            total = len(self.bot.guilds[0].text_channels)
            if self.bot.IS_DPY_2:
                total += len(self.bot.guilds[0].threads)
            return await ctx.send(f"The message cache isn't ready yet. Try again later. \n{self.bot.itercount}/{total} channels have been cached.")
        key = self.get_key(ctx.guild.id)
        if self.delay >= 1:
            await ctx.send("Fetching leaderboard data...")
        jmmmapping = await self.get_jmmmapping()
        leaderboard = sorted(list(jmmmapping.items()), key=lambda m: (key(m), self.get_messages(m)), reverse=True)
        desc = f"**Currently sorted by *{key.__name__.replace('get_','')}***.\n**Showing places {limit[0]+1} through {limit[1]}. (out of {len(leaderboard)})**\n"
        for value in leaderboard[limit[0]:limit[1]]:
            place = leaderboard.index(value)
            award = self.get_award(place)
            if not self.is_enabled('show draobmmj', ctx.guild.id):
                desc += f"{award}: {value[0]} ({value[1]['messages']} messages on the jmmboard, {value[1]['reactions']} golden jmms recieved, a jmmscore of {value[1]['reactions']-value[1]['draobmmjreactions']}, and {value[1]['positivity']}% positive reactions)\n"
            else:
                desc += f"{award}: {value[0]} ({value[1]['messages']} messages on the jmmboard, {value[1]['reactions']} golden jmms recieved, {value[1]['draobmmjmessages']} messages on the draobmmj, {value[1]['draobmmjreactions']} nogoldjmms recieved, a jmmscore of {value[1]['reactions']-value[1]['draobmmjreactions']}, and {value[1]['positivity']}% positive reactions)\n"
        leaderboard = discord.Embed(title="Jmmboard leaderboard:", description=desc, color=0xFDFE00)
        try:
            response = await ctx.send(embed=leaderboard)
        except discord.HTTPException:
            response = await ctx.send("<:blobpaiN:839543891518685225> I can't show what you requested. Try using a smaller limit. (or a smaller interval if you're using leaderboard slicing)")
        await self.await_delete(response)

    @commands.command(hidden=True, aliases=['stats', 'jmmboardstats'])
    async def jmmstats(self, ctx, *, user=None):
        if self.bot.cache_lock.locked() and self.bot.initial_caching == True:
            total = len(self.bot.guilds[0].text_channels)
            if self.bot.IS_DPY_2:
                total += len(self.bot.guilds[0].threads)
            return await ctx.send(f"The message cache isn't ready yet. Try again later. \n{self.bot.itercount}/{total} channels have been cached.")
        try:
            user = await self.convert_to_member(ctx, user)
        except:
            return await ctx.send("I can't find that user.")
        key = self.get_key(ctx.guild.id)
        if self.delay >= 1:
            await ctx.send(f"Looking up stats for {user}...")
        jmmmapping = await self.get_jmmmapping()
        leaderboard = sorted(list(jmmmapping.items()), key=lambda m: (key(m), self.get_messages(m)), reverse=True)
        try:
            current = (str(user), jmmmapping[str(user)])
        except KeyError:
            return await ctx.send(f"Something went wrong when looking up stats for '{user}'. They might not have anything on the jmmboard.")
        place = leaderboard.index(current)
        embed = discord.Embed(title=f"Jmmboard stats for {user}", color=0xFDFE00, description=f"**The leaderboard is currently sorted by *{key.__name__.replace('get_','')}***.\n")
        award = self.get_award(place)
        embed.add_field(name="Place on the leaderboard:", value=award)
        embed.add_field(name="Messages on the jmmboard:", value=f"{current[1]['messages']} messages")
        embed.add_field(name="Golden jmms recieved:", value=str(current[1]['reactions']))
        embed.add_field(name="jmmscore (goldjmms - nogoldjmms):", value=f"{current[1]['jmmscore']} ({current[1]['positivity']}% positive)")
        if self.is_enabled('show draobmmj', ctx.guild.id):
            embed.add_field(name="Messages on the draobmmj:", value=f"{current[1]['draobmmjmessages']} messages")
            embed.add_field(name="nogoldjmms recieved:", value=str(current[1]['draobmmjreactions']))
        with contextlib.suppress(IndexError):
            if place <= len(leaderboard)+1:
                embed.add_field(name="Ahead of:", value=f"{leaderboard[place+1][0]} (with {leaderboard[place+1][1]['messages']} messages on the jmmboard, {leaderboard[place+1][1]['reactions']} golden jmms recieved, a jmmscore of {leaderboard[place+1][1]['jmmscore']}, and {leaderboard[place+1][1]['positivity']}% positive reactions)", inline=False)
            if place > 0:
                embed.add_field(name="Behind:", value=f"{leaderboard[place-1][0]} (with {leaderboard[place-1][1]['messages']} messages on the jmmboard, {leaderboard[place-1][1]['reactions']} golden jmms recieved, a jmmscore of {leaderboard[place-1][1]['jmmscore']}, and {leaderboard[place-1][1]['positivity']}% positive reactions)", inline=False)
        response = await ctx.send(embed=embed)
        await self.await_delete(response)

def setup(bot):
    bot.add_cog(info(bot))

def teardown(bot):  
    bot.remove_cog(info(bot))
