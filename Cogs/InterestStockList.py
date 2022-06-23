#관심종목

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashContext, cog_ext

from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option, create_choice

import asyncio
from aiohttp import ClientSession

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from urllib.parse import quote_plus

from typing import Union

from define import *

################################################################################ 코루틴 선언 ################################################################################

async def get_text_from_url(stock_num): #코루틴 정의
    url = f"https://finance.naver.com/item/sise.naver?code={stock_num}" #네이버 금융에 검색
    timer = time()
    
    async with ClientSession() as session:
        async with session.get(url, headers={"user-agent": UserAgent().random}) as res:
            soup = bs(await res.text(), "lxml")
            stock_name: str = soup.select_one("#middle > div.h_company > div.wrap_company > h2 > a").text #주식회사 이름
            stock_num: str = soup.select_one("#middle > div.h_company > div.wrap_company > div > span.code").text #기업코드
            price: int = int(soup.select_one("#_nowVal").text.replace(",", "")) #현재 시세
            yesterday_price: int = int(
                soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(3) > td:nth-child(4) > span").text.replace(",", "")) #어제 시세
            compared_price: int = price - yesterday_price #어제대비 가격
            compared_per: int = round((price - yesterday_price) / yesterday_price * 100, 2) #어제대비 가격%
            price_sign = "" if compared_price <= 0 else "+" #부호설정
            stock_time: str = soup.select_one("#time > em").text #기준일 (개장전, 장중, 장마감)
            date: list[int] = [int(i) for i in stock_time[:10].split(".")]
            stop_trading = soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span").text #시가
            
            if compared_price == 0:
                price_sign_img = "<:0:957290558982869053>" #보합
            elif compared_price > 0:
                price_sign_img = "<:p:957290559217762324>" #상승
            else:
                price_sign_img = "<:m:957290558857048086>" #하락
            
            logger.info(f"Done. {time() - timer}seconds")
    
    stop_trading = soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span").text #시가
    if stop_trading == "0":
        stock_time = "거래정지"
    else:
        stock_time = stock_time[stock_time.find("(")+1:stock_time.find(")")] #장중 & 장 마감
    
    return {
        "name": stock_name,
        "price": price,
        "compared_price": f"{price_sign}{compared_price:,}",
        "compared_per": f"{price_sign}{compared_per}",
        "price_sign_img": price_sign_img,
        "date": f"{date[0]}년 {date[1]}월 {date[2]}일 기준",
        "stop_trading": "(거래정지)" if stop_trading == "0" else ""
    }

################################################################################

async def get_text_(author_id):
    futures: list[asyncio.Task] = [
        asyncio.ensure_future(get_text_from_url(keyword))
            for keyword in GetUserInformation()[author_id]['InterestStock']
    ]
    return await asyncio.gather(*futures)

######################################################################################################################################################

@CommandExecutionTime
async def _Interest_Stock_List_code(ctx: Union[Context, SlashContext], option: str, input_stock_name: str):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {option} {input_stock_name}")
    
    if await CheckUser(ctx): return
    
    if isinstance(ctx, SlashContext):
        await ctx.defer(hidden=not GetUserInformation()[str(ctx.author.id)]['Settings']['ShowInterestStockList'])
    
    if option is None or option == "주가":
        if not GetUserInformation()[str(ctx.author.id)]['InterestStock']:
            logger.info("관심종목을 추가해 주세요.")
            await ctx.reply("관심종목을 추가해 주세요.")
            return
        
        async def _crawling():
            crawl_data = await get_text_(str(ctx.author.id))
            embed = Embed(title=f"{ctx.author.name}님의 관심종목", color=RandomEmbedColor())
            for _stock in crawl_data:
                embed.add_field(
                    name=f"{_stock['name']}{_stock['stop_trading']} | {_stock['price']:,}원 {_stock['price_sign_img']}",
                    value=f"전일대비: {_stock['compared_price']}원 | {_stock['compared_per']}%",
                    inline=False
                )
            embed.set_footer(text=crawl_data[0]['date'])
            return embed
        
        if isinstance(ctx, Context):
            async with ctx.typing():
                await ctx.reply(embed=await _crawling())
        else:
            await ctx.reply(embed=await _crawling())
    
    elif option == "추가":
        if input_stock_name is None:
            logger.warning("이름을 입력해 주세요.")
            await ctx.reply("이름을 입력해 주세요.")
            return
        
        elif len(GetUserInformation()[str(ctx.author.id)]['InterestStock']) == 10:
            logger.warning("관심종목은 최대 10개까지 추가할 수 있습니다.")
            await ctx.reply("관심종목은 최대 10개까지 추가할 수 있습니다.")
            return
        
        ua = UserAgent().random
        _stock_name = input_stock_name.lower()

        try: int(_stock_name) #입력받은 문자가 숫자인지 확인
        except:
            if _stock_name in GetUserInformation()[str(ctx.author.id)]['StockDict'].keys():
                _stock_name = GetUserInformation()[str(ctx.author.id)]['StockDict'][_stock_name]
                
            elif _stock_name in GetStockDictionary().keys():
                _stock_name = GetStockDictionary()[_stock_name]

            else:
                url = f"https://www.google.com/search?q={quote_plus(_stock_name)}+주가"
                soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")
                _stock_name = soup.select_one("#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span").text
                _stock_name = _stock_name[0:_stock_name.find("(")]
        
        if GetStockInformation(_stock_name) is None:
            logger.warning("주식을 찾지 못하였습니다.")
            await ctx.reply("주식을 찾지 못하였습니다.")
            return
        
        with setUserInformation() as data:
            if _stock_name in data.json_data[str(ctx.author.id)]['InterestStock']:
                logger.warning("이미 추가되어있는 주식 입니다.")
                await ctx.reply("이미 추가되어있는 주식 입니다.")
                return
            
            else:
                data.json_data[str(ctx.author.id)]['InterestStock'].append(_stock_name)
        
        logger.info("관심종목에 추가되었습니다.")
        await ctx.reply("관심종목에 추가되었습니다.")
    
    elif option == "제거":
        if input_stock_name is None:
            logger.warning("이름을 입력해 주세요.")
            await ctx.reply("이름을 입력해 주세요.")
            return
        
        if not GetUserInformation()[str(ctx.author.id)]['InterestStock']:
            logger.info("관심종목에 아무것도 없습니다.")
            await ctx.reply("관심종목에 아무것도 없습니다.")
            return
        
        ua = UserAgent().random
        _stock_name = input_stock_name.lower()

        try: int(_stock_name) #입력받은 문자가 숫자인지 확인
        except:
            if _stock_name in GetUserInformation()[str(ctx.author.id)]['StockDict'].keys():
                _stock_name: str = GetUserInformation()[str(ctx.author.id)]['StockDict'][_stock_name]
                
            elif _stock_name in GetStockDictionary().keys():
                _stock_name: str = GetStockDictionary()[_stock_name]

            else:
                url = f"https://www.google.com/search?q={quote_plus(_stock_name)}+주가"
                soup = bs(requests.get(url, headers={"User-agent": ua}).text, "lxml")
                _stock_name = soup.select_one("#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span").text
                _stock_name = _stock_name[0:_stock_name.find("(")]
        
        if GetStockInformation(_stock_name) is None:
            logger.warning("주식을 찾지 못하였습니다.")
            await ctx.reply("주식을 찾지 못하였습니다.")
            return
        
        if _stock_name in GetUserInformation()[str(ctx.author.id)]['InterestStock']:
            with setUserInformation() as data:
                logger.info(f"관심종목에서 제거되었습니다.")
                await ctx.reply(f"관심종목에서 제거되었습니다.")
                data.json_data[str(ctx.author.id)]['InterestStock'].remove(_stock_name)
            return
            
        logger.warning(f"{input_stock_name}이/가 목록에 존재하지 않습니다.")
        await ctx.reply(f"{input_stock_name}이/가 목록에 존재하지 않습니다.")
    
    else:
        logger.warning("옵션을 확인해 주세요.")
        await ctx.reply("옵션을 확인해 주세요.")
        return

######################################################################################################################################################

class InterestStockList_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="관심종목",
        description="관심이 있는 주식을 추가합니다.",
        guild_ids=guilds_id,
        options=[
            create_option(
                name="옵션",
                description="옵션을 선택해 주세요.",
                option_type=OptionType.STRING,
                required=False,
                choices=[
                    create_choice(
                        name="주가",
                        value="주가"
                    ),
                    create_choice(
                        name="추가",
                        value="추가"
                    ),
                    create_choice(
                        name="제거",
                        value="제거"
                    )
                ]
            ),
            create_option(
                name="이름",
                description="「기업이름」 또는 「기업번호」를 적어주세요.",
                option_type=OptionType.STRING,
                required=False
            )
        ],
        connector={"옵션": "option", "이름": "input_stock_name"}
    )
    async def _Interest_Stock_List(self, ctx: SlashContext, option: str=None, input_stock_name: str=None):
        await _Interest_Stock_List_code(ctx, option, input_stock_name)
    
    @_Interest_Stock_List.error
    async def _Interest_Stock_List_error(self, ctx: SlashContext, error):
        if isinstance(error, AttributeError):
            logger.warning("주식을 찾지 못하였습니다.")
            await ctx.reply("주식을 찾지 못하였습니다.")
        
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")

####################################################################################################

class InterestStockList_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="관심종목", aliases=["관심"])
    async def _Interest_Stock_List(self, ctx: Context, option: str=None, input_stock_name: str=None):
        await _Interest_Stock_List_code(ctx, option, input_stock_name)
    
    @_Interest_Stock_List.error
    async def _Interest_Stock_List_error(self, ctx: Context, error):
        if isinstance(error.original, AttributeError):
            logger.warning("주식을 찾지 못하였습니다.")
            await ctx.reply("주식을 찾지 못하였습니다.")
            
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(InterestStockList_Context(bot))
    bot.add_cog(InterestStockList_SlashContext(bot))