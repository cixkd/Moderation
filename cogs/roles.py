from disnake import Embed, ui, SelectOption, Role
from disnake.ext.commands import Cog, TextChannelConverter, group, has_permissions, MissingRequiredArgument
from datetime import datetime, timedelta
import asyncio

from assets import functions as func

class DeleteRole(ui.Select):
    def __init__(self, bot, ctx, datas):
        self.bot = bot
        self.ctx = ctx
        options = []
        self.datas = datas
        self.roles = datas[0][1]
        for data in self.roles:
            role = ctx.guild.get_role(data)
            if data:
                label = role.name
            else:
                label = "Deleted-Role"
            options.append(SelectOption(label=label, value=data))
        super().__init__(placeholder="Select any roles from the menu.", min_values=1, max_values=len(options), options=options)
    
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        for val in self.values:
            self.roles.remove(int(val))
        if not self.roles:
            await func.DataUpdate(self.bot, f"DELETE FROM reaction_roles WHERE msg_id = $1", self.datas[0][2])
        else:
            await func.DataUpdate(self.bot, f"UPDATE reaction_roles SET role_ids = $1 WHERE msg_id = $2", self.roles, self.datas[0][2])
        await inter.send(embed=func.SuccessEmbed('Role deleted!', 'Reaction role was deleted successfully.'))

class DeleteMenu(ui.Select):
    def __init__(self, bot, ctx, datas):
        self.bot = bot
        self.ctx = ctx
        options = []
        self.datas = datas
        for data in datas:
            options.append(SelectOption(label=data[4], value=data[4]))
        super().__init__(placeholder="Select any option from the menu.", min_values=1, max_values=1, options=options)
    
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        await inter.edit_original_message(view=MenuView(self.bot, self.ctx, [x for x in self.datas if x[4] == self.values[0]], 'remove_rr'))

class SelectEmbed(ui.Select):
    def __init__(self, bot, ctx, datas, vals):
        self.bot = bot
        self.ctx = ctx
        self.vals = vals
        self.datas = datas
        options = [SelectOption(label="Create new embed", value="new")]
        for data in datas:
            options.append(SelectOption(label=data[4], value=data[4]))
        super().__init__(placeholder="Select any option from the menu.", min_values=1, max_values=1, options=options)

    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        if self.values[0] == 'new':
            try:
                m = await self.ctx.send("Now type the name or ID of the channel where you want the reaction role embed.")
                channel = await self.bot.wait_for('message', check=lambda a: a.author.id == self.ctx.author.id and a.channel.id == self.ctx.channel.id, timeout=300.0)
                try:
                    channel = await TextChannelConverter().convert(self.ctx, channel.content)
                except:
                    return await inter.send(embed=func.ErrorEmbed('Error', 'Channel not found, please run the command again.'))
            except asyncio.TimeoutError:
                return await m.edit(content="Timed out, please select an option again.")
            try:
                m = await self.ctx.send("Now input a name for the embed.")
                name = await self.bot.wait_for('message', check=lambda a: a.author.id == self.ctx.author.id and a.channel.id == self.ctx.channel.id, timeout=300.0)
            except asyncio.TimeoutError:
                return await m.edit(content="Timed out, please select an option again.")
            msg = await channel.send(embed=Embed(title=name.content))
            await func.DataUpdate(self.bot, f"INSERT INTO reaction_roles(guild_id, role_ids, msg_id, channel_id, embed_name, emojis) VALUES($1, $2, $3, $4, $5, $6)", inter.guild.id, [self.vals[0].id], msg.id, channel.id, name.content, [self.vals[1]])
            await inter.edit_original_message(view=None, embed=func.SuccessEmbed('Menu Created!', 'New menu was created and reaction role was added successfully.'))
        else:
            for data in self.datas:
                if data[4] == self.values[0]:
                    if self.vals[1] not in data[5]:
                        data[5].append(self.vals[1])
                    else:
                        return await inter.send(embed=func.ErrorEmbed('Error', 'This emoji is already reserved for another role.'))
                    data[1].append(self.vals[0].id)
                    await func.DataUpdate(self.bot, f"UPDATE reaction_roles SET emojis = $1, role_ids = $2 WHERE msg_id = $3", data[5], data[1], data[2])
                    await inter.edit_original_message(view=None, embed=func.SuccessEmbed('Role added!', 'Reaction role was added successfully.'))
        if len(self.vals) == 3:
            await func.DataUpdate(self.bot, f"INSERT INTO short_roles(guild_id, role_id, time) VALUES($1, $2, $3)", self.ctx.guild.id, self.vals[0].id, self.vals[2])

class MenuView(ui.View):
    def __init__(self, bot, ctx, datas, command, *vals):
        super().__init__(timeout=300.0)
        self.value = False
        if command == 'remove':
            self.add_item(DeleteMenu(bot, ctx, datas))
        elif command == 'add_rr':
            self.add_item(SelectEmbed(bot, ctx, datas, vals))
        elif command == 'remove_rr':
            self.add_item(DeleteRole(bot, ctx, datas))

