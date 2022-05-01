import traceback
from disnake import Embed, Member
from disnake.ext.commands import Cog, command, group, MissingRequiredArgument, BadArgument
from datetime import timedelta, datetime
import asyncio

from assets import functions as func

class Mute(Cog):
    """
        🔇 Mute
    """
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.ExpireChannelMute())

    async def ExpireChannelMute(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                datas = await func.DataFetch(self.bot, 'all', 'mutes')
                if not datas:
                    continue
                for data in datas:
                    try:
                        time = datetime.strptime(data[3], '%Y-%m-%d %H:%M:%S.%f')
                        if datetime.now() >= time:
                            channel = self.bot.get_channel(data[2])
                            guild = self.bot.get_guild(data[0])
                            member = guild.get_member(data[1])
                            await channel.set_permissions(member, send_messages=None)
                            await func.DataUpdate(self.bot, f"DELETE FROM mutes WHERE guild_id = {data[0]} and user_id = {data[1]} and channel_id = {data[2]}")
                            await member.send(embed=func.UnmuteEmbed())
                    except:
                        pass
            except:
                pass
            await asyncio.sleep(5)
    
    @group(invoke_without_command=True)
    async def mute(self, ctx):
        await ctx.send(embed=Embed(title="Mute System", description="`!mute temp <member> [time (like: 2m, 2h or 2d)]`\n`!tmute <member> [time (like: 2m, 2h or 2d)]`\n`!mute channel <member> [time (like: 2m, 2h or 2d)]`\n`!mute automute <condition (enable/disable)>`"))

    @mute.command()
    @func.owner_or_permissions()
    async def automute(self, ctx, condition):
        data = await func.DataFetch(self.bot, 'one', 'auto_mute_status', ctx.guild.id)
        if not data:
            await func.DataUpdate(self.bot, f"INSERT INTO auto_mute_status(guild_id, status) VALUES($1, $2)", ctx.guild.id, 0)
            data = [0, 0]
        if condition.lower() in ['true', 'enable', 'enabled']:
            if not data[1]:
                await func.DataUpdate(self.bot, f"UPDATE auto_mute_status SET status = 1 WHERE guild_id = {ctx.guild.id}")
                await ctx.send(embed=func.SuccessEmbed('Auto-Mute enabled!', 'Auto mute was enabled successfully.'))
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'Auto mute is already enabled.'))
        elif condition.lower() in ['false', 'disable', 'disabled']:
            if data[1]:
                await func.DataUpdate(self.bot, f"UPDATE auto_mute_status SET status = 0 WHERE guild_id = {ctx.guild.id}")
                await ctx.send(embed=func.SuccessEmbed('Auto-Mute disabled!', 'Auto mute was disabled successfully.'))
            else:
                await ctx.send(embed=func.ErrorEmbed('Error', 'Auto mute is already disabled.'))
        else:
            await ctx.send(embed=func.ErrorEmbed('Error', 'Provide a valid condition. (`enable`/`disable`)'))
    
    @automute.error
    async def automute_error(self, ctx, e):
        if isinstance(e, (MissingRequiredArgument, BadArgument)):
            await ctx.send(embed=func.ErrorEmbed('Syntax Error', 'Correct syntax is: `!mute automute <condition (enable/disable)>`'))
    
    async def CheckTime(self, ctx, time):
        if time:
            time_stamps = ['d', 'h', 'm']
            duration_check = ''.join([x for x in time if not x.isdigit()])
            if duration_check not in time_stamps:
                await ctx.send(embed=func.ErrorEmbed("Error", "Wrong syntax, Time should be like `2m, 2h or 2d`."))
                return False
            for stamp in time_stamps:
                if stamp in time:
                    if stamp == 'h':
                        added_time = timedelta(hours=int(time.replace('h','')))
                    elif stamp == 'm':
                        added_time = timedelta(minutes=int(time.replace('m','')))
                    elif stamp == 'd':
                        added_time = timedelta(days=int(time.replace('d','')))
                    break
        else:
            added_time = timedelta(hours=2)
        if (added_time.total_seconds()/86400) >= 29:
            await ctx.send(embed=func.ErrorEmbed('Error', 'Mute time cannot be greater than 28 days.'))
            return False
        return added_time

    async def GetReason(self, ctx):
        m = await ctx.send("Now input a reason for the mute.")
        try:
            msg = await self.bot.wait_for('message', check=lambda a: a.author.id == ctx.author.id and a.channel.id == ctx.channel.id, timeout=300.0)
            return msg.content
        except asyncio.TimeoutError:
            await m.edit(content="Timeout, please run the command again.")
            return False
        
    @mute.command(aliases=['tp'])
    @func.owner_or_permissions()
    async def temp(self, ctx, member: Member, time = None):
        added_time = await self.CheckTime(ctx, time)
        if not added_time:
            return
        if not time:
            time = "2h"
        reason = await self.GetReason(ctx)
        expiry_time = datetime.now() + added_time
        await member.timeout(duration=added_time)
        embed = func.InfractionEmbed("Temporary Mute", reason, int(expiry_time.timestamp()))
        await member.send(embed=embed)
        await ctx.send(embed=func.SuccessEmbed('User Muted!', f'{member.name} was muted successfully.'))
    
    @temp.error
    async def temp_error(self, ctx, e):
        if isinstance(e, (MissingRequiredArgument, BadArgument)):
            await ctx.send(embed=func.ErrorEmbed('Syntax Error', 'Correct syntax is: `!mute temp <member> [time (like: 2m, 2h or 2d)]`'))
    
    @command()
    @func.owner_or_permissions()
    async def tmute(self, ctx, member: Member, time=None):
        await self.temp(ctx, member, time)
    
    @tmute.error
    async def tmute_error(self, ctx, e):
        if isinstance(e, (MissingRequiredArgument, BadArgument)):
            await ctx.send(embed=func.ErrorEmbed('Syntax Error', 'Correct syntax is: `!tmute <member> [time (like: 2m, 2h or 2d)]`'))

    @mute.command(aliases=['ch'])
    @func.owner_or_permissions()
    async def channel(self, ctx, member: Member, time = None):
        added_time = await self.CheckTime(ctx, time)
        if not added_time:
            return
        reason = await self.GetReason(ctx)
        if not reason:
            return
        if not time:
            time = "2h"
        expiry_time = datetime.now() + added_time
        embed = func.InfractionEmbed('Channel Mute', reason, int(expiry_time.timestamp()))
        await member.send(embed=embed)
        
        await func.DataUpdate(self.bot, "INSERT INTO mutes(guild_id, user_id, channel_id, time) VALUES($1, $2, $3, $4)", ctx.guild.id, member.id, ctx.channel.id, str(expiry_time))
        await ctx.send(embed=func.SuccessEmbed('User Muted!', f'{member.name} was muted successfully.'))
        await ctx.channel.set_permissions(member, send_messages=False)

    @channel.error
    async def channel_error(self, ctx, e):
        if isinstance(e, (MissingRequiredArgument, BadArgument)):
            await ctx.send(embed=func.ErrorEmbed('Syntax Error', 'Correct syntax is: `!mute channel [member] <time (like: 2m, 2h or 2d)>`'))

def setup(bot):
    bot.add_cog(Mute(bot))