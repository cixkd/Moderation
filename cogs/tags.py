from disnake import Embed, ui, SelectOption
from disnake.ext.commands import Cog, group, command, MissingRequiredArgument

from assets import functions as func

class DeleteMenu(ui.Select):
    def __init__(self, bot, ctx, datas):
        self.bot = bot
        self.ctx = ctx
        options = []
        for data in datas:
            options.append(SelectOption(label=data[1], value=data[1]))
        super().__init__(placeholder="Select channels from the menu.", min_values=1, max_values=len(datas), options=options)
    
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send('You cannot interact with this menu.', epheremal=True)
        for val in self.values:
            await func.DataUpdate(self.bot, f"DELETE FROM tags WHERE name = '{val}'")
        await inter.edit_original_message(embed=func.SuccessEmbed('Tags Deleted!', 'Selected tags were removed from the database successfully.'), view=None)
        
class MenuView(ui.View):
    def __init__(self, bot, ctx, datas):
        super().__init__(timeout=300.0)
        self.add_item(DeleteMenu(bot, ctx, datas))

class Tags(Cog):
    """
        🏷️ Tags
    """
    def __init__(self, bot):
        self.bot = bot

    @group(aliases=['tags'], invoke_without_command=True)
    async def tag(self, ctx):
        await ctx.send(embed=Embed(title='Tag Commands', description="`!tag add <name> <information>`\n`!tag remove`\n`!tview <name>`"))

    @tag.command(aliases=['add'])
    @func.owner_or_permissions()
    async def create(self, ctx, name, *, info):
        datas = await func.DataFetch(self.bot, 'all', 'tags', ctx.guild.id)
        async def CreateTag():
            await func.DataUpdate(self.bot, "INSERT INTO tags(guild_id, name, info) VALUES($1, $2, $3)", ctx.guild.id, name, info)
            await ctx.send(embed=func.SuccessEmbed('Tag Created!', f'Tag named `{name}` created successfully.'))
        if datas:
            if name.lower() not in [data[1].lower() for data in datas]:
                await CreateTag()
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', f'One tag named `{name}` already exists.'))
        else:
            await CreateTag()
    
    @create.error
    async def create_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await self.tag(ctx)

    @tag.command()
    @func.owner_or_permissions()
    async def remove(self, ctx):
        datas = await func.DataFetch(self.bot, 'all', 'tags', ctx.guild.id)
        if datas:
            await ctx.send(view=MenuView(self.bot, ctx, datas))
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'No tags found.'))
    
    @command()
    async def tview(self, ctx, name):
        datas = await func.DataFetch(self.bot, 'all', 'tags', ctx.guild.id)
        if datas:
            if name.lower() not in [data[1].lower() for data in datas]:
                await ctx.send("No tag with that name was found.")
            else:
                for data in datas:
                    if data[1].lower() == name.lower():
                        await ctx.send(data[2])
        else:
            await ctx.send("No tag with that name was found.")
    
    @tview.error
    async def tview_error(self, ctx, e):
        if isinstance(e, MissingRequiredArgument):
            await self.tag(ctx)

def setup(bot):
    bot.add_cog(Tags(bot))