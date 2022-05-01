from disnake import Embed, ui, SelectOption, Object, Member, User, TextChannel, Role, Color
from disnake.ext.commands import Cog, command, MissingRequiredArgument, group, BadArgument, MemberNotFound
from datetime import timedelta, datetime
import asyncio
import traceback

from assets import functions as func
from config import Log_Channel

class DeleteMenu(ui.Select):
    def __init__(self, bot, ctx, datas):
        self.bot = bot
        self.ctx = ctx
        options = []
        for data in datas:
            guild = self.bot.get_guild(data[0])
            role = guild.get_role(data[1])
            if role:
                label = role.name
            else:
                label = "Deleted-Role"
            options.append(SelectOption(label=label, value=data[1]))
        super().__init__(placeholder="Select roles from the menu.", min_values=1, max_values=len(datas), options=options)
    
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        for val in self.values:
            await func.DataUpdate(self.bot, f"DELETE FROM priv_roles WHERE role_id = {val}")
        await inter.edit_original_message(embed=func.SuccessEmbed('Role Deleted!', 'Selected roles were removed from the database successfully.'), view=None)
        
class MenuView(ui.View):
    def __init__(self, bot, ctx, datas):
        super().__init__(timeout=300.0)
        self.add_item(DeleteMenu(bot, ctx, datas))

