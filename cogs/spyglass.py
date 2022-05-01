from disnake import Embed, ui, SelectOption, Member, PermissionOverwrite
from disnake.ext.commands import Cog, group, MissingRequiredArgument, BadArgument

from assets import functions as func

class DeleteMenu(ui.Select):
    def __init__(self, bot, ctx, datas):
        self.bot = bot
        self.ctx = ctx
        options = []
        for data in datas:
            c = self.bot.get_channel(data[2])
            if c:
                label = c.name
            else:
                label = "Deleted-Channel"
            options.append(SelectOption(label=label, value=data[2]))
        super().__init__(placeholder="Select channels from the menu.", min_values=1, max_values=len(datas), options=options)
    
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        for val in self.values:
            await func.DataUpdate(self.bot, f"DELETE FROM spyglass WHERE channel_id = {val}")
            try:
                c = self.bot.get_channel(int(val))
                await c.delete()
            except:
                pass
        await inter.edit_original_message(embed=func.SuccessEmbed('Channel Deleted!', 'Selected channels were removed from the database successfully.'), view=None)
        
class MenuView(ui.View):
    def __init__(self, bot, ctx, datas):
        super().__init__(timeout=300.0)
        self.add_item(DeleteMenu(bot, ctx, datas))

class SpyGlass(Cog):
    """
        🔎 SpyGlass
    """
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.CoverBacklog())
    
    async def CoverBacklog(self):
        await self.bot.wait_until_ready()
        datas = await func.DataFetch(self.bot, "all", 'spyglass')
        if datas:
            for data in datas:
                guild = self.bot.get_guild(data[0])
                Channel = self.bot.get_channel(data[2])
                if not Channel:
                    await func.DataUpdate(self.bot, f"DELETE FROM spyglass WHERE channel_id = {data[2]}")
                    continue
                try:
                    member = guild.get_member(data[1])
                    cha = self.bot.get_channel(data[4])
                    msg = await cha.fetch_message(data[3])
                except:
                    continue
                user_messages = []
                for channel in guild.text_channels:
                    if channel.category.name == 'spyglass':
                        continue
                    messages = await channel.history(limit=None, after=msg.created_at).flatten()
                    for message in messages:
                        if message.author.id == member.id:
                            user_messages.append(message)
                if len(user_messages):
                    for msg in [msg for msg in user_messages if msg.id not in data[5]]:
                        embed = Embed(description=msg.content, color=msg.author.color, timestamp=msg.created_at)
                        try:
                            embed.set_author(name=msg.author, url=msg.jump_url, icon_url=msg.author.icon.url)
                        except:
                            embed.set_author(name=msg.author, url=msg.jump_url)
                        embed.add_field(name="Channel", value=msg.channel.mention)
                        await Channel.send(embed=embed, files=msg.attachments)

                    await func.DataUpdate(self.bot, f"UPDATE spyglass SET last_message = $1 WHERE channel_id = $2", msg.id, data[2])
    
    @Cog.listener()
    async def on_message(self, msg):
        if msg.guild == None:
            return
        await self.bot.wait_until_ready()
        datas = await func.DataFetch(self.bot, "all", 'spyglass', msg.guild.id)
        if datas:
            for data in datas:
                if data[1] == msg.author.id:
                    channel = self.bot.get_channel(data[2])
                    if channel:
                        all_messages = data[5]
                        all_messages.append(msg.id)
                        embed = Embed(description=msg.content, color=msg.author.color, timestamp=msg.created_at)
                        try:
                            embed.set_author(name=msg.author, url=msg.jump_url, icon_url=msg.author.avatar.url)
                        except:
                            embed.set_author(name=msg.author, url=msg.jump_url)
                        embed.add_field(name="Channel", value=msg.channel.mention)
                        files = []
                        if len(msg.attachments):
                            for i in msg.attachments:
                                i = await i.to_file()
                                files.append(i)
                        await channel.send(embed=embed, files=files)
                        await func.DataUpdate(self.bot, f"UPDATE spyglass SET last_message = $1, last_channel = $2, all_messages = $3 WHERE channel_id = $4", msg.id, msg.channel.id, all_messages, channel.id)
                    else:
                        await func.DataUpdate(self.bot, "DELETE FROM spyglass WHERE channel_id = $1", data[2])

    @group(aliases=['spyglass'], invoke_without_command=True)
    async def spy(self, ctx):
        await ctx.send(embed=Embed(title="Spy Glass Commands", description=f"`!spy add <member>`\n`!spy remove`"))

    @spy.command(aliases=['create'])
    @func.owner_or_permissions()
    async def add(self, ctx, member: Member):
        datas = await func.DataFetch(self.bot, 'all', 'spyglass', ctx.guild.id)
        async def AddSpyGlass():
            if 'spyglass' not in [category.name for category in ctx.guild.categories]:
                category = await ctx.guild.create_category(name='spyglass')
            else:
                for category in ctx.guild.categories:
                    if category.name == 'spyglass':
                        break
            overwrites = {
                ctx.guild.default_role: PermissionOverwrite(view_channel=False),
                ctx.guild.me: PermissionOverwrite(view_channel=True),
            }
            mod_roles = await func.DataFetch(self.bot, 'all', 'priv_roles', ctx.guild.id)
            if mod_roles:
                for role in mod_roles:
                    role = ctx.guild.get_role(role[1])
                    if role:
                        overwrites.update({role: PermissionOverwrite(view_channel=True)})
            channel = await ctx.guild.create_text_channel(name=f"{member.name}-{member.id}", category=category, overwrites=overwrites)
            await func.DataUpdate(self.bot, f"INSERT INTO spyglass(guild_id, user_id, channel_id, last_message, last_channel, all_messages) VALUES($1, $2, $3, $4, $5, $6)", ctx.guild.id, member.id, channel.id, 123, 123, [])
            await ctx.send(embed=func.SuccessEmbed('Spy Glass Activated!', f'Every message from {member.mention} will be logged in {channel.mention}.'))
        if not len(datas):
            if member.id not in [data[1] for data in datas]:
                await AddSpyGlass()
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'Member is already being spied on.'))
        else:
            await AddSpyGlass()
    
    @add.error
    async def add_error(self, ctx, e):
        if isinstance(e, (MissingRequiredArgument, BadArgument)):
            await self.spy(ctx)

    @spy.command()
    @func.owner_or_permissions()
    async def remove(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'spyglass', ctx.guild.id)
        if datas:
            await ctx.send(view=MenuView(self.bot, ctx, datas))
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'No active spy glasses found.'))
    
    @spy.command(name="view")
    @func.owner_or_permissions()
    async def spy_view(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'spyglass', ctx.guild.id)
        if datas:
            embed = Embed(title="Active SpyGlasses", description="\n".join([f"{i+1}. {self.bot.get_channel(x[2]).mention}" for i, x in enumerate(datas)]))
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'No active spy glasses found.'))
        
    
def setup(bot):
    bot.add_cog(SpyGlass(bot))
