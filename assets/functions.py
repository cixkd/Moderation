from disnake import Embed, Color
import traceback
from disnake.ext import commands

from config import Rules, Mute, Unmute

async def DataFetch(bot, command, table, *vals):
    try:
        query = f"SELECT * FROM {table}"
        if len(vals) == 1:
            query += f' WHERE guild_id = {vals[0]}'
        elif len(vals) == 2:
            query += f' WHERE guild_id = {vals[0]} and user_id = {vals[1]}'
        else:
            pass
        
        if command == 'all':
            datas = await bot.db.fetch(query)
            return datas
        else:
            data = await bot.db.fetchrow(query)
            return data
    except:
        print(traceback.format_exc())

async def DataUpdate(bot, query, *vals):
    if len(vals) == 0:
        await bot.db.execute(query)
    else:
        await bot.db.execute(query, *vals)
        
def SuccessEmbed(title, description):
    return Embed(title=":ballot_box_with_check: "+title, description=description, color=Color.from_rgb(104, 194, 144))

def ErrorEmbed(title, description):
    return Embed(title=":x: "+title, description=description, color=Color.from_rgb(205, 109, 109))

def UnmuteEmbed():
    e = Embed(title=f"<:{Unmute['name']}:{Unmute['ID']}> You have been unmuted.", description="You may now continue sending messages.", color=Color.from_rgb(104, 194, 144))
    return e

def InfractionEmbed(offence, reason, expirey = None, num = None):
    string = ""
    if expirey:
        string += f"\n**Expire:** <t:{expirey}>"
    if num:
        string += f"\n**Number of offences:** `{num}`"
    embed = Embed(title=f"<:{Mute['name']}:{Mute['ID']}> Infraction Information\n\nPlease review our rules", description=f"**Type:** {offence} \n**Reason:** {reason}{string}\n\nIf you would like to discuss or appeal this infraction, send a message to the ModMail bot.", url=Rules, color=Color.from_rgb(205, 109, 109))
    return embed

def owner_or_permissions():
    original = commands.has_permissions(manage_guild=True).predicate
    async def extended_check(ctx):
        if ctx.guild is None:
            return False
        roles = await DataFetch(ctx.bot, 'all', 'priv_roles', ctx.guild.id)
        condition = False
        if roles:
            for role in roles:
                if role[1] in [r.id for r in ctx.author.roles]:
                    condition = True
        c = ctx.guild.owner_id == ctx.author.id or condition
        if not c:
            c = await original(ctx)
        if not c:
            await ctx.send(embed=ErrorEmbed('Missing Permissions', 'You cannot use this command.'))
        return c
    return commands.check(extended_check)

