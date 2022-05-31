#매도

from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from urllib.parse import quote_plus

from typing import Union

from define import *

######################################################################################################################################################

@CommandExecutionTime
async def _StockSelling_code(ctx: Union[Context, SlashContext], input_stock_name: str, num: Union[int, str]):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {input_stock_name} {num}")
    
    if await CheckUser(ctx): return
    
    try: num = int(num)
    except: pass
    
    if isinstance(num, int):
        if num <= 0:
            logger.info("매도 할 개수는 음수이거나 0일 수 없습니다.")
            await ctx.reply("매도 할 개수는 음수이거나 0일 수 없습니다.")
            return
    
    ua = UserAgent().random
    input_stock_name = input_stock_name.lower()
    
    if isinstance(ctx, SlashContext):
        await ctx.defer()
    
    try: int(input_stock_name) #입력받은 문자가 숫자일 경우
    except:
        if input_stock_name in GetUserInformation()[str(ctx.author.id)]['StockDict'].keys():
            input_stock_name = GetUserInformation()[str(ctx.author.id)]['StockDict'][input_stock_name]
            
        elif input_stock_name in GetStockDictionary().keys():
            input_stock_name = GetStockDictionary()[input_stock_name]
            
        else:
            url = f"https://www.google.com/search?q={quote_plus(input_stock_name)}+주가"
            soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")
            input_stock_name = soup.select_one("#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span").text
            input_stock_name = input_stock_name[0:input_stock_name.find("(")]
        
    url = f"https://finance.naver.com/item/sise.naver?code={input_stock_name}"
    soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")
    
    try:
        price: int = int(soup.select_one("#_nowVal").text.replace(",", "")) #현재 시세
    except ValueError:
        logger.warning("매수하려는 주식을 찾지 못하였습니다.")
        await ctx.reply("매수하려는 주식을 찾지 못하였습니다.")
        return
        
    soup_stock_name: str = soup.select_one("#middle > div.h_company > div.wrap_company > h2 > a").text #주식회사 이름
    stop_trading: str = soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span").text #시가

    if input_stock_name in GetUserInformation()[str(ctx.author.id)]['Stock'].keys():
        if stop_trading == "0":
            logger.info(f"{soup_stock_name}의 주식이 거래중지 중이라 매도할 수 없습니다.")
            await ctx.reply(f"{soup_stock_name}의 주식이 거래중지 중이라 매도할 수 없습니다.")
            return
        
        if isinstance(num, str):
            if num in ("풀매도", "모두"):
                num: int = GetUserInformation()[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity'] #보유주식의 수 만큼 설정
                
            elif num == "반매도":
                num: int = GetUserInformation()[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity'] // 2
                if num == 0:
                    logger.info(f"매도하려는 {soup_stock_name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.")
                    await ctx.reply(f"매도하려는 {soup_stock_name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.")
                    return
                
            else:
                if isinstance(ctx, Context):
                    await ctx.reply(f"「.{ctx.invoked_with} {ctx.args[2]} __{ctx.args[3]}__」밑줄 친 부분에는「풀매도」,「모두」또는「반매도」또는 숫자만 입력해 주세요.")
                else:
                    await ctx.reply(f"「/{ctx.invoked_with} {ctx.args[0]} __{ctx.args[1]}__」밑줄 친 부분에는「풀매도」,「모두」또는「반매도」또는 숫자만 입력해 주세요.")
                return
        
        if num <= GetUserInformation()[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity']:
            with setUserInformation() as data:
                data.json_data[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity'] -= num
                data.json_data[str(ctx.author.id)]['Deposit'] += (price * num)
                
                if data.json_data[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity'] == 0:
                    del(data.json_data[str(ctx.author.id)]['Stock'][input_stock_name])
            
            logger.info(f"{soup_stock_name}의 주식이 {price:,}원에 {num:,}주가 매도되었습니다.")
            await ctx.reply(f"{soup_stock_name}의 주식이 {price:,}원에 {num:,}주가 매도되었습니다.")
        else:
            logger.info(f"매도 하려는 주식개수가 현재 {soup_stock_name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {GetUserInformation()[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity']}주)")
            await ctx.reply(f"매도 하려는 주식개수가 현재 {soup_stock_name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {GetUserInformation()[str(ctx.author.id)]['Stock'][input_stock_name]['Quantity']}주)")
            return
    else:
        logger.info(f"{soup_stock_name}의 주식이 자산에 없습니다.")
        await ctx.reply(f"{soup_stock_name}의 주식이 자산에 없습니다.")
        return

######################################################################################################################################################

class StockSelling_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name="매도",
        description="입력한 기업의 주식을 매도합니다.",
        guild_ids=guilds_id,
        options=[
            create_option(
                name="기업이름",
                description="「기업이름」 또는 「기업번호」를 적어주세요.",
                option_type=OptionType.STRING,
                required=True
            ),
            create_option(
                name="개수",
                description="「매도 할 주식 개수」 또는 「풀매도」,「모두」 또는 「반매도」를 적어주세요.",
                option_type=OptionType.STRING,
                required=True
            )
        ],
        connector={"기업이름": "stock_name", "개수": "num"}
    )
    async def _StockSelling(self, ctx: SlashContext, stock_name: str, num: str):
        await _StockSelling_code(ctx, stock_name, num)
        
    @_StockSelling.error
    async def _StockSelling_error(self, ctx: SlashContext, error):
        if isinstance(error, AttributeError):
            logger.warning("매도하려는 주식을 찾지 못하였습니다.")
            await ctx.reply("매도하려는 주식을 찾지 못하였습니다.")
            
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")

######################################################################################################################################################

class StockSelling_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="매도", aliases=["판매", "주식판매", "주식매도"])
    async def _StockSelling(self, ctx: Context, stock_name: str, num: str):
        await _StockSelling_code(ctx, stock_name, num)

    @_StockSelling.error
    async def _StockSelling_error(self, ctx: Context, error):
        if ErrorCheck(error, "stock_name is a required argument that is missing."):
            logger.warning("매도 할 주식을 입력해 주세요.")
            await ctx.reply("매도 할 주식을 입력해 주세요.")
        
        elif ErrorCheck(error, "num is a required argument that is missing."):
            logger.warning("매도 할 주식의 수를 입력해 주세요.")
            await ctx.reply("매도 할 주식의 수를 입력해 주세요.")
            
        elif isinstance(error.original, AttributeError):
            logger.warning("매도하려는 주식을 찾지 못하였습니다.")
            await ctx.reply("매도하려는 주식을 찾지 못하였습니다.")
            
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")


######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(StockSelling_Context(bot))
    bot.add_cog(StockSelling_SlashContext(bot))