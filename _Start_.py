import asyncio
import nest_asyncio; nest_asyncio.apply()
from functools import partial

import discord
from discord.utils import get
from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashCommand, SlashContext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.model import SlashCommandPermissionType as PermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission
from discord.ext.commands.errors import MissingRequiredArgument, CommandNotFound

import json

import time
from datetime import timedelta, datetime

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from urllib.parse import quote_plus

from platform import platform

from random import randint

from typing import Union


'''
일반, 슬래시 커맨드 코드 위치 (Ctrl + F)

통합 커맨드:
    *사용자등록
    *지원금

일반 커맨드:
    .도움말
    .주가
    .자산정보
    .매수
    .매도
    .초기화
    .회원탈퇴
    
슬래시 커맨드:
    /정보
    /설정
    
    /자산정보
    /주가
    /매수
    /매도
    /초기화
    /회원탈퇴
'''


DEBUGGING = True #디버그 실행

guilds_id=(915543134648287242, 921706352957620285, 925277183147147265)
permission_setting = {
    id: [
        create_permission(
            id=642288666156466176,
            id_type=PermissionType.USER,
            permission=True
        )
    ] for id in guilds_id
}

################################################################################ 로깅

def _Logging(): #변수의 혼용을 막기위해 함수로 만듦
    import logging

    now = str(datetime.today())[:19].replace(' ', '_', 1).replace(':', '-')

    open(f'./logs/{now}.log', 'w', encoding='utf-8').close()

    global logger
    logger = logging.getLogger()
    if DEBUGGING:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter(u'[%(asctime)s][%(levelname)s]: <%(module)s> [%(funcName)s | %(lineno)d] >> %(message)s')

    file_handler = logging.FileHandler(f'./logs/{now}.log', encoding='utf-8')
    # file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    
_Logging()

################################################################################ 기본값 설정 ################################################################################

def _InitialVarSetting():
    global operation_time, bot, slash, Token
    
    operation_time = time.time() #가동된 현재 시간

    # intents = Intents.default()
    # intents.members = True

    intents = discord.Intents.all()

    if DEBUGGING:
        game = discord.Game('봇 테스트') # ~하는 중
        bot = commands.Bot(command_prefix=';', help_command=None, status=discord.Status.do_not_disturb, activity=game, intents=intents)
    else:
        game = discord.Game('주식투자') # ~하는 중
        bot = commands.Bot(command_prefix='.', help_command=None, status=discord.Status.online, activity=game, intents=intents)

    slash = SlashCommand(bot, sync_commands=True)

    with open('./etc/Token.txt', 'r', encoding='utf-8') as Token_txt:
        Token = Token_txt.read()

_InitialVarSetting()

################################################################################ 클래스 선언 ################################################################################

class ConvertSecToTimeStruct():
    '''
    (day, hour, min, sec)
    '''
    def __init__(self, seconds: int):
        _delta = timedelta(seconds=seconds)
        self.day = _delta.days
        
        _delta = str(timedelta(seconds=_delta.seconds)).split(':')
        self.hour = int(_delta[0])
        self.min = int(_delta[1])
        self.sec = int(_delta[2])

################################################################################ 함수 선언 ################################################################################

def RandomEmbedColor():
    r = lambda: randint(0,255)
    value = f'0x{r():02x}{r():02x}{r():02x}'
    return int(value, 16)

def AddUser(ID: int):
    dictionary = {
            'UserID': ID,
            'Deposit': 10000000,
            'TotalAssets': 10000000,
            'SupportFund': 0,
            'SupportFundTime': 0,
            # 'Settings': {
            #     'InformationDisclosure': True
            # },
            # 'StockDict': {},
            'InformationDisclosure': True,
            'Stock': {}
           }
    return dictionary

def GetStockDictionary() -> dict:
    with open('./json/StockDictionary.json', 'r', encoding='utf-8') as Inf:
        return json.load(Inf)

def GetUserInformation() -> list[dict]: #Information.json에 있는 값 불러오기
    with open('./json/UserInformation.json', 'r', encoding='utf-8') as Inf:
        return json.load(Inf)

def SetUserInformation(json_data: list[dict]):
    with open('./json/UserInformation.json', 'w', encoding='utf-8') as Inf:
        json.dump(json_data, Inf, indent='\t', ensure_ascii=False)

def GetUserIDArrayNum(ctx: Union[Context, SlashContext, int]): #ctx.author.id가 들어있는 배열의 번호를 반환
    json_data = GetUserInformation()
    if isinstance(ctx, (Context, SlashContext)):
        ctx = ctx.author.id

    for num, i in enumerate(json_data):
        if i['UserID'] == ctx:
            return num
        
def IsVaildUser(ctx: Union[Context, SlashContext, int]): #ctx.author.id를 가진 유저가 Information.json에 존재하는지 여부
    json_data = GetUserInformation()
    if isinstance(ctx, (Context, SlashContext)):
        ctx = ctx.author.id
        
    for i in json_data:
        if i['UserID'] == ctx:
            return True
    return False

def ErrorCheck(error, error_context): #찾으려는 에러가 error.args에 있는지 여부
    # logger.warning(error)
    return any(error_context in i for i in error.args)

################################################################################ 자산정보 코루틴 선언 ################################################################################

async def get_text_from_url(author_id, num, stock_num):  # 코루틴 정의
    global stock_num_array
    global TotalAssets
    
    json_data = GetUserInformation()
    
    loop = asyncio.get_event_loop()
    ua = UserAgent().random

    url = f'https://finance.naver.com/item/main.naver?code={stock_num}' #네이버 금융에 검색
    request = partial(requests.get, url, headers={'user-agent': ua})
    timer = time.time()
    res = await loop.run_in_executor(None, request)
    
    soup = bs(res.text, 'lxml')
    stock_name = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text
    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
    lastday_per = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세%
    balance = json_data[GetUserIDArrayNum(author_id)]['Stock'][stock_num] #현재 주식 수량
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
    
    logger.info(f'{num} Done. {time.time() - timer}seconds')
    
    stock_num_array[num].append(f'{stock_name} | {int(price):,}원 | {UpAndDown[UpAndDown_soup]}{lastday_per}%') #['주식이름']
    stock_num_array[num].append(balance) #['주식이름', 주식수량]
    stock_num_array[num].append(int(price) * balance) #['주식이름', 주식수량, 현재시세 * 주식 수]
    
    TotalAssets += int(price) * balance #총 자산

