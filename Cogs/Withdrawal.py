#회원탈퇴

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.errors import MissingRequiredArgument

from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option

from typing import Union

from define import *

######################################################################################################################################################

@CommandExecutionTime
async def _Withdrawal_code(ctx: Union[Context, SlashContext], string: str):
    logger.info(f'[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {string}')
    
    if await CheckUser(ctx): return
    
    if string == '탈퇴확인':
        with setUserInformation() as data:
            del(data.json_data[str(ctx.author.id)])
        
        logger.info('회원탈퇴가 완료되었습니다.')
        await ctx.reply('회원탈퇴가 완료되었습니다.')
    
    else:
        if isinstance(ctx, Context):
            logger.info(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
            await ctx.reply(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
        else:
            logger.info('「탈퇴확인」를 입력해야 탈퇴할 수 있습니다.')
            await ctx.reply('「탈퇴확인」를 입력해야 탈퇴할 수 있습니다.')

######################################################################################################################################################

class Withdrawal_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='회원탈퇴',
        description='이 봇에 저장되있는 사용자의 정보를 삭제합니다.',
        guild_ids=guilds_id,
        options=[
            create_option(
                name='확인문구',
                description='「탈퇴확인」이라고 적어주세요.',
                option_type=OptionType.STRING,
                required=True
            )
        ],
        connector={'확인문구': 'string'}
    )
    async def _Withdrawal(self, ctx: SlashContext, string: str):
        await _Withdrawal_code(ctx, string)
        
####################################################################################################

class Withdrawal_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='회원탈퇴', aliases=['탈퇴'])
    async def _Withdrawal(self, ctx: Context, string: str):
        await _Withdrawal_code(ctx, string)
        
    @_Withdrawal.error
    async def _Withdrawal_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            logger.warning(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
            await ctx.reply(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
        
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.```{error}```")

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(Withdrawal_Context(bot))
    bot.add_cog(Withdrawal_SlashContext(bot))