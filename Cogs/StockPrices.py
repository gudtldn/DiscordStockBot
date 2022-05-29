#주가

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option
from discord.ext.commands.errors import MissingRequiredArgument

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from urllib.parse import quote_plus
from io import BytesIO

from random import randint

from typing import Union

from define import *
from define import _IsVaildUser

######################################################################################################################################################

@CommandExecutionTime
async def _StockPrices_code(ctx: Union[Context, SlashContext], input_stock_name: str):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {input_stock_name}")
    
    if ctx.guild is None:
        logger.info("Guild is None")
        return

    if isinstance(ctx, SlashContext):
        await ctx.defer()
    
    ua = UserAgent().random
    input_stock_name = input_stock_name.lower()

    try: int(input_stock_name) #입력받은 문자가 숫자인지 확인
    except:
        if _IsVaildUser(ctx):
            if input_stock_name in GetUserInformation()[str(ctx.author.id)]['StockDict'].keys():
                input_stock_name = GetUserInformation()[str(ctx.author.id)]['StockDict'][input_stock_name]
                
            elif input_stock_name in GetStockDictionary().keys():
                input_stock_name = GetStockDictionary()[input_stock_name]

            else:
                url = f"https://www.google.com/search?q={quote_plus(input_stock_name)}+주가"
                soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")
                input_stock_name = soup.select_one("#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span").text
                input_stock_name = input_stock_name[0:input_stock_name.find("(")]
        
        else:
            url = f"https://www.google.com/search?q={quote_plus(input_stock_name)}+주가"
            soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")
            input_stock_name = soup.select_one("#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span").text
            input_stock_name = input_stock_name[0:input_stock_name.find("(")]
    
    url = f"https://finance.naver.com/item/sise.naver?code={input_stock_name}"
    soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")

    soup_stock_name: str = soup.select_one("#middle > div.h_company > div.wrap_company > h2 > a").text #주식회사 이름
    soup_stock_num: str = soup.select_one("#middle > div.h_company > div.wrap_company > div > span.code").text #기업코드
    price: int = int(soup.select_one("#_nowVal").text.replace(",", "")) #현재 시세
    yesterday_price: int = int(soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(3) > td:nth-child(4) > span").text.replace(",", "")) #어제 시세
    compared_price: int = price - yesterday_price #어제대비 가격
    compared_per: int = round((price - yesterday_price) / yesterday_price * 100, 2) #어제대비 가격%
    price_sign = "" if compared_price <= 0 else "+" #부호설정
    stock_time: str = soup.select_one("#time > em").text #기준일 (개장전, 장중, 장마감)
    date: list[int] = [int(i) for i in stock_time[:10].split(".")]
    
    stop_trading = soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span").text #시가
    if stop_trading == "0":
        stock_time = "거래정지"
    else:
        stock_time = stock_time[stock_time.find("(")+1:stock_time.find(")")] #장중 & 장 마감
   
    chart_img = None
    embed = discord.Embed(
        title=f"{soup_stock_name}({stock_time})",
        url=f"https://finance.naver.com/item/main.naver?code={input_stock_name}",
        description=f"기업번호: {soup_stock_num}",
        color=RandomEmbedColor()
    )
    embed.add_field(name=f"{price:,}원", value=f"전일대비: {price_sign}{compared_price:,} | {price_sign}{compared_per:,}%", inline=False)
    if _IsVaildUser(ctx):
        if GetUserInformation()[str(ctx.author.id)]['Settings']['ShowStockChartImage'] == True:
            chart_img_url = f"https://ssl.pstatic.net/imgfinance/chart/item/area/day/{input_stock_name}.png?sidcode=16444779{randint(1, 99999):05}"
            img_data = BytesIO(requests.get(chart_img_url, allow_redirects=True).content)
            chart_img = discord.File(img_data, filename="chart_img.png")
            embed.set_image(url="attachment://chart_img.png")
    embed.set_footer(text=f"{date[0]}년 {date[1]}월 {date[2]}일 기준")
        
    await ctx.reply(embed=embed, file=chart_img)

######################################################################################################################################################

class StockPrices_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name="주가",
        description="현재 주가를 검색합니다.",
        guild_ids=guilds_id,
        options=[
            create_option(
                name="이름",
                description="「검색 할 기업이름」또는「기업번호」",
                option_type=OptionType.STRING,
                required=True
            )
        ],
        connector={"이름": "stock_name"}
    )
    async def _StockPrices(self, ctx: SlashContext, stock_name: str):
        await _StockPrices_code(ctx, stock_name)
        
    @_StockPrices.error
    async def _StockPrices_error(self, ctx: SlashContext, error):
        if isinstance(error, AttributeError):
            logger.warning("주식을 찾지 못하였습니다.")
            await ctx.reply("주식을 찾지 못하였습니다.")
        
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")

#################################################################################################### .주가

class StockPrices_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="주가", aliases=["시세"])
    async def _StockPrices(self, ctx: Context, *, stock_name: str):
        await _StockPrices_code(ctx, stock_name)
            
    @_StockPrices.error
    async def _StockPrices_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            logger.warning("검색할 주식을 입력해 주세요.")
            await ctx.reply("검색할 주식을 입력해 주세요.")

        elif isinstance(error.original, AttributeError):
            logger.warning("주식을 찾지 못하였습니다.")
            await ctx.reply("주식을 찾지 못하였습니다.")

        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(StockPrices_Context(bot))
    bot.add_cog(StockPrices_SlashContext(bot))