################################################################################

async def get_text_(author_id, keywords):
    futures = []
    
    # 아직 실행된 것이 아니라, 실행할 것을 계획하는 단계
    for num, keyword in enumerate(keywords):
        futures.append(asyncio.ensure_future(get_text_from_url(author_id, num, keyword)))

    await asyncio.gather(*futures)

################################################################################ 봇 이벤트 ################################################################################

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name + " 디버깅으" if DEBUGGING else bot.user.name}로 로그인')
    print(f'{bot.user.name + " 디버깅으" if DEBUGGING else bot.user.name}로 로그인')
    
#################### 테스트중 역할 설정 ####################

    for guild in guilds_id:
        guild: discord.Guild = bot.get_guild(guild)
        role: discord.Role = get(guild.roles, name='봇 테스트 중')
        member: discord.Member
        
        if DEBUGGING:
            for member in guild.members:
                if not member.bot:
                    await member.add_roles(role)
            logger.info('added')
        else:
            for member in guild.members:
                if not member.bot:
                    await member.remove_roles(role)
            logger.info('removed')
        
################################################################################

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        logger.warning(f'{ctx.author.name}: {error}')

################################################################################ 관리자 전용 명령어 ################################################################################

################################################################################ /정보
# @commands.has_permissions(administrator=True)
@slash.slash(
    name='정보',
    description='현재 봇의 정보를 확인합니다.',
    guild_ids=guilds_id,
    options=[],
    default_permission=False,
    permissions=permission_setting
)
async def _Information(ctx: SlashContext):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with}')

    now_time = ConvertSecToTimeStruct(int(time.time() - operation_time))
    
    logger.info(f'현재 플렛폼: {platform()}, 가동시간: {now_time.day}일 {now_time.hour}시 {now_time.min}분 {now_time.sec}초, 지연시간: {bot.latency}ms')
    await ctx.reply(f'현재 플렛폼: {platform()}\n가동시간: {now_time.day}일 {now_time.hour}시 {now_time.min}분 {now_time.sec}초\n지연시간: {bot.latency}ms', hidden=True)
    
# @_Information.error
# async def _Information_error(ctx, error):
#     if isinstance(error, commands.MissingPermissions):
#         logger.warning('권한이 없습니다.')
#         await ctx.reply('권한이 없습니다.', hidden=True)
#     else:
#        logger.warning(error)
#        await ctx.reply(error, hidden=True)
        
################################################################################ /설정

