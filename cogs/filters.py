import traceback
from disnake import Embed, ui, SelectOption, Color, File
from disnake.ext.commands import Cog, command, group, MissingRequiredArgument
import asyncio
import names
from datetime import datetime, timedelta
import io

from assets import functions as func

class DeleteMenu(ui.Select):
    def __init__(self, bot, ctx, datas):
        self.bot = bot
        self.ctx = ctx
        options = []
        used_labels_bl = []
        used_labels_wl = []
        for data in datas:
            if data[2] == 1:
                emoji = '⬛'
                if data[1] not in used_labels_bl:
                    options.append(SelectOption(label=data[1], value=f"{data[1]},{data[2]}", emoji=emoji))
                used_labels_bl.append(data[1])
            else:
                emoji = '⬜'
                if data[1] not in used_labels_wl:
                    options.append(SelectOption(label=data[1], value=f"{data[1]},{data[2]}", emoji=emoji))
                used_labels_wl.append(data[1])
            
            
        super().__init__(placeholder="Select filters from the menu.", min_values=1, max_values=len(options), options=options)
    
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        for val in self.values:
            datas = val.split(',')
            await func.DataUpdate(self.bot, f"DELETE FROM filters WHERE trigger = '{datas[0]}' and type = {int(datas[1])}")

        await inter.edit_original_message(embed=func.SuccessEmbed('Filter Deleted!', 'Selected filters were removed from the database successfully.'), view=None)
        
class MenuView(ui.View):
    def __init__(self, bot, ctx, datas):
        super().__init__(timeout=300.0)
        length = len(datas)
        if length > 25:
            for i in range(0, length, 25):
                self.add_item(DeleteMenu(bot, ctx, datas[:25]))
                del datas[:25]

        else:
            self.add_item(DeleteMenu(bot, ctx, datas))
