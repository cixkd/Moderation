import traceback
from disnake import ui, ButtonStyle, Embed
from disnake.ext.commands import command, Cog

class HelpButton(ui.Button):
    def __init__(self, bot, ctx, label, embed):
        self.bot = bot
        self.ctx = ctx
        self.embed = embed
        super().__init__(
            style=ButtonStyle.gray,
            label = label
            )
    async def callback(self, inter):
        await inter.response.defer()
        if inter.author.id != self.ctx.author.id:
            return await inter.send("You cannot interact with this menu.", epheremal=True)
        await inter.edit_original_message(embed=self.embed)

class HelpView(ui.View):
    def __init__(self, bot, ctx, labels, embeds):
        super().__init__(timeout=300.0)
        for i, label in enumerate(labels):
            self.add_item(HelpButton(bot, ctx, label, embeds[i]))

class Help(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def help(self, ctx):
        main = Embed(title="📔 Help Menu", description=f"• Detailed description of every command can be found while executing it.")
        try:
            main.set_footer(icon_url=self.bot.user.avatar.url)
        except:
            pass
        embeds = [
            main
        ]
        labels = ['🏠 Home']
        for command in self.bot.commands:
            if command.cog:
                if command.cog.qualified_name == "Help":
                    continue
                else:
                    description = command.cog.description
            else:
                description = "⚙️ Others"
            if description not in [x.title for x in embeds]:
                e = Embed(title=description, description="")
                try:
                    e.set_footer(icon_url=self.bot.user.avatar.url)
                except:
                    pass
                embeds.append(e)
                labels.append(description)
            for embed in embeds:
                if embed.title == description:
                    embed.description += f"`!{command.qualified_name}`\n"
        await ctx.send(embed=embeds[0], view=HelpView(self.bot, ctx, labels, embeds))
    
    @command(name="help")
    async def helpmenu(self, ctx):
        try:
            await self.help(ctx)
        except:
            print(traceback.format_exc())
    
def setup(bot):
    bot.add_cog(Help(bot))