@commands.has_permissions(administrator=True)
@slash.slash(
    name='설정',
    description='봇의 환경설정을 수정합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='설정이름',
            description='설정 할 옵션을 선택하세요.',
            option_type=OptionType.STRING,
            required=True,
            choices=[
                create_choice(
                    name='정보',
                    value='정보'
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
    default_permission=False,
    permissions=permission_setting,
    connector={
        '설정이름': 'setting_name',
        '기업이름': 'add_stock_name',
        '기업번호': 'add_stock_num'
    }
)
async def _BotSetting(ctx: SlashContext, setting_name: str, add_stock_name: str = None, add_stock_num: str = None):
    logger.info(f'{ctx.author.name}: {setting_name} {add_stock_name} {add_stock_num}')
    
    def SetStockDictionary(json_data: dict):
        with open('./json/StockDictionary.json', 'w', encoding='utf-8') as Inf:
            json.dump(json_data, Inf, indent='\t', ensure_ascii=False)
    
    stock_json = GetStockDictionary()
    if setting_name == '정보':
        value: str = ''
        
        for stock_name in stock_json:
            value += f'{stock_name}: {stock_json[stock_name]}\n'
                
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
            
        for i in stock_json:
            if i == add_stock_name:
                logger.info('이미 추가되있는 기업입니다.')
                await ctx.reply('이미 추가되있는 기업입니다.', hidden=True)
                return
            
        stock_json[add_stock_name] = add_stock_num
        SetStockDictionary(stock_json)
        
        logger.info(f'`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.')
        await ctx.reply(f'`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.', hidden=True)
        
    elif setting_name == '제거':
        if not add_stock_name:
            logger.info('**기업이름**는 필수 입력 항목 입니다.')
            await ctx.reply('**기업이름**는 필수 입력 항목 입니다.', hidden=True)
            return
        
        for i in stock_json:
            if i == add_stock_name:
                logger.info(f'`{i}: {stock_json[i]}`이/가 제거되었습니다.')
                await ctx.reply(f'`{i}: {stock_json[i]}`이/가 제거되었습니다.', hidden=True)
                del(stock_json[i])
                SetStockDictionary(stock_json)
                return
            
        logger.info(f'{add_stock_name}이/가 json에 존재하지 않습니다.')
        await ctx.reply(f'{add_stock_name}이/가 json에 존재하지 않습니다.', hidden=True)
        return

@_BotSetting.error
async def _BotSetting_error(ctx: SlashContext, error):
    if isinstance(error, commands.MissingPermissions):
        logger.warning('권한이 없습니다.')
        await ctx.reply('권한이 없습니다.', hidden=True)
        
    elif isinstance(error, AttributeError):
        logger.warning('존재하지 않는 기업번호입니다.')
        await ctx.reply('존재하지 않는 기업번호입니다.', hidden=True)
        
    else:
        logger.warning(f'{error}')
        await ctx.send(f'{error}', hidden=True)

################################################################################ 명령어 ################################################################################

################################################################################ *사용자등록

@slash.slash(
    name='사용자등록',
    description='데이터 베이스에 사용자를 등록합니다.',
    guild_ids=guilds_id,
    options=[]
)
@bot.command(name='사용자등록', aliases=[])
async def _AddUser(ctx: Union[Context, SlashContext]):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with}')
    
    json_data = GetUserInformation()

    if IsVaildUser(ctx):
        logger.info('이미 등록되어 있는 사용자 입니다.')
        await ctx.reply('이미 등록되어 있는 사용자 입니다.')
        return

    json_data.append(AddUser(ctx.author.id)) #사용자 추가
    SetUserInformation(json_data)
        
    logger.info('등록되었습니다.')
    await ctx.reply('등록되었습니다.')
    
################################################################################ .주가

@bot.command(name='주가', aliases=['시세'])
async def _StockPrices(ctx: Context, *, stock_name: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name}')
        
    ua = UserAgent()
    stock_name = stock_name.lower()

    try:
        int(stock_name) #입력받은 문자가 숫자일 경우
    except:
        if stock_name in GetStockDictionary().keys():
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
        
@_StockPrices.error
async def _StockPrices_error(ctx,error):
    if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.warning('주식을 찾지 못하였습니다.')
        await ctx.reply('주식을 찾지 못하였습니다.')

    elif isinstance(error, MissingRequiredArgument):
        logger.warning('검색할 주식을 입력해 주세요.')
        await ctx.reply('검색할 주식을 입력해 주세요.')

    else:
        logger.warning(error)
        await ctx.send(f'{error}')

################################################################################ /주가
    
@slash.slash(
    name='주가',
    description='현재 주가를 검색합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='이름',
            description='「검색 할 기업이름」 또는 「기업번호」',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'이름': 'stock_name'}
)
async def _StockPrices(ctx: SlashContext, stock_name: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name}')
    
    await ctx.defer() #인터렉션 타임아웃때문에 기다리기
    
    ua = UserAgent()
    stock_name = stock_name.lower()
    
    try:
        int(stock_name) #입력받은 문자가 숫자일 경우
    except:
        if stock_name in GetStockDictionary().keys():
            stock_name = GetStockDictionary()[stock_name]
        else:
            url = f'https://www.google.com/search?q={quote_plus(stock_name)}+주가'
            soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')
            stock_name = soup.select_one('#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span').text
            stock_name = stock_name[0:stock_name.find('(')]
        
    url = f'https://finance.naver.com/item/main.naver?code={stock_name}'
    soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')


    title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
    stock_num = soup.select_one('#middle > div.h_company > div.wrap_company > div > span.code').text #기업코드
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
    embed = discord.Embed(title=f'{title}({stock_time})', description=f'기업번호: {stock_num}', color=RandomEmbedColor())
    embed.add_field(name=f'{price}원', value=f'전일대비: {UpAndDown[UpAndDown_soup]}{lastday} | {UpAndDown[UpAndDown_soup]}{lastday_per}%', inline=False)
    await ctx.reply(embed=embed)
    logger.info('Done.')
        
@_StockPrices.error
async def _StockPrices_error(ctx,error):
    if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.warning('주식을 찾지 못하였습니다.')
        await ctx.reply('주식을 찾지 못하였습니다.')
    
    else:
        logger.warning(error)
        await ctx.send(f'{error}')

################################################################################ .자산정보

