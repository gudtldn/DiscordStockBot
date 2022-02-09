#단축어설정

from discord.ext import commands
from discord_slash import SlashContext, cog_ext

from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option, create_choice

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from module._define_ import *

######################################################################################################################################################

async def _ShortenedWordSetting_code(ctx: SlashContext, setting_name: str, add_stock_name: str = None, add_stock_num: str = None):
    logger.info(f'{ctx.author.name}: {setting_name} {add_stock_name} {add_stock_num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    
    if setting_name == '목록':
        value: str = '단축어 목록:\n'
        
        for stock_name in json_data[GetArrayNum(ctx)]['StockDict']:
            value += f'{stock_name}: {json_data[GetArrayNum(ctx)]["StockDict"][stock_name]}\n'
        
        await ctx.reply(value, hidden=True)
        
    elif setting_name == '추가':
        if add_stock_num is None:
            logger.info('**기업번호**는 필수 입력 항목 입니다.')
            await ctx.reply('**기업번호**는 필수 입력 항목 입니다.', hidden=True)
            return
            
        if not add_stock_name: #add_stock_name이 None일 경우 인터넷에서 검색
            ua = UserAgent()
            url = f'https://finance.naver.com/item/main.naver?code={add_stock_num}'
            soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')
            
            add_stock_name = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text.lower() #주식회사 이름
            add_stock_num = soup.select_one('#middle > div.h_company > div.wrap_company > div > span.code').text #기업코드
            
        for i in json_data[GetArrayNum(ctx)]['StockDict']:
            if i == add_stock_name:
                logger.info('이미 추가되있는 기업입니다.')
                await ctx.reply('이미 추가되있는 기업입니다.', hidden=True)
                return
            
        json_data[GetArrayNum(ctx)]['StockDict'][add_stock_name] = add_stock_num
        SetUserInformation(json_data)
        
        logger.info(f'`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.')
        await ctx.reply(f'`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.', hidden=True)
        
    elif setting_name == '제거':
        if not add_stock_name:
            logger.info('**기업이름**는 필수 입력 항목 입니다.')
            await ctx.reply('**기업이름**는 필수 입력 항목 입니다.', hidden=True)
            return
        
        for i in json_data[GetArrayNum(ctx)]['StockDict']:
            if i == add_stock_name:
                logger.info(f'`{i}: {json_data[GetArrayNum(ctx)]["StockDict"][i]}`이/가 제거되었습니다.')
                await ctx.reply(f'`{i}: {json_data[GetArrayNum(ctx)]["StockDict"][i]}`이/가 제거되었습니다.', hidden=True)
                del(json_data[GetArrayNum(ctx)]['StockDict'][i])
                SetUserInformation(json_data)
                return
            
        logger.info(f'{add_stock_name}이/가 목록에 존재하지 않습니다.')
        await ctx.reply(f'{add_stock_name}이/가 목록에 존재하지 않습니다.', hidden=True)
        return

######################################################################################################################################################

class ShortenedWordSetting_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @cog_ext.cog_slash(
        name='단축어설정',
        description='단축어목록을 확인하거나, 추가 또는 제거합니다.',
        guild_ids=guilds_id,
        options=[
            create_option(
                name='설정이름',
                description='설정 할 옵션을 선택하세요.',
                option_type=OptionType.STRING,
                required=True,
                choices=[
                    create_choice(
                        name='목록',
                        value='목록'
                    ),
                    create_choice(
                        name='추가',
                        value='추가'
                    ),
                    create_choice(
                        name='제거',
                        value='제거'
                    )
                ]
            ),
            create_option(
                name='기업이름',
                description='설정이름이 추가 또는 제거일 때 사용할 기업이름을 입력 해 주세요.',
                option_type=OptionType.STRING,
                required=False
            ),
            create_option(
                name='기업번호',
                description='설정이름이 추가 또는 제거일 때 사용할 기업번호를 입력 해 주세요.',
                option_type=OptionType.STRING,
                required=False
            )
        ],
        connector={
            '설정이름': 'setting_name',
            '기업이름': 'add_stock_name',
            '기업번호': 'add_stock_num'
        }
    )
    async def _ShortenedWordSetting(self, ctx: SlashContext, setting_name: str, add_stock_name: str = None, add_stock_num: str = None):
        await _ShortenedWordSetting_code(ctx, setting_name, add_stock_name, add_stock_num)

    @_ShortenedWordSetting.error
    async def _ShortenedWordSetting_error(self, ctx: SlashContext, error):      
        if isinstance(error, AttributeError):
            logger.warning('존재하지 않는 기업번호입니다.')
            await ctx.reply('존재하지 않는 기업번호입니다.', hidden=True)
            
        else:
            logger.warning(f'{error}')
            await ctx.send(f'{error}', hidden=True)

######################################################################################################################################################

class ShortenedWordSetting_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(ShortenedWordSetting_SlashContext(bot))