class Filters(Cog):
    """
        ⛔ Filters
    """
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.CheckNames())

    async def CheckNames(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                for member in guild.members:
                    try:
                        await self.on_member_join(member)
                    except:
                        pass
            await asyncio.sleep(10)

    @Cog.listener()
    async def on_member_join(self, target):
        async def CheckName(username):
            if username == None:
                return False
            punc = r'''!()-[]{};:'"\,<>./?@#$%^&*_~- '''
            filtered_username = ""
            for letter in username:
                if not letter in punc:
                    filtered_username += letter
            matches = 0
            for letter in filtered_username:
                if letter.isalpha() or letter.isnumeric():
                    matches += 1
            blacklist = await func.DataFetch(self.bot, 'all', 'filters', target.guild.id)
            if blacklist:
                blacklist = [x[1] for x in blacklist if x[2] == 1]
            else:
                blacklist = []
            return matches != len(filtered_username) or len(filtered_username) >= 16 or filtered_username in blacklist
        while True:
            name = names.get_last_name()
            if len(name) <= 15:
                break
        async def AddOffence():
            data = await func.DataFetch(self.bot, 'one', 'nick_offences', target.guild.id, target.id)
            offences = 1
            if data:
                await func.DataUpdate(self.bot, f"UPDATE nick_offences SET offences = $1 WHERE guild_id = $2 and user_id = $3", data[2]+1, target.guild.id, target.id)
                offences = data[2]+1
                if data[2]+1 >= 6:
                    if 'nickname_mute' not in [x.name for x in target.guild.roles]:
                        await target.guild.create_role(name='nickname_mute')
                    for r in target.guild.roles:
                        if r.name == 'nickname_mute':
                            await target.add_roles(r)
                            break
                    await target.send(embed=Embed(title=":warning: Warning", description="You cannot change your nickname anymore because of repeated offences.", color=Color.from_rgb(205, 109, 109)))
                    
            else:
                await func.DataUpdate(self.bot, f"INSERT INTO nick_offences(offences, guild_id, user_id)  VALUES($1, $2, $3)", 1, target.guild.id, target.id)
            embed = func.InfractionEmbed("Username offence", "Your name seems to have either non-english characters and/or is too long or contains blacklisted words. You may change your nickname using `!nickname <name>`", None, offences)
            await target.send(embed=embed)
        if await CheckName(target.name) and not target.nick:
            await target.edit(nick=name)
            await AddOffence()
        else:
            if await CheckName(target.nick):
                await target.edit(nick=name)
                await AddOffence()

    @Cog.listener()
    async def on_message(self, msg):
        try:
            if msg.author.bot or msg.guild == None:
                return
            datas = await func.DataFetch(self.bot, 'all' ,'filters', msg.guild.id)
            if not datas:
                return
            async def AutoMute():
                auto_mute = await func.DataFetch(self.bot, 'one', 'auto_mute_status', msg.guild.id)
                time = None
                num = 1
                warn = "Auto Warning"
                if auto_mute:
                    if auto_mute[1]:
                        offences = await func.DataFetch(self.bot, 'one', 'auto_mute', msg.guild.id, msg.author.id)
                        if offences:
                            num = offences[2]+1
                            await func.DataUpdate(self.bot, "UPDATE auto_mute SET offences = $1 WHERE guild_id = $2 and user_id = $3", offences[2]+1, msg.guild.id, msg.author.id)
                            if offences[2]+1 >= 5:
                                warn = "AutoMute"
                                duration = 7200.0+((offences[2]+1-5)*3600)
                                time = int((datetime.now() + timedelta(seconds=duration)).timestamp())
                                if (duration/86400) >= 28:
                                    duration = 86400*28
                                try:
                                    await msg.author.timeout(duration=duration)
                                except:
                                    pass

                        else:
                            await func.DataUpdate(self.bot, "INSERT INTO auto_mute(offences, guild_id, user_id) VALUES($1, $2, $3)", 1, msg.guild.id, msg.author.id)
                
                embed = func.InfractionEmbed(warn, "Sent a blacklisted content or file.", time, num)
                await msg.author.send(embed=embed)
            for data in datas:
                if data[2] == 1:
                    if data[1].lower() in msg.content.lower():
                        await msg.delete()
                        await AutoMute()
                if data[2] == 2:
                    allowed_extensions = [x[1] for x in datas if x[2] == 2]
                    if len(msg.attachments):
                        for attachment in msg.attachments:
                            name = attachment.filename
                            name = name.split('.')
                            if name[1].lower() not in allowed_extensions:
                                await msg.delete()
                                await AutoMute()
                                break
        except:
            print(traceback.format_exc())

    @group(invoke_without_command=True)
    async def filter(self, ctx):
        await ctx.send(embed=Embed(title="Filter Commands", description='`!filter blacklist add [trigger]`\n`!filter whitelist add [trigger]`\n`!filter remove`\n`!filter view`'))

    @filter.command()
    @func.owner_or_permissions()
    async def view(self, ctx):
        try:
            datas = await func.DataFetch(self.bot, 'all', 'filters', ctx.guild.id)
            if datas:
                value1 = ""
                value2 = ""
                for data in datas:
                    if data[2] == 1:
                        value1 += data[1]+'\n'
                    else:
                        value2 += data[1]+'\n'
                files = []
                if value2 != "":
                    files.append(File(filename="Blacklist.txt", fp=io.StringIO(value1)))
                    # embed.add_field(name="Whitelist", value='||'+value2+'||')
                if value1 != "":
                    files.append(File(filename="Whitelist.txt", fp=io.StringIO(value2)))
                    # embed.add_field(name="Blacklist", value='||'+value1+'||', inline=False)
                await ctx.send(files=files)
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'There are no active filters.'))
        except:
            print(traceback.format_exc())
    @filter.command()
    @func.owner_or_permissions()
    async def remove(self, ctx):
        try:
            datas = await func.DataFetch(self.bot, 'all', 'filters', ctx.guild.id)
            if datas:
                if len(datas) > 25*5:
                    for i in range(0, len(datas), 25*5):
                        await ctx.send(view=MenuView(self.bot, ctx, datas[:25*5]))
                        del datas[:25*5]

                else:
                    await ctx.send(view=MenuView(self.bot, ctx, datas))
                
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'There are no active filters.'))
        except:
            print(traceback.format_exc())
    
    @filter.group(invoke_without_command=True)
    async def blacklist(self, ctx):
        await self.filter(ctx)

    @blacklist.command()
    @func.owner_or_permissions()
    async def add(self, ctx, *, trigger):
        trigger = trigger.split(',')
        datas = await func.DataFetch(self.bot, 'all', 'filters', ctx.guild.id)
        async def AddBl(i):
            await func.DataUpdate(self.bot, f'INSERT INTO filters(guild_id, trigger, type) VALUES($1, $2, $3)', ctx.guild.id, i, 1)
            
        if datas:
            for i in trigger:
                if i.strip() not in [data[1] for data in datas if data[2] == 1]:
                    await AddBl(i.strip())

            await ctx.send(embed=func.SuccessEmbed('Trigger added!', 'New trigger was added successfully.'))
        else:
            await AddBl()
    
    @add.error
    async def bl_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await ctx.send(embed=Embed(title="Missing Argument", description="Correct syntax is: `!filter blacklist add [trigger]`"))

    @filter.group(invoke_without_command=True)
    async def whitelist(self, ctx):
        await self.filter(ctx)

    @whitelist.command(name="add")
    @func.owner_or_permissions()
    async def wh_add(self, ctx, *, trigger):
        datas = await func.DataFetch(self.bot, 'all', 'filters', ctx.guild.id)
        async def AddWl():
            await func.DataUpdate(self.bot, f'INSERT INTO filters(guild_id, trigger, type) VALUES($1, $2, $3)', ctx.guild.id, trigger, 2)
            await ctx.send(embed=func.SuccessEmbed('Trigger added!', 'New trigger was added successfully.'))
        if datas:
            if trigger not in [data[1] for data in datas if data[2] == 2]:
                await AddWl()
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'Same trigger already exists in the database.'))
        else:
            await AddWl()
    
    @wh_add.error
    async def wh_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await ctx.send(embed=Embed(title="Missing Argument", description="Correct syntax is: `!filter whitelist add [trigger]`"))

def setup(bot):
    bot.add_cog(Filters(bot))