@bot.command(name='자산정보', aliases=['자산조회'])
async def _AssetInformation(ctx: Context, option: Union[discord.Member, str]=None): #멘션을 입력하면 자산정보 내용에 멘션된 사람의 닉네임이 나오게끔 수정
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {option}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    author_id = ctx.author.id
    
    if option is not None: #부가 옵션이 전달되어 있을 때
        if option == '공개여부':
            disclosure_status = {True:'공개', False:'비공개'}
            logger.info(f'현재 {ctx.author.name}님의 자산정보 공개여부는 「{disclosure_status[json_data[GetUserIDArrayNum(ctx)]["InformationDisclosure"]]}」로 설정되어 있습니다.')
            await ctx.reply(f'현재 {ctx.author.name}님의 자산정보 공개여부는 「{disclosure_status[json_data[GetUserIDArrayNum(ctx)]["InformationDisclosure"]]}」로 설정되어 있습니다.')
            return

        elif option in ('공개', 'true', 'True'):
            json_data[GetUserIDArrayNum(ctx)]['InformationDisclosure'] = True
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 「공개」로 설정되었습니다.')
            await ctx.reply('자산정보 공개여부가 「공개」로 설정되었습니다.')
            return
        
        elif option in ('비공개', 'false', 'False'):
            json_data[GetUserIDArrayNum(ctx)]['InformationDisclosure'] = False
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 「비공개」로 설정되었습니다.')
            await ctx.reply('자산정보 공개여부가 「비공개」로 설정되었습니다.')
            return
        
        elif option in ('랭킹', '순위'):
            members: list[discord.Member] = ctx.guild.members
            member_assets = []
            
            for member in members:
                if IsVaildUser(member.id):
                    if json_data[GetUserIDArrayNum(member.id)]['InformationDisclosure']:
                        member_assets.append((member.name, json_data[GetUserIDArrayNum(member.id)]['TotalAssets']))
                    
            member_assets.sort(key=lambda total: total[1], reverse=True) #총 자산을 기준으로 리스트 정렬
            
            embed = discord.Embed(title='자산랭킹', color=RandomEmbedColor())
            embed.set_footer(text='등록되어 있지 않은 유저, 자산정보가 비공개인 유저는 자산랭킹에 보이지 않습니다.')
            for num, asset in enumerate(member_assets):
                if num <= 10:
                    embed.add_field(name=f'{num+1}위 {asset[0]}', value=f'{asset[1]:,}원', inline=False)
                else: break
            
            await ctx.reply(embed=embed)
            return
        
        else:
            author_id: int = option.id
            user_name: str = option.name
            
            if user_name == ctx.author.name: #만약 자기 자신을 멘션했다면
                option = None
                author_id: int = ctx.author.id
            
            elif not json_data[GetUserIDArrayNum(author_id)]['InformationDisclosure']:
                logger.info(f'{user_name}님의 정보가 비공개되어 있습니다.')
                await ctx.reply(f'{user_name}님의 정보가 비공개되어 있습니다.')
                return
    
    async with ctx.typing():
        global stock_num_array
        global TotalAssets
        
        stock_num_array = [[] for i in range(len(json_data[GetUserIDArrayNum(author_id)]['Stock']))] #현재 주식 종류의 개수만큼 배열을 만듦
        TotalAssets = 0 #총 자산
        
        start_time = time.time() #크롤링 시간
        
        asyncio.get_event_loop().run_until_complete(
            get_text_(author_id, json_data[GetUserIDArrayNum(author_id)]['Stock'])
        )
        
        TotalAssets += json_data[GetUserIDArrayNum(author_id)]['Deposit'] #예수금
        
        json_data[GetUserIDArrayNum(author_id)]['TotalAssets'] = TotalAssets #다 합친걸 총 자산에 저장
        
        SetUserInformation(json_data)
        
        embed = discord.Embed(title=f'{ctx.author.name if option is None else user_name}님의 자산정보', color=RandomEmbedColor())
        embed.add_field(name='예수금', value=f'{json_data[GetUserIDArrayNum(author_id)]["Deposit"]:,}원')
        embed.add_field(name='총 자산', value=f'{json_data[GetUserIDArrayNum(author_id)]["TotalAssets"]:,}원')
        embed.add_field(name='지원금으로 얻은 돈', value=f'{json_data[GetUserIDArrayNum(author_id)]["SupportFund"]:,}원', inline=False)
        if len(json_data[GetUserIDArrayNum(author_id)]['Stock']) != 0:
            embed.add_field(name='='*25, value='_ _', inline=False)
        
        for add_embed in stock_num_array:
            embed.add_field(name=add_embed[0], value=f'잔고수량: {add_embed[1]:,} | {add_embed[2]:,}원', inline=False)
        
        logger.info(f'All Done. {time.time() - start_time} seconds')
        await ctx.reply(embed=embed)
    
