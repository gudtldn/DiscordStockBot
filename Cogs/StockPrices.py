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

from typing import Union

from module._define_ import *

######################################################################################################################################################

async def _StockPrices_code(ctx: Union[Context, SlashContext], stock_name: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name}')

    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return

    if isinstance(ctx, SlashContext):
        await ctx.defer()
    
    ua = UserAgent()
    stock_name = stock_name.lower()
    json_data = GetUserInformation()

    try: int(stock_name) #입력받은 문자가 숫자일 경우
    except:
        if stock_name in json_data[GetArrayNum(ctx)]['StockDict'].keys():
            stock_name = json_data[GetArrayNum(ctx)]['StockDict'][stock_name]
            
        elif stock_name in GetStockDictionary().keys():
            stock_name = GetStockDictionary()[stock_name]

        else:
            url = f'https://www.google.com/search?q={quote_plus(stock_name)}+주가'
            soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')
            stock_name = soup.select_one('#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span').text
            stock_name = stock_name[0:stock_name.find('(')]
        
    url = f'https://finance.naver.com/item/main.naver?code={stock_name}'
    soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')


    title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
    description = soup.select_one('#middle > div.h_company > div.wrap_company > div > span.code').text #기업코드
    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '') #현재 시세
    lastday = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세
    lastday_per = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세%
    
    stop_trading_soup = bs(requests.get(f'https://finance.naver.com/item/sise.naver?code={stock_name}', headers={'User-agent' : ua.random}).text, 'lxml')
    stop_trading = stop_trading_soup.select_one('#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span').text #시가
    if stop_trading == '0':
        stock_time = '거래정지'
    else:
        stock_time = soup.select_one('#time > em > span').text; stock_time = stock_time[stock_time.find('(')+1:stock_time.find(')')] #장중 & 장 마감
        
    try:
        UpAndDown_soup = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2) > span.ico.up').text #+
    except:
        try:
            UpAndDown_soup = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2) > span.ico.down').text #-
        except:
            try:
                UpAndDown_soup = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2) > span.ico.sam').text #X
            except:
                try:
                    UpAndDown_soup = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4) > span.ico.plus').text #+
                except:
                    UpAndDown_soup = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4) > span.ico.minus').text #-


    UpAndDown = {'상승':'+', '하락':'-', '보합':'', '+':'+', '-':'-'}
    embed = discord.Embed(title=f'{title}({stock_time})', description=f'기업번호: {description}', color=RandomEmbedColor())
    embed.add_field(name=f'{price}원', value=f'전일대비: {UpAndDown[UpAndDown_soup]}{lastday} | {UpAndDown[UpAndDown_soup]}{lastday_per}%', inline=False)
    logger.info('Done.')
    await ctx.reply(embed=embed)

######################################################################################################################################################

class StockPrices_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name='주가',
        description='현재 주가를 검색합니다.',
        guild_ids=guilds_id,
        options=[
            create_option(
                name='이름',
                description='「검색 할 기업이름」또는「기업번호」',
                option_type=OptionType.STRING,
                required=True
            )
        ],
        connector={'이름': 'stock_name'}
    )
    async def _StockPrices(self, ctx: SlashContext, stock_name: str):
        await _StockPrices_code(ctx, stock_name)
        
    @_StockPrices.error
    async def _StockPrices_error(self, ctx, error):
        if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
            logger.warning('주식을 찾지 못하였습니다.')
            await ctx.reply('주식을 찾지 못하였습니다.')
        
        else:
            logger.warning(error)
            await ctx.send(f'{error}')

####################################################################################################

class StockPrices_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='주가', aliases=['시세'])
    async def _StockPrices(self, ctx: Context, *, stock_name: str):
        await _StockPrices_code(ctx, stock_name)
            
    @_StockPrices.error
    async def _StockPrices_error(self, ctx, error):
        if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
            logger.warning('주식을 찾지 못하였습니다.')
            await ctx.reply('주식을 찾지 못하였습니다.')

        elif isinstance(error, MissingRequiredArgument):
            logger.warning('검색할 주식을 입력해 주세요.')
            await ctx.reply('검색할 주식을 입력해 주세요.')

        else:
            logger.warning(error)
            await ctx.send(f'{error}')


######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(StockPrices_Context(bot))
    bot.add_cog(StockPrices_SlashContext(bot))