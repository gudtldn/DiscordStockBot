#지원금

from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashContext, cog_ext

from random import randint

from time import time

from typing import Union

from define import *

######################################################################################################################################################

@CommandExecutionTime
async def _SupportFund_code(ctx: Union[Context, SlashContext]):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with}")
    
    if await CheckUser(ctx): return
        
    cool_down = 3600 * 4 #쿨타임
    
    if int(time()) - GetUserInformation()[str(ctx.author.id)]['SupportFundTime'] > cool_down: #만약 저장되있는 현재시간 - 저장된시간이 cool_down을 넘는다면
        
        random_added_deposit = randint(1, 10) * 10000

        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Deposit'] += random_added_deposit
            data.json_data[str(ctx.author.id)]['SupportFund'] += random_added_deposit
            data.json_data[str(ctx.author.id)]['SupportFundTime'] = int(time())
        
        logger.info(f'{random_added_deposit:,}원이 지급되었습니다.')
        if GetUserInformation()[str(ctx.author.id)]['Settings']['ShowSupportFundCooldown']:
            cool_down_unix = GetUserInformation()[str(ctx.author.id)]['SupportFundTime'] + cool_down
            await ctx.reply(f'{random_added_deposit:,}원이 지급되었습니다.\n(다음 지원금은 <t:{cool_down_unix}:T> 이후에 받을 수 있습니다.)')
        
        else:
            await ctx.reply(f'{random_added_deposit:,}원이 지급되었습니다.')
        
    else:
        now_time = convertSecToTimeStruct(GetUserInformation()[str(ctx.author.id)]['SupportFundTime'] - int(time()) + cool_down)
        cool_down_unix = GetUserInformation()[str(ctx.author.id)]['SupportFundTime'] + cool_down
        logger.info(f'지원금을 받으려면 {now_time.hour}시간 {now_time.min}분 {now_time.sec}초를 더 기다려야 합니다. | (<t:{cool_down_unix}:T> 이후에 받을 수 있습니다.)')
        await ctx.reply(f'지원금을 받으려면 {now_time.hour}시간 {now_time.min}분 {now_time.sec}초를 더 기다려야 합니다.\n(<t:{cool_down_unix}:T> 이후에 받을 수 있습니다.)')

######################################################################################################################################################

class SupportFund_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='지원금',
        description='1만원 ~ 10만원 사이에서 랜덤으로 지원금을 지급합니다.',
        guild_ids=guilds_id,
        options=[]
    )
    async def _SupportFund(self, ctx: SlashContext):
        await _SupportFund_code(ctx)

######################################################################################################################################################

class SupportFund_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='지원금', aliases=['돈받기'])
    async def _SupportFund(self, ctx: Context):
        await _SupportFund_code(ctx)

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(SupportFund_Context(bot))
    bot.add_cog(SupportFund_SlashContext(bot))