@_AssetInformation.error
async def _AssetInformation_error(ctx, error):
    if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.warning('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        await ctx.reply('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        
    elif ErrorCheck(error, "Command raised an exception: NotFound: 404 Not Found (error code: 10013): Unknown User"):
        logger.warning('존재하지 않는 유저 입니다.')
        await ctx.reply('존재하지 않는 유저 입니다.')
        
    elif ErrorCheck(error, "Command raised an exception: NotFound: 404 Not Found (error code: 10007): Unknown Member"):
        logger.warning('이 서버에 없는 유저 입니다.')
        await ctx.reply('이 서버에 없는 유저 입니다.')
        
    elif ErrorCheck(error, "Command raised an exception: TypeError: list indices must be integers or slices, not NoneType"):
        logger.warning('등록되어 있지 않은 유저입니다.')
        await ctx.reply('등록되어 있지 않은 유저입니다.')
        
    elif ErrorCheck(error, f"Command raised an exception: ValueError: invalid literal for int() with base 10: '{ctx.args[1].replace('<@', '').replace('>', '')}'")or \
        ErrorCheck(error, "Command raised an exception: ValueError: invalid literal for int() with base 10: '{0}'".format(ctx.args[1].replace('@', '@\u200b'))):
        logger.warning('다시 입력해 주세요.')
        await ctx.reply('다시 입력해 주세요.')
        
    elif ErrorCheck(error, "Command raised an exception: AttributeError: 'str' object has no attribute 'id'"):
        logger.warning('다시 입력해 주세요.')
        await ctx.reply('다시 입력해 주세요.')
        
    else:
        logger.warning(error)
        await ctx.send(f'{error}')

################################################################################ /자산정보

@slash.slash(
    name='자산정보',
    description='현재 자신의 자산정보를 확인합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='유저',
            description='다른유저의 자산정보를 확인합니다.',
            option_type=OptionType.USER,
            required=False
        ),
        create_option(
            name='공개정보',
            description='현재 자산정보의 공개여부를 확인 또는 설정합니다.',
            option_type=OptionType.STRING,
            required=False,
            choices=[
                create_choice(
                    name='공개여부',
                    value='공개여부'
                ),
                create_choice(
                    name='공개',
                    value='공개'
                ),
                create_choice(
                    name='비공개',
                    value='비공개'
                )
            ]
        ),
        create_option(
            name='랭킹',
            description='이 서버의 자산랭킹을 나열합니다.',
            option_type=OptionType.STRING,
            required=False,
            choices=[
                create_choice(
                    name='랭킹',
                    value='랭킹'
                )
            ]
        )
    ],
    connector={'유저': 'option', '공개정보': 'option', '랭킹': 'option'}
)
async def _AssetInformation(ctx: SlashContext, option: Union[discord.User, str]=None):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {option}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    author_id = ctx.author.id
    
    if option is not None: #부가 옵션이 전달되어 있을 때
        if option == '공개여부':
            disclosure_status = {True:'공개', False:'비공개'}
            logger.info(f'현재 {ctx.author.name}님의 자산정보 공개여부는 「{disclosure_status[json_data[GetUserIDArrayNum(ctx)]["InformationDisclosure"]]}」로 설정되어 있습니다.')
            await ctx.reply(f'현재 {ctx.author.name}님의 자산정보 공개여부는 「{disclosure_status[json_data[GetUserIDArrayNum(ctx)]["InformationDisclosure"]]}」로 설정되어 있습니다.')
            return

        elif option in ('공개', 'true', 'True'):
            json_data[GetUserIDArrayNum(ctx)]['InformationDisclosure'] = True
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 「공개」로 설정되었습니다.')
            await ctx.reply('자산정보 공개여부가 「공개」로 설정되었습니다.')
            return
        
        elif option in ('비공개', 'false', 'False'):
            json_data[GetUserIDArrayNum(ctx)]['InformationDisclosure'] = False
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 「비공개」로 설정되었습니다.')
            await ctx.reply('자산정보 공개여부가 「비공개」로 설정되었습니다.')
            return
        
        elif option in ('랭킹', '순위'):
            members: list[discord.Member] = ctx.guild.members
            member_assets = []
            
            for member in members:
                if IsVaildUser(member.id):
                    if json_data[GetUserIDArrayNum(member.id)]['InformationDisclosure']:
                        member_assets.append((member.name, json_data[GetUserIDArrayNum(member.id)]['TotalAssets']))
                    
            member_assets.sort(key=lambda total: total[1], reverse=True) #총 자산을 기준으로 리스트 정렬
            
            embed = discord.Embed(title='자산랭킹', color=RandomEmbedColor())
            embed.set_footer(text='등록되어 있지 않은 유저, 자산정보가 비공개인 유저는 자산랭킹에 보이지 않습니다.')
            for num, asset in enumerate(member_assets):
                if num <= 10:
                    embed.add_field(name=f'{num+1}위 {asset[0]}', value=f'{asset[1]:,}원', inline=False)
                else: break
            
            await ctx.reply(embed=embed)
            return
        
        else:
            author_id: int = option.id
            user_name: str = option.name
            
            if user_name == ctx.author.name: #만약 자기 자신을 멘션했다면
                option = None
                author_id: int = ctx.author.id
            
            elif not json_data[GetUserIDArrayNum(author_id)]['InformationDisclosure']:
                logger.info(f'{user_name}님의 정보가 비공개되어 있습니다.')
                await ctx.reply(f'{user_name}님의 정보가 비공개되어 있습니다.')
                return
    
    
    hidden = not json_data[GetUserIDArrayNum(author_id)]['InformationDisclosure']
    await ctx.defer(hidden=hidden) #인터렉션 타임아웃때문에 기다리기
    
    global stock_num_array
    global TotalAssets
    
    stock_num_array = [[] for i in range(len(json_data[GetUserIDArrayNum(author_id)]['Stock']))] #현재 주식 종류의 개수만큼 배열을 만듦
    TotalAssets = 0 #총 자산
    
    start_time = time.time() #크롤링 시간
    
    asyncio.get_event_loop().run_until_complete(
        get_text_(author_id, json_data[GetUserIDArrayNum(author_id)]['Stock'])
    )
    
    TotalAssets += json_data[GetUserIDArrayNum(author_id)]['Deposit'] #예수금
    
    json_data[GetUserIDArrayNum(author_id)]['TotalAssets'] = TotalAssets #다 합친걸 총 자산에 저장
    
    SetUserInformation(json_data)
    
    embed = discord.Embed(title=f'{ctx.author.name if option is None else user_name}님의 자산정보', color=RandomEmbedColor())
    embed.add_field(name='예수금', value=f'{json_data[GetUserIDArrayNum(author_id)]["Deposit"]:,}원')
    embed.add_field(name='총 자산', value=f'{json_data[GetUserIDArrayNum(author_id)]["TotalAssets"]:,}원')
    embed.add_field(name='지원금으로 얻은 돈', value=f'{json_data[GetUserIDArrayNum(author_id)]["SupportFund"]:,}원', inline=False)
    if len(json_data[GetUserIDArrayNum(author_id)]['Stock']) != 0:
        embed.add_field(name='='*25, value='_ _', inline=False)
    
    for add_embed in stock_num_array:
        embed.add_field(name=add_embed[0], value=f'잔고수량: {add_embed[1]:,} | {add_embed[2]:,}원', inline=False)

    logger.info(f'All Done. {time.time() - start_time} seconds')
    await ctx.reply(embed=embed)
    