class Mod(Cog):
    """
        👮 Moderation
    """
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.ExpireBans())
    
    async def ExpireBans(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            datas = await func.DataFetch(self.bot, 'all', 'bans')
            if not datas:
                continue
            for data in datas:
                try:
                    time = datetime.strptime(data[2], '%Y-%m-%d %H:%M:%S.%f')
                    if datetime.now() >= time:
                        guild = self.bot.get_guild(data[0])
                        member = Object(id=data[1])
                        await guild.unban(user=member, reason="Time's up.")
                        await func.DataUpdate(self.bot, f"DELETE FROM bans WHERE guild_id = {data[0]} and user_id = {data[1]}")
                except:
                    print(traceback.format_exc())
            await asyncio.sleep(10)

    @Cog.listener()
    async def on_message_delete(self, msg):
        if msg.author.bot:
            return
        embed=Embed(title=f"**{msg.author}**'s message was deleted", 
        description=msg.content, timestamp=msg.created_at, color=Color.from_rgb(205, 109, 109))
        embed.add_field(name= "Channel" ,value=msg.channel.mention, 
        inline=False)
        try:
            embed.set_author(name=f"{msg.author} ({msg.author.id})", icon_url=msg.author.avatar.url)
        except:
            embed.set_author(name=f"{msg.author} ({msg.author.id})")
        channel=self.bot.get_channel(Log_Channel)
        files = []
        if len(msg.attachments):
            for i in msg.attachments:
                i = await i.to_file()
                files.append(i)
        if files:
            await channel.send(embed=embed, files=files)
        else:
            await channel.send(embed=embed)
    
    @Cog.listener()
    async def on_message_edit(self, msg_before, msg_after):
        if msg_before.author.bot:
            return
        embed=Embed(title=f"**{msg_before.author}** Edited their message",
        description="", color=Color.from_rgb(205, 109, 109), timestamp=msg_after.created_at)
        embed.add_field(name="Before"  ,value=msg_before.content, 
        inline=True)
        embed.add_field(name="After" ,value=msg_after.content, 
        inline=True)
        try:
            embed.set_author(name=f"{msg_before.author} ({msg_before.author.id})", icon_url=msg_before.author.avatar.url, url=msg_before.jump_url)
        except:
            embed.set_author(name=f"{msg_before.author} ({msg_before.author.id})", url=msg_before.jump_url)
        channel=self.bot.get_channel(Log_Channel)
        await channel.send(embed=embed)
    
    @command()
    @func.owner_or_permissions()
    async def purge(self, ctx, amount:int):
        try:
            if amount <= 1000:
                await ctx.channel.purge(limit=amount+1, check=lambda m: m.pinned == False)
            else:
                await ctx.send("You can't clear more than 1000 messages.")
        except:
            await ctx.send("An error occurred, try running the command again.")

    @command()
    async def nickname(self, ctx, name):
        if 'nickname_mute' not in [x.name for x in ctx.guild.roles]:
            await ctx.guild.create_role(name='nickname_mute')
        if 'nickname_mute' not in [x.name for x in ctx.author.roles]:
            try:
                await ctx.author.edit(nick=name)
                await ctx.send(embed=func.SuccessEmbed('Nickname changed!', f'Your nickname was changed to **{name}**.'))
            except:
                print(traceback.format_exc())

        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'You cannot change your nickname anymore.'))
        
    @nickname.error
    async def nickname_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await ctx.send(embed=func.ErrorEmbed('Error', 'Correct syntax is: `!nickname <name>`'))

    @group(invoke_without_command=True, aliases=['privroles'])
    async def proles(self, ctx):
        await ctx.send(embed=Embed(title="Privilaged Roles Commands", description="`!proles add <role>`\n`!prole remove`\n`!proles view`"))
    
    @proles.command(name="view")
    async def p_roles_view(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'priv_roles', ctx.guild.id)
        if datas:
            roles = []
            for data in datas:
                role = ctx.guild.get_role(data[1])
                if role:
                    roles.append(role.mention)

            e = Embed(title="Privilaged Roles", description="\n".join([x for x in roles]))
            await ctx.send(embed=e)
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'There are no privileged roles.'))

    @proles.command(name="add")
    @func.owner_or_permissions()
    async def proles_add(self, ctx, role: Role):
        datas = await func.DataFetch(self.bot, 'all', 'priv_roles', ctx.guild.id)
        async def AddRole():
            await func.DataUpdate(self.bot, f"INSERT INTO priv_roles(guild_id, role_id) VALUES($1, $2)", ctx.guild.id, role.id)
            await ctx.send(embed=func.SuccessEmbed('Role added!', f'{role.mention} was given privilages successfully.'))
        if datas:
            if role.id not in [data[1] for data in datas]:
                await AddRole()
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'This role has already been setup as a privileged role.'))
        else:
            await AddRole()
    
    @proles_add.error
    async def proles_error(self, ctx, e):
        if isinstance(e, (BadArgument, MissingRequiredArgument)):
            await self.proles(ctx)
    
    @proles.command(name="remove")
    @func.owner_or_permissions()
    async def proles_remove(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'priv_roles', ctx.guild.id)
        if datas:
            await ctx.send(view=MenuView(self.bot, ctx, datas))
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'No privilaged roles found.'))
    
    @proles_remove.error
    async def proles_remove_error(self, ctx, e):
        if isinstance(e, (BadArgument, MissingRequiredArgument)):
            await self.proles(ctx)

    @command()
    @func.owner_or_permissions()
    async def slowmode(self, ctx, seconds: int, channel: TextChannel = None):
        if channel == None:
            channel = ctx.channel
        await channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=func.SuccessEmbed('Slowmode Edited!', f'Slowmode changed to {seconds} successfully.'))
    
    @slowmode.error
    async def slowmode_error(self, ctx, e):
        if isinstance(e, (MissingRequiredArgument, BadArgument)):
            await ctx.send(embed=func.ErrorEmbed('Error', 'Correct syntax is: `!slowmode <seconds> [channel]`\nIf channel is not specified, slowmode of the parent channel will be edited.'))

    @command()
    @func.owner_or_permissions()
    async def ban(self, ctx, member: User, time = None):
        if time not in ["None", None]:
            time_stamps = ['d', 'h', 'm']
            duration_check = ''.join([x for x in time if not x.isdigit()])
            if duration_check not in time_stamps:
                return await ctx.send(embed=func.ErrorEmbed("Error", "Wrong syntax, Time should be like `2m, 2h or 2d` or `None` for permanent ban."))
            for stamp in time_stamps:
                if stamp in time:
                    if stamp == 'h':
                        added_time = timedelta(hours=int(time.replace('h','')))
                    elif stamp == 'm':
                        added_time = timedelta(minutes=int(time.replace('m','')))
                    elif stamp == 'd':
                        added_time = timedelta(days=int(time.replace('d','')))
                    break
        elif time == "None":
            added_time = None
        else:
            added_time = timedelta(days=30)
        if added_time:
            time = datetime.now()
            time += added_time
        m = await ctx.send("Now input the reason for the ban.")
        try:
            msg = await self.bot.wait_for('message', check=lambda a: a.channel.id == ctx.channel.id and a.author.id == ctx.author.id, timeout=300.0)
            if added_time:
                string = f"\nYour ban will expire on <t:{int(time.timestamp())}:t>."
            else:
                string = '.'
            try:
                await member.send(f"You were banned from **{ctx.guild.name}**\n\nReason: {msg.content}{string}")
            except:
                pass
            member = Object(id=member.id)
            await ctx.guild.ban(user=member, reason=msg.content)
            if added_time:
                datas = await func.DataFetch(self.bot, 'all', 'bans', ctx.guild.id)
                if datas:
                    for data in datas:
                        if data[1] == member.id:
                            await func.DataUpdate(self.bot, f"UPDATE bans SET time = $1 WHERE guild_id = {ctx.guild.id} and user_id = {member.id}", str(time))
                        else:
                            await func.DataUpdate(self.bot, f"INSERT INTO bans(guild_id, user_id, time) VALUES($1, $2, $3)", ctx.guild.id, member.id, str(time))
                else:
                    await func.DataUpdate(self.bot, f"INSERT INTO bans(guild_id, user_id, time) VALUES($1, $2, $3)", ctx.guild.id, member.id, str(time))
            await ctx.send(embed=func.SuccessEmbed('User Banned!', f'User was banned successfully.'))
        except asyncio.TimeoutError:
            await m.edit(content="Timed out. Please run the command again.")
    
    @ban.error
    async def ban_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await ctx.send(embed=func.ErrorEmbed('Missing Arguments', '`!ban <user> <time>`\nTime can be set to `None` for a permanent ban.'))

    @command()
    @func.owner_or_permissions()
    async def kick(self, ctx, member: Member, *, reason = "No Reason Provided."):
        await member.send(f"You were kicked from {ctx.guild.name}.\n\nReason: {reason}")
        await member.kick(reason=reason)
    
    @kick.error
    async def kick_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await ctx.send(embed=func.ErrorEmbed('Missing Arguments', '`!kick <member>`'))
        if isinstance(e, MemberNotFound):
            await ctx.send(embed=func.ErrorEmbed('Error', f'Member you mentioned was not found. Make sure they are in the guild.'))

def setup(bot):
    bot.add_cog(Mod(bot))