class Roles(Cog):
    """
        ✨ Roles
    """
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.ExpireTempRoles())
    
    async def ExpireTempRoles(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            datas = await func.DataFetch(self.bot, 'all', 'roles_expire')
            if datas:
                for data in datas:
                    try:
                        time = datetime.strptime(data[2], '%Y-%m-%d %H:%M:%S.%f')
                        if time <= datetime.now():
                            guild = self.bot.get_guild(data[0])
                            member = guild.get_member(data[3])
                            role = guild.get_role(data[1])
                            await member.remove_roles(role)
                            await func.DataUpdate(self.bot, f"DELETE FROM roles_expire WHERE guild_id = {data[0]} and user_id = {data[3]}")
                    except:
                        pass
            await asyncio.sleep(5)
    
    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.bot.wait_until_ready()
        reaction_datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', payload.guild_id)
        if reaction_datas:
            for data in reaction_datas:
                if data[2] == payload.message_id:
                    emoji_sr = None
                    for i, emoji in enumerate(data[5]):
                        if emoji == str(payload.emoji):
                            emoji_sr = i
                    if emoji_sr != None:
                        for i, role in enumerate(data[1]):
                            if i == emoji_sr:
                                guild = self.bot.get_guild(payload.guild_id)
                                role = guild.get_role(role)
                                member = guild.get_member(payload.user_id)
                                await member.remove_roles(role)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.bot.wait_until_ready()
        reaction_datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', payload.guild_id)
        if reaction_datas:
            for data in reaction_datas:
                if data[2] == payload.message_id:
                    emoji_sr = None
                    for i, emoji in enumerate(data[5]):
                        if emoji == str(payload.emoji):
                            emoji_sr = i
                    if emoji_sr != None:
                        for i, role in enumerate(data[1]):
                            if i == emoji_sr:
                                guild = self.bot.get_guild(payload.guild_id)
                                role = guild.get_role(role)
                                if role in payload.member.roles:
                                    return
                                await payload.member.add_roles(role)
                                shortr_datas = await func.DataFetch(self.bot, 'all', 'short_roles', payload.guild_id)
                                if shortr_datas:
                                    for data in shortr_datas:
                                        if role.id == data[1]:
                                            time = datetime.now() + timedelta(seconds=data[2])
                                            await func.DataUpdate(self.bot, f"INSERT INTO roles_expire(guild_id, role_id, user_id, time) VALUES($1, $2, $3, $4)", payload.guild_id, role.id, payload.member.id, str(time))

    @Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        datas = await func.DataFetch(self.bot, 'all', 'temp_roles', member.guild.id)
        if datas:
            for data in datas:
                role = member.guild.get_role(data[1])
                time = datetime.now() + timedelta(seconds=data[2])
                if role:
                    await member.add_roles(role)
                    await func.DataUpdate(self.bot, "INSERT INTO roles_expire(guild_id, role_id, time, user_id) VALUES($1, $2, $3, $4)", member.guild.id, role.id, str(time), member.id)
    
    @group(invoke_without_command=True)
    async def roles(self, ctx):
        await ctx.send(embed=Embed(title="Roles commands", description="`!roles rr add <role> <emoji>`\n`!roles temp add <role> <time>`\n`!roles sh add <role> <time> <emoji>`\n`!roles update`\n`!roles remove`\n`!roles view`"))
    
    @roles.group(aliases=['rr', 'reactionr'], invoke_without_command=True)
    async def reactionroles(self, ctx):
        await self.roles(ctx)
    
    @roles.command(aliases=['remove'])
    @has_permissions(manage_roles=True)
    async def delete(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', ctx.guild.id)
        if datas:
            await ctx.send(view=MenuView(self.bot, ctx, datas, 'remove'))
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'There are no active reaction roles .'))
    
    @roles.command(name="view")
    @has_permissions(manage_roles=True)
    async def roles_view(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', ctx.guild.id)
        if datas:
            # embed = Embed(title="Active reaction roles", description="\n".join([f"{i+1}. Menu: {x[4]}" for i, x in enumerate(datas)]))
            embed =  Embed(title="Active reaction roles")
            for data in datas:
                value = ""
                for r in data[1]:
                    r = ctx.guild.get_role(r)
                    if r:
                        value += r.mention+'\n'
                    else:
                        value += "Deleted-Role\n"
                embed.add_field(name=data[4],value=value, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'There are no active reaction roles .'))

    @roles.command()
    @has_permissions(manage_roles=True)
    async def update(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', ctx.guild.id)
        if datas:
            embed_names = []
            for data in datas:
                if data[4] not in embed_names:
                    embed_names.append(data[4])
            for data in datas:
                for name in embed_names:
                    if name == data[4]:
                        ch = self.bot.get_channel(data[3])
                        msg = await ch.fetch_message(data[2])
                        embed = msg.embeds[0]
                        guild = self.bot.get_guild(data[0])
                        lines = ""
                        emojis = []
                        for i, role in enumerate(data[1]):
                            role = guild.get_role(role)
                            for index, emoji in enumerate(data[5]):
                                if ((role) and (index == i) and (role.name not in lines)):
                                    lines += f"{emoji} {role.name}\n"
                                    emojis.append(emoji)
                        embed.description = lines
                        await msg.edit(embed=embed)
                        for emoji in emojis:
                            if emoji not in [reaction.emoji for reaction in msg.reactions]:
                                try:
                                    await msg.add_reaction(emoji)
                                except:
                                    pass
                        for reaction in msg.reactions:
                            if str(reaction.emoji) not in lines:
                                await msg.clear_reaction(reaction)
            await ctx.send(embed=func.SuccessEmbed('Embeds Updated!', "All embeds updated successfully."))
    
    @reactionroles.command(name="add", aliases=['create'])
    @has_permissions(manage_roles=True)
    async def rr_add(self, ctx, role: Role, emoji):
        datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', ctx.guild.id)
        await ctx.send(view=MenuView(self.bot, ctx, datas, 'add_rr', role, emoji))
    
    @rr_add.error
    async def rr_add_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await self.roles(ctx)
    
    @roles.group(aliases=['temprole', 'temp', 'tp'], invoke_without_command=True)
    @has_permissions(manage_roles=True)
    async def temproles(self, ctx):
        await self.roles(ctx)
    
    @temproles.command(name="add", aliases=['create'])
    @has_permissions(manage_roles=True)
    async def tp_add(self, ctx, role: Role, time):
        time_stamps = ['d', 'h', 'm']
        duration_check = ''.join([x for x in time if not x.isdigit()])
        if duration_check not in time_stamps:
            return await ctx.send(embed=func.ErrorEmbed("Error", "Wrong syntax, Time should be like `2m, 2h or 2d`."))
        for stamp in time_stamps:
            if stamp in time:
                if stamp == 'h':
                    added_time = timedelta(hours=int(time.replace('h','')))
                elif stamp == 'm':
                    added_time = timedelta(minutes=int(time.replace('m','')))
                elif stamp == 'd':
                    added_time = timedelta(days=int(time.replace('d','')))
                break
        
        datas = await func.DataFetch(self.bot, 'all', 'temp_roles', ctx.guild.id)
        async def CreateTempRole():
            await func.DataUpdate(self.bot, "INSERT INTO temp_roles(guild_id, role_id, time) VALUES($1, $2, $3)", ctx.guild.id, role.id, added_time.total_seconds())
            await ctx.send(embed=func.SuccessEmbed('Role added successfully.', f'{role} was added in temporary roles successfully.'))
        if datas:
            if role.id not in [data[1] for data in datas]:
                await CreateTempRole()
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', f'{role.mention} is already setup in temporary roles.'))
        else:
            await CreateTempRole()
    
    @tp_add.error
    async def tp_add_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await self.roles(ctx)
        
    @roles.group(aliases=['short', 'shortroles', 'sh'], invoke_without_command=True)
    @has_permissions(manage_roles=True)
    async def shorttime(self, ctx):
        await self.roles(ctx)
    
    @shorttime.command(name="add", aliases=['create'])
    @has_permissions(manage_roles=True)
    async def sh_add(self, ctx, role: Role, time, emoji):
        time_stamps = ['d', 'h', 'm']
        duration_check = ''.join([x for x in time if not x.isdigit()])
        if duration_check not in time_stamps:
            return await ctx.send(embed=func.ErrorEmbed("Error", "Wrong syntax, Time should be like `2m, 2h or 2d`."))
        for stamp in time_stamps:
            if stamp in time:
                if stamp == 'h':
                    added_time = timedelta(hours=int(time.replace('h','')))
                elif stamp == 'm':
                    added_time = timedelta(minutes=int(time.replace('m','')))
                elif stamp == 'd':
                    added_time = timedelta(days=int(time.replace('d','')))
                break
        datas = await func.DataFetch(self.bot, 'all', 'short_roles', ctx.guild.id)
        added_time = added_time.total_seconds()
        if datas:
            for data in datas:
                if data[1] == role.id:
                    return await ctx.send(embed=func.ErrorEmbed('Error', 'A setup for this role is already in the database.'))
        datas = await func.DataFetch(self.bot, 'all', 'reaction_roles', ctx.guild.id)
        await ctx.send(view=MenuView(self.bot, ctx, datas, 'add_rr', role, emoji, added_time))

    @sh_add.error
    async def sh_add_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await self.roles(ctx)

def setup(bot):
    bot.add_cog(Roles(bot))