@_AssetInformation.error
async def _AssetInformation_error(ctx, error):
    if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.warning('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        await ctx.reply('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        
    elif ErrorCheck(error, "list indices must be integers or slices, not NoneType"):
        logger.warning('등록되어 있지 않은 유저입니다.')
        await ctx.reply('등록되어 있지 않은 유저입니다.')
        
    else:
        logger.warning(error)
        await ctx.send(f'{error}')

################################################################################ .매수

@bot.command(name='매수', aliases=['구매', '주식구매', '주식매수'])
async def _StockPurchase(ctx: Context, stock_name: str, num: Union[int, str]): #명령어, 주식이름, 개수
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if isinstance(num, int):
        if num <= 0:
            logger.info('매수 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매수 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    stock_name = stock_name.lower()
    ua = UserAgent()
    
    try: int(stock_name) #입력받은 stock_name이 int인지 검사
    except: #int가 아닌경우
        if stock_name in GetStockDictionary().keys():
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
            num = json_data[GetUserIDArrayNum(ctx)]['Deposit'] // int(price)
            if num < 1:
                logger.info('예수금이 부족합니다.')
                await ctx.reply('예수금이 부족합니다.')
                return
        
        else:
            await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__」밑줄 친 부분에는「풀매수」,「모두」또는 숫자만 입력해 주세요.')
            return
        
    else:
        if json_data[GetUserIDArrayNum(ctx)]['Deposit'] - (int(price) * num) < 0:
            logger.info('예수금이 부족합니다.')
            await ctx.reply('예수금이 부족합니다.')
            return
        
    if stock_name in json_data[GetUserIDArrayNum(ctx)]['Stock'].keys(): #Stock안에 stock_name이 있는가?
        json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] += num
    else:
        json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] = num
    
    json_data[GetUserIDArrayNum(ctx)]['Deposit'] -= (int(price) * num) #예수금 저장
    SetUserInformation(json_data)
    
    logger.info(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    await ctx.reply(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    
@_StockPurchase.error
async def _StockPurchase_error(ctx, error):
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

################################################################################ /매수

@slash.slash(
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
async def _StockPurchase(ctx: SlashContext, stock_name: str, num: Union[int, str]): #명령어, 주식이름, 개수
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if isinstance(num, int):
        if num <= 0:
            logger.info('매수 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매수 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    stock_name = stock_name.lower()
    ua = UserAgent()
    
    await ctx.defer()
    
    try: int(stock_name) #입력받은 stock_name이 int인지 검사
    except: #int가 아닌경우
        if stock_name in GetStockDictionary().keys():
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
            num = json_data[GetUserIDArrayNum(ctx)]['Deposit'] // int(price)
            if num < 1:
                logger.info('예수금이 부족합니다.')
                await ctx.reply('예수금이 부족합니다.')
                return
        
        else:
            await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[0]} __{ctx.args[1]}__」밑줄 친 부분에는「풀매수」,「모두」또는 숫자만 입력해 주세요.')
            return
        
    else:
        if json_data[GetUserIDArrayNum(ctx)]['Deposit'] - (int(price) * num) < 0:
            logger.info('예수금이 부족합니다.')
            await ctx.reply('예수금이 부족합니다.')
            return
        
    if stock_name in json_data[GetUserIDArrayNum(ctx)]['Stock'].keys(): #Stock안에 stock_name이 있는가?
        json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] += num
    else:
        json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] = num
    
    json_data[GetUserIDArrayNum(ctx)]['Deposit'] -= (int(price) * num) #예수금 저장
    SetUserInformation(json_data)
    
    logger.info(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    await ctx.reply(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    
@_StockPurchase.error
async def _StockPurchase_error(ctx, error):    
    if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.warning('매수하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, "'NoneType' object has no attribute 'select_one'"):
        logger.warning('매수하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.warning(error)
        await ctx.send(f'{error}')

################################################################################ .매도

@bot.command(name='매도', aliases=['판매', '주식판매', '주식매도'])
async def _StockSelling(ctx: Context, stock_name: str, num: Union[int, str]):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return

    if isinstance(num, int):
        if num <= 0:
            logger.info('매도 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매도 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    ua = UserAgent()
    stock_name = stock_name.lower()
    
    try: int(stock_name) #입력받은 문자가 숫자일 경우
    except:
        if stock_name in GetStockDictionary().keys():
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

    if stock_name in json_data[GetUserIDArrayNum(ctx)]['Stock'].keys():
        if stop_trading == '0':
            logger.info(f'{name}의 주식이 거래중지 중이라 매도할 수 없습니다.')
            await ctx.reply(f'{name}의 주식이 거래중지 중이라 매도할 수 없습니다.')
            return
        
        if isinstance(num, str):
            if num in ('풀매도', '모두'):
                num: int = json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] #보유주식의 수 만큼 설정
                
            elif num == '반매도':
                num: int = json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] // 2
                if num == 0:
                    logger.info(f'매도하려는 {name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    await ctx.reply(f'매도하려는 {name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    return
                
            else:
                await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__」밑줄 친 부분에는「풀매도」,「모두」또는「반매도」또는 숫자만 입력해 주세요.')
                return
        
        if num <= json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name]:
            json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] -= num
            json_data[GetUserIDArrayNum(ctx)]['Deposit'] += (int(price) * num)
            
            if json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] == 0:
                del(json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name])
            
            SetUserInformation(json_data)
            
            logger.info(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
            await ctx.reply(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
        else:
            logger.info(f'매도 하려는 주식개수가 현재 {name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx)]["Stock"][stock_name]}주)')
            await ctx.reply(f'매도 하려는 주식개수가 현재 {name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx)]["Stock"][stock_name]}주)')
            return
    else:
        logger.info(f'{name}의 주식이 자산에 없습니다.')
        await ctx.reply(f'{name}의 주식이 자산에 없습니다.')
        return
  
@_StockSelling.error
async def _StockSelling_error(ctx, error):
    if ErrorCheck(error, "stock_name is a required argument that is missing."):
        logger.warning('매도 할 주식을 입력해 주세요.')
        await ctx.reply('매도 할 주식을 입력해 주세요.')
    
    elif ErrorCheck(error, "num is a required argument that is missing."):
        logger.warning('매도 할 주식의 수를 입력해 주세요.')
        await ctx.reply('매도 할 주식의 수를 입력해 주세요.')
        
    elif ErrorCheck(error, f"Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.warning('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, f"Command raised an exception: AttributeError: 'NoneType' object has no attribute 'select_one'"):
        logger.warning('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.warning(error)
        await ctx.send(f'{error}')
        
################################################################################ /매도
        
@slash.slash(
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
async def _StockSelling(ctx: SlashContext, stock_name: str, num: Union[int, str]):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return

    if isinstance(num, int):
        if num <= 0:
            logger.info('매도 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매도 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    ua = UserAgent()
    stock_name = stock_name.lower()
    
    await ctx.defer()
    
    try: int(stock_name) #입력받은 문자가 숫자일 경우
    except:
        if stock_name in GetStockDictionary().keys():
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

    if stock_name in json_data[GetUserIDArrayNum(ctx)]['Stock'].keys():
        if stop_trading == '0':
            logger.info(f'{name}의 주식이 거래중지 중이라 매도할 수 없습니다.')
            await ctx.reply(f'{name}의 주식이 거래중지 중이라 매도할 수 없습니다.')
            return
        
        if isinstance(num, str):
            if num in ('풀매도', '모두'):
                num: int = json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] #보유주식의 수 만큼 설정
                
            elif num == '반매도':
                num: int = json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] // 2
                if num == 0:
                    logger.info(f'매도하려는 {name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    await ctx.reply(f'매도하려는 {name}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    return
                
            else:
                await ctx.reply(f'「.{ctx.invoked_with} {ctx.args[0]} __{ctx.args[1]}__」밑줄 친 부분에는「풀매도」,「모두」또는「반매도」또는 숫자만 입력해 주세요.')
                return
        
        if num <= json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name]:
            json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] -= num
            json_data[GetUserIDArrayNum(ctx)]['Deposit'] += (int(price) * num)
            
            if json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name] == 0:
                del(json_data[GetUserIDArrayNum(ctx)]['Stock'][stock_name])
            
            SetUserInformation(json_data)
            
            logger.info(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
            await ctx.reply(f'{name}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
        else:
            logger.info(f'매도 하려는 주식개수가 현재 {name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx)]["Stock"][stock_name]}주)')
            await ctx.reply(f'매도 하려는 주식개수가 현재 {name}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx)]["Stock"][stock_name]}주)')
            return
    else:
        logger.info(f'{name}의 주식이 자산에 없습니다.')
        await ctx.reply(f'{name}의 주식이 자산에 없습니다.')
        return
  
@_StockSelling.error
async def _StockSelling_error(ctx, error):
    if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.warning('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, "'NoneType' object has no attribute 'select_one'"):
        logger.warning('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.warning(error)
        await ctx.send(f'{error}')

################################################################################ *지원금

@slash.slash(
    name='지원금',
    description='1만원 ~ 10만원 사이에서 랜덤으로 지원금을 지급합니다.',
    guild_ids=guilds_id,
    options=[]
)
@bot.command(name='지원금', aliases=['돈받기'])
async def _SupportFund(ctx: Union[Context, SlashContext]):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    
    cool_down = 3600 * 4 #쿨타임
    
    if int(time.time()) - json_data[GetUserIDArrayNum(ctx)]['SupportFundTime'] > cool_down: #만약 저장되있는 현재시간 - 저장된시간이 cool_down을 넘는다면
        
        random_added_deposit = randint(1, 10) * 10000

        json_data[GetUserIDArrayNum(ctx)]['Deposit'] += random_added_deposit
        json_data[GetUserIDArrayNum(ctx)]['SupportFund'] += random_added_deposit
        json_data[GetUserIDArrayNum(ctx)]['SupportFundTime'] = int(time.time())
        
        SetUserInformation(json_data)

        logger.info(f'{random_added_deposit:,}원이 지급되었습니다.')
        await ctx.reply(f'{random_added_deposit:,}원이 지급되었습니다.')
        
    else:
        now_time = ConvertSecToTimeStruct(json_data[GetUserIDArrayNum(ctx)]['SupportFundTime'] - int(time.time()) + cool_down)
        logger.info(f'지원금을 받으려면 {now_time.hour}시간 {now_time.min}분 {now_time.sec}초를 더 기다려야 합니다.')
        await ctx.reply(f'지원금을 받으려면 {now_time.hour}시간 {now_time.min}분 {now_time.sec}초를 더 기다려야 합니다.')
    
################################################################################ .초기화

@bot.command(name='초기화', aliases=[])
async def _Initialization(ctx: Context, *, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '초기화확인':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx)])
        json_data.append(AddUser(ctx.author.id)) #사용자 추가
        SetUserInformation(json_data)
        logger.info('초기화가 완료되었습니다.')
        await ctx.reply('초기화가 완료되었습니다.')
    
    else:
        logger.info('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        await ctx.reply('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        
@_Initialization.error
async def _Initialization_error(ctx: Context, error):
    if isinstance(error, MissingRequiredArgument):
        logger.warning('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        await ctx.reply('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
    
    else:
        logger.warning(error)
        await ctx.reply(error)

################################################################################ /초기화

@slash.slash(
    name='초기화',
    description='자신의 자산을 초기화 합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='확인문구',
            description='「초기화확인」를 입력해 주세요.',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'확인문구': 'string'}
)
async def _Initialization(ctx: SlashContext, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '초기화확인':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx)])
        json_data.append(AddUser(ctx.author.id)) #사용자 추가
        SetUserInformation(json_data)
        logger.info('초기화가 완료되었습니다.')
        await ctx.reply('초기화가 완료되었습니다.')
    
    else:
        logger.info('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        await ctx.reply('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        
################################################################################ .회원탈퇴

@bot.command(name='회원탈퇴', aliases=['탈퇴'])
async def _Withdrawal(ctx: Context, *, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '탈퇴확인':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx)])
        SetUserInformation(json_data)
        logger.info('회원탈퇴가 완료되었습니다.')
        await ctx.reply('회원탈퇴가 완료되었습니다.')
    
    else:
        logger.info(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
        await ctx.reply(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')

@_Withdrawal.error
async def _Withdrawal_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        logger.warning(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
        await ctx.reply(f'「.{ctx.invoked_with} 탈퇴확인」을 입력해야 탈퇴할 수 있습니다.')
    
    else:
        logger.warning(error)
        await ctx.reply(error)

################################################################################ /회원탈퇴

@slash.slash(
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
async def _Withdrawal(ctx: SlashContext, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '탈퇴확인':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx)])
        SetUserInformation(json_data)
        logger.info('회원탈퇴가 완료되었습니다.')
        await ctx.reply('회원탈퇴가 완료되었습니다.')
    
    else:
        logger.info('「탈퇴확인」를 입력해야 탈퇴할 수 있습니다.')
        await ctx.reply('「탈퇴확인」를 입력해야 탈퇴할 수 있습니다.')

################################################################################ .도움말

@bot.command(name='도움말', aliases=['명령어', '?'])
async def _HelpCommand(ctx: Context, command: str=None):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {command}')
    
    if command is not None:
        command = command.replace('.', '')
    
    if command is None:
        embed = discord.Embed(title='도움말', description='[] <-- 필수 입력항목 | <> <-- 선택 입력항목', color=RandomEmbedColor())
        embed.add_field(name='.사용자등록', value='데이터 베이스에 사용자를 등록합니다.', inline=False)
        embed.add_field(name='.자산정보', value='현재 자신의 자산정보를 확인합니다.', inline=False)
        embed.add_field(name='.주가', value='현재 주가를 검색합니다.', inline=False)
        embed.add_field(name='.매수', value='입력한 기업의 주식을 매수합니다.', inline=False)
        embed.add_field(name='.매도', value='입력한 기업의 주식을 매도합니다.', inline=False)
        embed.add_field(name='.지원금', value='1만원 ~ 10만원 사이에서 랜덤으로 지원금을 지급합니다.', inline=False)
        embed.add_field(name='.초기화', value='자신의 자산정보를 초기화 합니다.', inline=False)
        embed.add_field(name='.탈퇴', value='이 봇에 저장되어있는 사용자의 정보를 삭제합니다.', inline=False)
        embed.set_footer(text='명령어를 자세히 보려면 「.도움말 <명령어 이름>」 을 써 주세요.')
        await ctx.reply(embed=embed)

    elif command in ('도움말', '명령어', '?'):
        command_list = ['도움말', '명령어', '?']
        command_list.remove(command)
        
        embed = discord.Embed(title='도움말', description='등록되어있는 명령어들을 출력합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        await ctx.reply(embed=embed)

    elif command == '사용자등록':
        embed = discord.Embed(title='사용자등록', description='데이터 베이스에 사용자를 등록합니다.', color=RandomEmbedColor())
        await ctx.reply(embed=embed)
    
    elif command in ('자산정보', '자산조회'):
        command_list = ['자산정보', '자산조회']
        command_list.remove(command)
        
        embed = discord.Embed(title='자산정보', description='자신의 자산정보를 확인합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        embed.add_field(name='.자산정보 <@유저>', value='@유저의 자산정보를 확인합니다.', inline=False)
        embed.add_field(name='.자산정보 <공개여부>', value='자신의 자산공개여부를 확인합니다.', inline=False)
        embed.add_field(name='.자산정보 <공개>', value='자신의 자산공개여부를 공개로 설정합니다.', inline=False)
        embed.add_field(name='.자산정보 <비공개>', value='자신의 자산공개여부를 비공개로 설정합니다.', inline=False)
        embed.add_field(name='.자산정보 <랭킹 | 순위>', value='이 서버에 있는 유저의 자산랭킹을 나열합니다.', inline=False)
        await ctx.reply(embed=embed)
    
    elif command in ('주가', '시세'):
        command_list = ['주가', '시세']
        command_list.remove(command)
        
        embed = discord.Embed(title='주가', description='검색한 기업의 현재 주가를 확인합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        embed.add_field(name='.주가 [기업이름 | 기업번호]', value='기업이름 또는 기업번호로 검색합니다.', inline=False)
        await ctx.reply(embed=embed)

    elif command in ('매수', '구매', '주식구매', '주식매수'):
        command_list = ['매수', '구매', '주식구매', '주식매수']
        command_list.remove(command)
        
        embed = discord.Embed(title='매수', description='입력한 기업의 주식을 매수합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        embed.add_field(name='.매수 [기업이름 | 기업번호] [매수 할 주식 개수]', value='입력한 기업의 주식을, 주식 개수만큼 매수합니다.', inline=False)
        embed.add_field(name='.매수 [기업이름 | 기업번호] [풀매수 | 모두]', value='입력한 기업의 주식을 최대까지 매수합니다.', inline=False)
        await ctx.reply(embed=embed)
    
    elif command in ('매도', '판매', '주식판매', '주식매도'):
        command_list = ['매도', '판매', '주식판매', '주식매도']
        command_list.remove(command)
        
        embed = discord.Embed(title='매도', description='입력한 기업의 주식을 매도합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        embed.add_field(name='.매도 [기업이름 | 기업번호] [매도 할 주식 개수]', value='입력한 기업의 주식을, 주식 개수만큼 매도합니다.', inline=False)
        embed.add_field(name='.매도 [기업이름 | 기업번호] [반매도]', value='입력한 기업의 주식의 절반을 매도합니다.', inline=False)
        embed.add_field(name='.매도 [기업이름 | 기업번호] [풀매도 | 모두]', value='입력한 기업의 주식을 모두 매도합니다.', inline=False)
        await ctx.reply(embed=embed)
    
    elif command in ('지원금', '돈받기'):
        command_list = ['지원금', '돈받기']
        command_list.remove(command)
        
        embed = discord.Embed(title='지원금', description='1만원 ~ 10만원 사이에서 랜덤으로 지급합니다. (쿨타임: 4시간)', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        await ctx.reply(embed=embed)
        
    elif command == '초기화':
        embed = discord.Embed(title='초기화', description='「초기화확인」를 입력해 자신의 자산정보를 초기화 합니다.', color=RandomEmbedColor())
        embed.add_field(name='.초기화 [확인문구]', value='확인문구에는 「초기화확인」를 입력해 주세요.')
        await ctx.reply(embed=embed)
        
    elif command in ('탈퇴', '회원탈퇴'):
        command_list = ['탈퇴', '회원탈퇴']
        command_list.remove(command)
        
        embed = discord.Embed(title='탈퇴', description='「탈퇴확인」를 입력해 저장되어있는 자신의 정보를 삭제합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value=f'{", ".join(command_list)}', inline=False)
        embed.add_field(name='.탈퇴 [확인문구]', value='확인문구에는 「탈퇴확인」를 입력해 주세요.')
        await ctx.reply(embed=embed)
        
    else:
        await ctx.reply('알 수 없는 명령어 입니다.')
        
################################################################################

bot.run(Token)