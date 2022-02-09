#매수

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

from module._define_ import *

######################################################################################################################################################

async def _StockPurchase_code(ctx: Union[Context, SlashContext], stock_name: str, num: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    try: num = int(num)
    except: pass
    
    if isinstance(num, int):
        if num <= 0:
            logger.info('매수 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매수 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    stock_name = stock_name.lower()
    ua = UserAgent()
    
    if isinstance(ctx, SlashContext):
        await ctx.defer()
    
    try: int(stock_name) #입력받은 stock_name이 int인지 검사
    except: #int가 아닌경우
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
    
    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
    name = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
    stop_trading_soup = bs(requests.get(f'https://finance.naver.com/item/sise.naver?code={stock_name}', headers={'User-agent' : ua.random}).text, 'lxml')
    stop_trading = stop_trading_soup.select_one('#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span').text #시가
    if stop_trading == '0':
        logger.info(f'{name}의 주식이 거래중지 중이라 매수할 수 없습니다.')
        await ctx.reply(f'{name}의 주식이 거래중지 중이라 매수할 수 없습니다.')
        return
    
    if isinstance(num, str):
        if num in ('풀매수', '모두'):
            num = json_data[GetArrayNum(ctx)]['Deposit'] // int(price)
            if num < 1:
                logger.info('예수금이 부족합니다.')
                await ctx.reply('예수금이 부족합니다.')
                return
        
        else:
            if isinstance(ctx, Context):
                await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__」밑줄 친 부분에는「풀매수」,「모두」또는 숫자만 입력해 주세요.')
            else:
                await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[0]} __{ctx.args[1]}__」밑줄 친 부분에는「풀매수」,「모두」또는 숫자만 입력해 주세요.')
            return
        
    else:
        if json_data[GetArrayNum(ctx)]['Deposit'] - (int(price) * num) < 0:
            logger.info('예수금이 부족합니다.')
            await ctx.reply('예수금이 부족합니다.')
            return
        
    if stock_name in json_data[GetArrayNum(ctx)]['Stock'].keys(): #Stock안에 stock_name이 있는가?
        json_data[GetArrayNum(ctx)]['Stock'][stock_name] += num
    else:
        json_data[GetArrayNum(ctx)]['Stock'][stock_name] = num
    
    json_data[GetArrayNum(ctx)]['Deposit'] -= (int(price) * num) #예수금 저장
    SetUserInformation(json_data)
    
    logger.info(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    await ctx.reply(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')

######################################################################################################################################################

class StockPurchase_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name='매수',
        description='입력한 기업의 주식을 매수합니다.',
        guild_ids=guilds_id,
        options=[
            create_option(
                name='기업이름',
                description='「기업이름」 또는 「기업번호」를 적어주세요.',
                option_type=OptionType.STRING,
                required=True
            ),
            create_option(
                name='개수',
                description='「매수 할 주식 개수」 또는 「풀매수」,「모두」 를 적어주세요.',
                option_type=OptionType.STRING,
                required=True
            )
        ],
        connector={'기업이름': 'stock_name', '개수': 'num'}
    )
    async def _StockPurchase(self, ctx: SlashContext, stock_name: str, num: str):
        await _StockPurchase_code(ctx, stock_name, num)
        
    @_StockPurchase.error
    async def _StockPurchase_error(self, ctx, error):    
        if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
            logger.warning('매수하려는 주식을 찾지 못하였습니다.')
            await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
            
        elif ErrorCheck(error, "'NoneType' object has no attribute 'select_one'"):
            logger.warning('매수하려는 주식을 찾지 못하였습니다.')
            await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
            
        else:
            logger.warning(error)
            await ctx.send(f'{error}')

######################################################################################################################################################

class StockPurchase_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='매수', aliases=['구매', '주식구매', '주식매수'])
    async def _StockPurchase(self, ctx: Context, stock_name: str, num: str):
        await _StockPurchase_code(ctx, stock_name, num)

    @_StockPurchase.error
    async def _StockPurchase_error(self, ctx, error):
        if ErrorCheck(error, "stock_name is a required argument that is missing."):
            logger.warning('매수 할 주식을 입력해 주세요.')
            await ctx.reply('매수 할 주식을 입력해 주세요.')
            
        elif ErrorCheck(error, "num is a required argument that is missing."):
            logger.warning('매수 할 주식의 수를 입력해 주세요.')
            await ctx.reply('매수 할 주식의 수를 입력해 주세요.')
            
        elif ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
            logger.warning('매수하려는 주식을 찾지 못하였습니다.')
            await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
            
        elif ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'select_one'"):
            logger.warning('매수하려는 주식을 찾지 못하였습니다.')
            await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
        else:
            logger.warning(error)
            await ctx.send(f'{error}')

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(StockPurchase_Context(bot))
    bot.add_cog(StockPurchase_SlashContext(bot))