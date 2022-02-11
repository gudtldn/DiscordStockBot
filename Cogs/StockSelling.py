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

from module._define_ import *

######################################################################################################################################################

async def _StockSelling_code(ctx: Union[Context, SlashContext], stock_name: str, num: Union[int, str]):
    logger.info(f'[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    try: num = int(num)
    except: pass
    
    if isinstance(num, int):
        if num <= 0:
            logger.info('매도 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매도 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    ua = UserAgent()
    stock_name = stock_name.lower()
    
    if isinstance(ctx, SlashContext):
        await ctx.defer()
    
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

    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
    name = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
    stop_trading_soup = bs(requests.get(f'https://finance.naver.com/item/sise.naver?code={stock_name}', headers={'User-agent' : ua.random}).text, 'lxml')
    stop_trading = stop_trading_soup.select_one('#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(4) > td:nth-child(4) > span').text #시가

    if stock_name in json_data[GetArrayNum(ctx)]['Stock'].keys():
        if stop_trading == '0':
            logger.info(f'{name}의 주식이 거래중지 중이라 매도할 수 없습니다.')
            await ctx.reply(f'{name}의 주식이 거래중지 중이라 매도할 수 없습니다.')
            return
        
        if isinstance(num, str):
            if num in ('풀매도', '모두'):
                num: int = json_data[GetArrayNum(ctx)]['Stock'][stock_name] #보유주식의 수 만큼 설정
                
            elif num == '반매도':
                num: int = json_data[GetArrayNum(ctx)]['Stock'][stock_name] // 2
                if num == 0:
                    logger.info(f'매도하려는 {name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    await ctx.reply(f'매도하려는 {name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    return
                
            else:
                if isinstance(ctx, Context):
                    await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__」밑줄 친 부분에는「풀매도」,「모두」또는「반매도」또는 숫자만 입력해 주세요.')
                else:
                    await ctx.reply(f'「/{ctx.invoked_with} {ctx.args[0]} __{ctx.args[1]}__」밑줄 친 부분에는「풀매도」,「모두」또는「반매도」또는 숫자만 입력해 주세요.')
                return
        
        if num <= json_data[GetArrayNum(ctx)]['Stock'][stock_name]:
            json_data[GetArrayNum(ctx)]['Stock'][stock_name] -= num
            json_data[GetArrayNum(ctx)]['Deposit'] += (int(price) * num)
            
            if json_data[GetArrayNum(ctx)]['Stock'][stock_name] == 0:
                del(json_data[GetArrayNum(ctx)]['Stock'][stock_name])
            
            SetUserInformation(json_data)
            
            logger.info(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
            await ctx.reply(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
        else:
            logger.info(f'매도 하려는 주식개수가 현재 {name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetArrayNum(ctx)]["Stock"][stock_name]}주)')
            await ctx.reply(f'매도 하려는 주식개수가 현재 {name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetArrayNum(ctx)]["Stock"][stock_name]}주)')
            return
    else:
        logger.info(f'{name}의 주식이 자산에 없습니다.')
        await ctx.reply(f'{name}의 주식이 자산에 없습니다.')
        return

######################################################################################################################################################

class StockSelling_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name='매도',
        description='입력한 기업의 주식을 매도합니다.',
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
                description='「매도 할 주식 개수」 또는 「풀매도」,「모두」 또는 「반매도」를 적어주세요.',
                option_type=OptionType.STRING,
                required=True
            )
        ],
        connector={'기업이름': 'stock_name', '개수': 'num'}
    )
    async def _StockSelling(self, ctx: SlashContext, stock_name: str, num: str):
        await _StockSelling_code(ctx, stock_name, num)
        
    @_StockSelling.error
    async def _StockSelling_error(self, ctx, error):
        if isinstance(error, AttributeError):
            logger.warning('매도하려는 주식을 찾지 못하였습니다.')
            await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
            
        else:
            logger.warning(error)
            await ctx.send(f'{error}')

######################################################################################################################################################

class StockSelling_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='매도', aliases=['판매', '주식판매', '주식매도'])
    async def _StockSelling(self, ctx: Context, stock_name: str, num: str):
        await _StockSelling_code(ctx, stock_name, num)

    @_StockSelling.error
    async def _StockSelling_error(self, ctx, error):
        if ErrorCheck(error, "stock_name is a required argument that is missing."):
            logger.warning('매도 할 주식을 입력해 주세요.')
            await ctx.reply('매도 할 주식을 입력해 주세요.')
        
        elif ErrorCheck(error, "num is a required argument that is missing."):
            logger.warning('매도 할 주식의 수를 입력해 주세요.')
            await ctx.reply('매도 할 주식의 수를 입력해 주세요.')
            
        elif isinstance(error, AttributeError):
            logger.warning('매도하려는 주식을 찾지 못하였습니다.')
            await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
            
        else:
            logger.warning(error)
            await ctx.send(f'{error}')


######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(StockSelling_Context(bot))
    bot.add_cog(StockSelling_SlashContext(bot))