#사용자등록

from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashContext, cog_ext

from typing import Union

from define import *
from define import _IsVaildUser

######################################################################################################################################################

@CommandExecutionTime
async def _AddUser_code(ctx: Union[Context, SlashContext]):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with}")
    
    if ctx.guild is None:
        logger.info("Guild is None")
        return
    
    elif _IsVaildUser(ctx):
        logger.info("이미 등록되어 있는 사용자 입니다.")
        await ctx.reply("이미 등록되어 있는 사용자 입니다.")
        return

    with setUserInformation() as data:
        data.json_data[str(ctx.author.id)] = AddUser() #사용자 추가
        
    logger.info("등록되었습니다.")
    await ctx.reply("등록되었습니다.")

######################################################################################################################################################

class AddUser_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="사용자등록",
        description="데이터 베이스에 사용자를 등록합니다.",
        guild_ids=guilds_id,
        options=[]
    )
    async def _AddUser(self, ctx: SlashContext):
        await _AddUser_code(ctx)
        
####################################################################################################

class AddUser_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="사용자등록", aliases=["등록"])
    async def _AddUser(self, ctx: Context):
        await _AddUser_code(ctx)

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(AddUser_Context(bot))
    bot.add_cog(AddUser_SlashContext(bot))