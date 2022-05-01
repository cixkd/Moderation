from disnake.ext.commands import Cog

from assets import functions as func

class PostGreSql(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @Cog.listener()
    async def on_ready(self):
        # Roles
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS reaction_roles(guild_id BIGINT, role_ids BIGINT[], msg_id BIGINT, channel_id BIGINT, embed_name TEXT, emojis TEXT[])")
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS short_roles(guild_id BIGINT, role_id BIGINT, time BIGINT)")
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS roles_expire(guild_id BIGINT, role_id BIGINT, time TEXT, user_id BIGINT)")
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS temp_roles(guild_id BIGINT, role_id BIGINT, time BIGINT)")
        
        #tags
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS tags(guild_id BIGINT, name TEXT, info TEXT)") 

        #spyglass
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS spyglass(guild_id BIGINT, user_id BIGINT, channel_id BIGINT, last_message BIGINT, last_channel BIGINT, all_messages BIGINT[])")

        #bans to be revoked in x amount of time
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS bans(guild_id BIGINT, user_id BIGINT, time TIME)")

        #filters (Whitelist/blacklist)
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS filters(guild_id BIGINT, trigger TEXT, type INTEGER)")

        #nickname_offences
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS nick_offences(guild_id BIGINT, user_id BIGINT, offences INTEGER)")

        #mute
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS auto_mute(guild_id BIGINT, user_id BIGINT, offences INTEGER)")
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS auto_mute_status(guild_id BIGINT, status INTEGER)")
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS mutes(guild_id BIGINT, user_id BIGINT, channel_id BIGINT, time TEXT)")

        #privilaged_roles
        await func.DataUpdate(self.bot, "CREATE TABLE IF NOT EXISTS priv_roles(guild_id BIGINT, role_id BIGINT)")

def setup(bot):
    bot.add_cog(PostGreSql(bot))