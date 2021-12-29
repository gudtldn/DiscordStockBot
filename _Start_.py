import asyncio
import nest_asyncio; nest_asyncio.apply()
from functools import partial

import discord
from discord import Intents
from discord.utils import get
from discord.ext import commands
from discord_slash import SlashCommand, context
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.model import SlashCommandPermissionType as PermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission
from discord.ext.commands.errors import MissingRequiredArgument

import json

import time
from datetime import timedelta, datetime

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from urllib.parse import quote_plus

from platform import platform

from random import randint


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


DEBUGING = True #디버그 실행

guilds_id=[915543134648287242, 921706352957620285, 925277183147147265]
permission = {
    921706352957620285: [
        create_permission(
            id=642288666156466176,
            id_type=PermissionType.USER,
            permission=True
        )
    ],
    915543134648287242: [
        create_permission(
            id=642288666156466176,
            id_type=PermissionType.USER,
            permission=True
        )
    ],
    925277183147147265: [
        create_permission(
            id=642288666156466176,
            id_type=PermissionType.USER,
            permission=True
        )
    ]
}

################################################################################ 로깅

def _Logging(): #변수의 혼용을 막기위해 함수로 만듦
    import logging

    now = str(datetime.today())[:19].replace(' ', '_', 1).replace(':', '-')

    open(f'./logs/{now}.log', 'w', encoding='utf-8').close()

    global logger
    logger = logging.getLogger()
    if DEBUGING:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter(u'%(asctime)s %(levelname)s: %(funcName)s, Line: %(lineno)d: %(message)s')

    file_handler = logging.FileHandler(f'./logs/{now}.log', encoding='utf-8')
    # file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    
_Logging()

################################################################################ 디버그용 함수 ################################################################################

from inspect import stack

def __line__():
    return stack()[1][2]

def __function__():
    return stack()[1][3]

def PrintLogger(error):
    print(f'{datetime.now()}: {stack()[1][3]}, {stack()[1][2]}번째 줄, {error}')

################################################################################ 기본값 설정 ################################################################################

operation_time = time.time() #가동된 현재 시간

# intents = Intents.default()
# intents.members = True

intents = Intents.all()

if DEBUGING:
    game = discord.Game('봇 테스트') # ~하는 중
    bot = commands.Bot(command_prefix=';', help_command=None, status=discord.Status.do_not_disturb, activity=game, intents=intents)
else:
    game = discord.Game('주식투자') # ~하는 중
    bot = commands.Bot(command_prefix='.', help_command=None, status=discord.Status.online, activity=game, intents=intents)

slash = SlashCommand(bot, sync_commands=True)

Token = open('./etc/Token.txt', 'r', encoding='utf-8').read()

################################################################################ 에러 클래스 선언 ################################################################################

class CustomError(Exception):
    pass

################################################################################ 함수 선언 ################################################################################

def RandomEmbedColor():
    r = lambda: randint(0,255)
    value = f'0x{r():02x}{r():02x}{r():02x}'
    return int(value, 16)

def AddUser_Json(Name:str, ID:int):
    dictionary = {
            'UserName' : f'{Name}',
            'UserID': ID,
            'Deposit': 10000000,
            'TotalAssets': 10000000,
            'SupportFund': 0,
            'SupportFundTime': 0,
            'InformationDisclosure': True,
            'Stock': {}
           }
    return dictionary

def GetStockDictionary() -> dict:
    with open('./json/StockDictionary.json', 'r', encoding='utf-8') as Inf:
        json_data = json.load(Inf)
    return json_data

def GetUserInformation(array_num: int = None) -> list: #Information.json에 있는 값 불러오기
    with open('./json/UserInformation.json', 'r', encoding='utf-8') as Inf:
        json_data = json.load(Inf)
        if array_num is None:
            return json_data
        else:
            return json_data[array_num]

def SetUserInformation(json_data: dict):
    with open('./json/UserInformation.json', 'w', encoding='utf-8') as Inf:
        json.dump(json_data, Inf, indent='\t', ensure_ascii=False)

def GetUserIDArrayNum(ctx=None, id=None): #ctx.author.id가 들어있는 배열의 번호를 반환
    json_data = GetUserInformation()
    
    if id is None or ctx is not None:
        for num, i in enumerate(json_data):
            if i["UserID"] == ctx.author.id:
                return num
    
    elif ctx is None or id is not None:
        for num, i in enumerate(json_data):
            if i["UserID"] == id:
                return num
            
    else:
        raise CustomError('"ctx"와 "id"둘중 하나만 입력해 주세요.')
        
def IsVaildUser(ctx): #ctx.author.id를 가진 유저가 Information.json에 존재하는지 여부
    json_data = GetUserInformation()

    for i in json_data:
        if i["UserID"] == ctx.author.id:
            return True
    return False

def ErrorCheck(error, error_context): #찾으려는 에러가 error.args에 있는지 여부
    logger.error(error)
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
    balance = json_data[GetUserIDArrayNum(id=author_id)]["Stock"][stock_num] #현재 주식 수량
    
    logger.info(f'{num} Done. {time.time() - timer}seconds')
    
    stock_num_array[num].append(stock_name) #['주식이름']
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
    logger.info(f'{bot.user.name + " 디버깅으" if DEBUGING else bot.user.name}로 로그인')
    print(f'{bot.user.name + " 디버깅으" if DEBUGING else bot.user.name}로 로그인')
    
#################### 테스트중 역할 설정 ####################

    for guild in guilds_id:
        guild: discord.Guild = bot.get_guild(guild)
        role: discord.Role = get(guild.roles, name="봇 테스트 중")
        member: discord.Member
        
        if DEBUGING:
            for member in guild.members:
                if not member.bot:
                    await member.add_roles(role)
        else:
            for member in guild.members:
                if not member.bot:
                    await member.remove_roles(role)
        
################################################################################

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logger.error(error)

################################################################################ 관리자 전용 명령어 ################################################################################

################################################################################ /정보
# @commands.has_permissions(administrator=True)
@slash.slash(
    name='정보',
    description='현재 봇의 정보를 확인합니다.',
    guild_ids=guilds_id,
    options=[],
    default_permission=False,
    permissions=permission
)
async def _Information(ctx: context.SlashContext):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with}')

    now_operation_time = int(time.time() - operation_time)
    now_timedelta = timedelta(seconds=now_operation_time)
    
    logger.info(f'현재 플렛폼: {platform()}, 가동시간: {now_timedelta.days}일 {str(now_timedelta)[-8:-6]}시 {str(now_timedelta)[-5:-3]}분 {str(now_timedelta)[-2:]}초, 지연시간: {bot.latency}ms')
    await ctx.reply(f'현재 플렛폼: {platform()}\n가동시간: {now_timedelta.days}일 {str(now_timedelta)[-8:-6]}시 {str(now_timedelta)[-5:-3]}분 {str(now_timedelta)[-2:]}초\n지연시간: {bot.latency}ms', hidden=True)
    
# @_Information.error
# async def _Information_error(ctx, error):
#     if isinstance(error, commands.MissingPermissions):
#         logger.error('권한이 없습니다.')
#         await ctx.reply('권한이 없습니다.', hidden=True)
#     else:
#         PrintLogger(error)
        
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
    permissions=permission,
    connector={
        '설정이름': 'setting_name',
        '기업이름': 'add_stock_name',
        '기업번호': 'add_stock_num'
    }
)
async def _BotSetting(ctx: context.SlashContext, setting_name: str, add_stock_name: str = None, add_stock_num: str = None):
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
            logger.warning('**기업번호**는 필수 입력 항목 입니다.')
            return await ctx.reply('**기업번호**는 필수 입력 항목 입니다.', hidden=True)
            
        if not add_stock_name: #add_stock_name이 None일 경우 인터넷에서 검색
            ua = UserAgent()
            url = f'https://finance.naver.com/item/main.naver?code={add_stock_num}'
            soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')
            
            add_stock_name = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
            add_stock_num = soup.select_one('#middle > div.h_company > div.wrap_company > div > span.code').text #기업코드
            
        for i in stock_json:
            if i == add_stock_name:
                logger.warning('이미 추가되있는 기업입니다.')
                return await ctx.reply('이미 추가되있는 기업입니다.', hidden=True)
            
        stock_json[add_stock_name] = add_stock_num
        SetStockDictionary(stock_json)
        
        logger.info(f'`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.')
        await ctx.reply(f'`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.', hidden=True)
        
    elif setting_name == '제거':
        if not add_stock_name:
            logger.warning('**기업이름**는 필수 입력 항목 입니다.')
            return await ctx.reply('**기업이름**는 필수 입력 항목 입니다.', hidden=True)
        
        for i in stock_json:
            if i == add_stock_name:
                logger.info(f'`{i}: {stock_json[i]}`이/가 제거되었습니다.')
                await ctx.reply(f'`{i}: {stock_json[i]}`이/가 제거되었습니다.', hidden=True)
                del(stock_json[i])
                SetStockDictionary(stock_json)
                return
            
        logger.warning(f'{add_stock_name}이/가 json에 존재하지 않습니다.')
        return await ctx.reply(f'{add_stock_name}이/가 json에 존재하지 않습니다.', hidden=True)

@_BotSetting.error
async def _BotSetting_error(ctx: context.SlashContext, error):
    if isinstance(error, commands.MissingPermissions):
        logger.error('권한이 없습니다.')
        await ctx.reply('권한이 없습니다.', hidden=True)
        
    elif isinstance(error, AttributeError):
        logger.error('존재하지 않는 기업번호입니다.')
        await ctx.reply('존재하지 않는 기업번호입니다.', hidden=True)
        
    else:
        logger.error(f'{type(error)}: {error}')
        await ctx.send(f'{type(error)}: {error}', hidden=True)

################################################################################ 명령어 ################################################################################

################################################################################ *사용자등록

@slash.slash(
    name='사용자등록',
    description='데이터 베이스에 사용자를 등록합니다.',
    guild_ids=guilds_id,
    options=[]
)
@bot.command(name='사용자등록', aliases=[])
async def _AddUser(ctx):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with}')
    
    json_data = GetUserInformation()

    if IsVaildUser(ctx):
        logger.warning('이미 등록되어 있는 사용자 입니다.')
        return await ctx.reply('이미 등록되어 있는 사용자 입니다.')

    json_data.append(AddUser_Json(ctx.author.name, ctx.author.id)) #사용자 추가
    SetUserInformation(json_data)
        
    logger.info('등록되었습니다.')
    await ctx.reply('등록되었습니다.')
    
################################################################################ .주가

@bot.command(name='주가', aliases=['시세'])
async def _StockPrices(ctx: commands.context.Context, *, txt: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {txt}')
        
    ua = UserAgent()
    
    async with ctx.typing():
    
        try:
            int(txt) #입력받은 문자가 숫자일 경우
        except:
            if txt in GetStockDictionary().keys():
                txt = GetStockDictionary()[txt]
            else:
                url = f'https://www.google.com/search?q={quote_plus(txt)}+주가'
                soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')
                txt = soup.select_one('#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span').text
                txt = txt[0:txt.find('(')]
            
        url = f'https://finance.naver.com/item/main.naver?code={txt}'
        soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')


        title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
        description = soup.select_one('#middle > div.h_company > div.wrap_company > div > span.code').text #기업코드
        price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '') #현재 시세
        lastday = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세
        lastday_per = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세%
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
        embed = discord.Embed(title=title, description=f'기업번호: {description}', color=RandomEmbedColor())
        embed.add_field(name=f'{price}원', value=f'전일대비: {UpAndDown[UpAndDown_soup]}{lastday} | {UpAndDown[UpAndDown_soup]}{lastday_per}%', inline=False)
        logger.info('Done.')
        await ctx.send(embed=embed)
        
@_StockPrices.error
async def _StockPrices_error(ctx,error):
    PrintLogger(error)
    
    if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.error('주식을 찾지 못하였습니다.')
        await ctx.reply('주식을 찾지 못하였습니다.')

    elif isinstance(error, MissingRequiredArgument):
        logger.error('검색할 주식을 입력해 주세요.')
        await ctx.reply('검색할 주식을 입력해 주세요.')

    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ /주가
    
@slash.slash(
    name='주가',
    description='현재 주가를 검색합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='이름',
            description='검색 할 기업이름 또는 기업번호',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'이름': 'txt'}
)
async def _StockPrices(ctx: context.SlashContext, txt: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {txt}')
    
    await ctx.defer() #인터렉션 타임아웃때문에 기다리기
    
    ua = UserAgent()
    
    try:
        int(txt) #입력받은 문자가 숫자일 경우
    except:
        if txt in GetStockDictionary().keys():
            txt = GetStockDictionary()[txt]
        else:
            url = f'https://www.google.com/search?q={quote_plus(txt)}+주가'
            soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')
            txt = soup.select_one('#main > div:nth-child(6) > div > div:nth-child(3) > div > div > div > div > div:nth-child(2) > div > div > div > div > span').text
            txt = txt[0:txt.find('(')]
        
    url = f'https://finance.naver.com/item/main.naver?code={txt}'
    soup = bs(requests.get(url, headers={'User-agent' : ua.random}).text, 'lxml')


    title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
    description = soup.select_one('#middle > div.h_company > div.wrap_company > div > span.code').text #기업코드
    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '') #현재 시세
    lastday = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(2)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세
    lastday_per = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세%
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
    embed = discord.Embed(title=title, description=f'기업번호: {description}', color=RandomEmbedColor())
    embed.add_field(name=f'{price}원', value=f'전일대비: {UpAndDown[UpAndDown_soup]}{lastday} | {UpAndDown[UpAndDown_soup]}{lastday_per}%', inline=False)
    await ctx.send(embed=embed)
    logger.info('Done.')
        
@_StockPrices.error
async def _StockPrices_error(ctx,error):
    PrintLogger(error)
        
    if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.error('주식을 찾지 못하였습니다.')
        await ctx.reply('주식을 찾지 못하였습니다.')
    
    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ .자산정보

@bot.command(name='자산정보', aliases=['자산조회'])
async def _AssetInformation(ctx: commands.context.Context, *mention): #멘션을 입력하면 자산정보 내용에 멘션된 사람의 닉네임이 나오게끔 수정
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {mention}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    
    if len(mention) != 0:
        if mention[0] == '공개여부':
            disclosure_status = {True:'공개', False:'비공개'}
            logger.warning(f'현재 {ctx.author.name}님의 자산정보 공개여부는 "{disclosure_status[json_data[GetUserIDArrayNum(ctx=ctx)]["InformationDisclosure"]]}"로 설정되어 있습니다.')
            return await ctx.reply(f'현재 {ctx.author.name}님의 자산정보 공개여부는 "{disclosure_status[json_data[GetUserIDArrayNum(ctx=ctx)]["InformationDisclosure"]]}"로 설정되어 있습니다.')

        elif mention[0] in ('공개', 'true', 'True'):
            json_data[GetUserIDArrayNum(ctx=ctx)]['InformationDisclosure'] = True
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 "공개"로 설정되었습니다.')
            return await ctx.reply('자산정보 공개여부가 "공개"로 설정되었습니다.')
        
        elif mention[0] in ('비공개', 'false', 'False'):
            json_data[GetUserIDArrayNum(ctx=ctx)]['InformationDisclosure'] = False
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 "비공개"로 설정되었습니다.')
            return await ctx.reply('자산정보 공개여부가 "비공개"로 설정되었습니다.')
        
        else:
            mention : str = mention[0]
            author_id = int(mention.replace('<@', '').replace('!', '').replace('>', ''))
            user_name = str(await ctx.guild.fetch_member(author_id))
            user_name = user_name[:user_name.find('#')]
            if user_name == ctx.author.name:
                mention = None
                author_id : int = ctx.author.id
                
            elif not json_data[GetUserIDArrayNum(id=author_id)]['InformationDisclosure']:
                logger.warning(f'{user_name}님의 정보가 비공개되어 있습니다.')
                return await ctx.reply(f'{user_name}님의 정보가 비공개되어 있습니다.')
    else:
        mention = None
        author_id = ctx.author.id
        
    async with ctx.typing():
    
        global stock_num_array
        global TotalAssets
        
        stock_num_array = [[] for i in range(len(json_data[GetUserIDArrayNum(id=author_id)]['Stock']))] #현재 주식 종류의 개수만큼 배열을 만듦
        TotalAssets = 0 #총 자산
        
        start_time = time.time() #크롤링 시간
        
        asyncio.get_event_loop().run_until_complete(
            get_text_(author_id, json_data[GetUserIDArrayNum(id=author_id)]['Stock'])
        )
            
        TotalAssets += json_data[GetUserIDArrayNum(id=author_id)]['Deposit'] #예수금
        
        json_data[GetUserIDArrayNum(id=author_id)]['TotalAssets'] = TotalAssets #다 합친걸 총 자산에 저장
        
        SetUserInformation(json_data)
        
        embed = discord.Embed(title=f'{ctx.author.name if mention is None else user_name}님의 자산정보', color=RandomEmbedColor())
        embed.add_field(name='예수금', value=f'{json_data[GetUserIDArrayNum(id=author_id)]["Deposit"]:,}원')
        embed.add_field(name='총 자산', value=f'{json_data[GetUserIDArrayNum(id=author_id)]["TotalAssets"]:,}원')
        embed.add_field(name='지원금으로 얻은 돈', value=f'{json_data[GetUserIDArrayNum(id=author_id)]["SupportFund"]:,}원', inline=False)
        if len(json_data[GetUserIDArrayNum(id=author_id)]['Stock']) != 0:
            embed.add_field(name='='*25, value='_ _', inline=False)
        
        for add_embed in stock_num_array:    
            embed.add_field(name=add_embed[0], value=f'잔고수량: {add_embed[1]:,} | {add_embed[2]:,}원', inline=False)
            
        # await ctx.send(f'걸린시간: {time.time() - start_time} 초') #디버그
        # print(f'{time.time() - start_time} seconds')
        logger.info(f'All Done. {time.time() - start_time} seconds')
        await ctx.reply(embed=embed)
    
@_AssetInformation.error
async def _AssetInformation_error(ctx, error):
    PrintLogger(error)

    if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.error('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        await ctx.reply('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        
    elif ErrorCheck(error, "Command raised an exception: NotFound: 404 Not Found (error code: 10013): Unknown User"):
        logger.error('존재하지 않는 유저 입니다.')
        await ctx.reply('존재하지 않는 유저 입니다.')
        
    elif ErrorCheck(error, "Command raised an exception: NotFound: 404 Not Found (error code: 10007): Unknown Member"):
        logger.error('이 서버에 없는 유저 입니다.')
        await ctx.reply('이 서버에 없는 유저 입니다.')
        
    elif ErrorCheck(error, f"Command raised an exception: ValueError: invalid literal for int() with base 10: '{ctx.args[1].replace('<@', '').replace('>', '')}'")or \
        ErrorCheck(error, "Command raised an exception: ValueError: invalid literal for int() with base 10: '{0}'".format(ctx.args[1].replace('@', '@\u200b'))):
        logger.error('다시 입력해 주세요.')
        await ctx.reply('다시 입력해 주세요.')
        
    elif ErrorCheck(error, "Command raised an exception: TypeError: list indices must be integers or slices, not NoneType"):
        logger.error('등록되어 있지 않은 유저입니다.')
        await ctx.reply('등록되어 있지 않은 유저입니다.')
        
    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ /자산정보

@slash.slash(
    name='자산정보',
    description='현재 자신의 자산정보를 확인합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='유저',
            description='유저의 현재 자산정보를 확인합니다.',
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
        )
    ],
    connector={'유저': 'mention', '공개정보': 'mention'}
)
async def _AssetInformation(ctx: context.SlashContext, mention=None): #멘션을 입력하면 자산정보 내용에 멘션된 사람의 닉네임이 나오게끔 수정
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {mention}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    
    if mention is not None:
        try: mention: str = mention.mention
        except: pass
        
        if mention == '공개여부':
            disclosure_status = {True:'공개', False:'비공개'}
            logger.warning(f'현재 {ctx.author.name}님의 자산정보 공개여부는 "{disclosure_status[json_data[GetUserIDArrayNum(ctx=ctx)]["InformationDisclosure"]]}"로 설정되어 있습니다.')
            return await ctx.reply(f'현재 {ctx.author.name}님의 자산정보 공개여부는 "{disclosure_status[json_data[GetUserIDArrayNum(ctx=ctx)]["InformationDisclosure"]]}"로 설정되어 있습니다.')

        elif mention in ('공개', 'true', 'True'):
            json_data[GetUserIDArrayNum(ctx=ctx)]['InformationDisclosure'] = True
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 "공개"로 설정되었습니다.')
            return await ctx.reply('자산정보 공개여부가 "공개"로 설정되었습니다.')
        
        elif mention in ('비공개', 'false', 'False'):
            json_data[GetUserIDArrayNum(ctx=ctx)]['InformationDisclosure'] = False
            SetUserInformation(json_data)
            logger.info('자산정보 공개여부가 "비공개"로 설정되었습니다.')
            return await ctx.reply('자산정보 공개여부가 "비공개"로 설정되었습니다.')
        
        else:
            author_id = int(mention.replace('<@', '').replace('!', '').replace('>', ''))
            user_name = str(await ctx.guild.fetch_member(author_id))
            user_name = user_name[:user_name.find('#')]
            if user_name == ctx.author.name:
                mention = None
                author_id : int = ctx.author.id
                
            elif not json_data[GetUserIDArrayNum(id=author_id)]['InformationDisclosure']:
                logger.warning(f'{user_name}님의 정보가 비공개되어 있습니다.')
                return await ctx.reply(f'{user_name}님의 정보가 비공개되어 있습니다.')
    else:
        author_id = ctx.author.id
    
    hidden = not json_data[GetUserIDArrayNum(ctx=ctx)]["InformationDisclosure"]
    await ctx.defer(hidden=hidden) #인터렉션 타임아웃때문에 기다리기
    
    global stock_num_array
    global TotalAssets
    
    stock_num_array = [[] for i in range(len(json_data[GetUserIDArrayNum(id=author_id)]['Stock']))] #현재 주식 종류의 개수만큼 배열을 만듦
    TotalAssets = 0 #총 자산
    
    start_time = time.time() #크롤링 시간
    
    asyncio.get_event_loop().run_until_complete(
        get_text_(author_id, json_data[GetUserIDArrayNum(id=author_id)]['Stock'])
    )
        
    TotalAssets += json_data[GetUserIDArrayNum(id=author_id)]["Deposit"] #예수금
    
    json_data[GetUserIDArrayNum(id=author_id)]["TotalAssets"] = TotalAssets #다 합친걸 총 자산에 저장
    
    SetUserInformation(json_data)
    
    embed = discord.Embed(title=f'{ctx.author.name if mention is None else user_name}님의 자산정보', color=RandomEmbedColor())
    embed.add_field(name='예수금', value=f'{json_data[GetUserIDArrayNum(id=author_id)]["Deposit"]:,}원')
    embed.add_field(name='총 자산', value=f'{json_data[GetUserIDArrayNum(id=author_id)]["TotalAssets"]:,}원')
    embed.add_field(name='지원금으로 얻은 돈', value=f'{json_data[GetUserIDArrayNum(id=author_id)]["SupportFund"]:,}원', inline=False)
    if len(json_data[GetUserIDArrayNum(id=author_id)]['Stock']) != 0:
        embed.add_field(name='='*25, value='_ _', inline=False)
    
    for add_embed in stock_num_array:    
        embed.add_field(name=add_embed[0], value=f'잔고수량: {add_embed[1]:,} | {add_embed[2]:,}원', inline=False)
    
    await ctx.reply(embed=embed)
    # await ctx.send(f'걸린시간: {time.time() - start_time} 초') #디버그
    # print(f'{time.time() - start_time} seconds')
    logger.info(f'All Done. {time.time() - start_time} seconds')
    
@_AssetInformation.error
async def _AssetInformation_error(ctx, error):
    PrintLogger(error)

    if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.error('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        await ctx.reply('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
        
    elif ErrorCheck(error, "list indices must be integers or slices, not NoneType"):
        logger.error('등록되어 있지 않은 유저입니다.')
        await ctx.reply('등록되어 있지 않은 유저입니다.')
        
    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ .매수

@bot.command(name='매수', aliases=['구매', '주식구매', '주식매수'])
async def _StockPurchase(ctx: commands.context.Context, stock_name: str, num: str): #명령어, 주식이름, 개수
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if num != '풀매수':
        num = int(num)
        
        if num <= 0:
            logger.warning('매수 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매수 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    
    ua = UserAgent()
    
    async with ctx.typing():
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

        price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
        title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
        
        if num == '풀매수':
            num = json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] / int(price)
            if num < 1:
                logger.warning('예수금이 부족합니다.')
                return await ctx.reply('예수금이 부족합니다.')
            else:
                num = int(num)
        
        elif json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] - (int(price) * num) < 0:
            logger.warning('예수금이 부족합니다.')
            return await ctx.reply('예수금이 부족합니다.')

        if any(stock_name in i for i in list(json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"].keys())): #Stock안에 corporation_num이 있는가?
            json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name] += num
        else:
            json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name] = num
        
        json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] -= (int(price) * num) #예수금 저장
        SetUserInformation(json_data)
        
        logger.info(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
        await ctx.reply(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    
@_StockPurchase.error
async def _StockPurchase_error(ctx, error):
    PrintLogger(error)
    
    if ErrorCheck(error, "stock_name is a required argument that is missing."):
        logger.error('매수 할 주식을 입력해 주세요.')
        await ctx.reply('매수 할 주식을 입력해 주세요.')
        
    elif ErrorCheck(error, "num is a required argument that is missing."):
        logger.error('매수 할 주식의 수를 입력해 주세요.')
        await ctx.reply('매수 할 주식의 수를 입력해 주세요.')
        
    elif ErrorCheck(error, f"Command raised an exception: ValueError: invalid literal for int() with base 10: '{ctx.args[2]}'"):
        logger.error(f'"{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__" 밑줄 친 부분에는 숫자만 입력해 주세요.')
        await ctx.reply(f'"{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__" 밑줄 친 부분에는 숫자만 입력해 주세요.')
        
    elif ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.error('매수하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'select_one'"):
        logger.error('매수하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ /매수

@slash.slash(
    name='매수',
    description='입력한 기업의 주식을 매수합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='기업이름',
            description='"기업이름" 또는 "기업번호"를 적어주세요.',
            option_type=OptionType.STRING,
            required=True
        ),
        create_option(
            name='개수',
            description='"매수 할 주식 개수" 또는 "풀매수"를 적어주세요.',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'기업이름': 'stock_name', '개수': 'num'}
)
async def _StockPurchase(ctx: context.SlashContext, stock_name: str, num: str): #명령어, 주식이름, 개수
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if num != '풀매수':
        num = int(num)
        
        if num <= 0:
            logger.warning('매수 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매수 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    
    ua = UserAgent()
    
    await ctx.defer() #인터렉션 타임아웃때문에 기다리기
    
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

    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
    title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름
    
    if num == '풀매수':
        num = json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] / int(price)
        if num < 1:
            logger.warning('예수금이 부족합니다.')
            return await ctx.reply('예수금이 부족합니다.')
        else:
            num = int(num)
    
    elif json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] - (int(price) * num) < 0:
        logger.warning('예수금이 부족합니다.')
        return await ctx.reply('예수금이 부족합니다.')

    # print(any(str(stock_name) in i for i in list(json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"].keys())))

    if any(stock_name in i for i in list(json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"].keys())): #Stock안에 corporation_num이 있는가?
        json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name] += num
    else:
        json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name] = num
    
    json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] -= (int(price) * num) #예수금 저장
    SetUserInformation(json_data)
    
    logger.info(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    await ctx.reply(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매수되었습니다.')
    
@_StockPurchase.error
async def _StockPurchase_error(ctx, error):
    PrintLogger(error)
        
    if ErrorCheck(error, f"invalid literal for int() with base 10: '{ctx.args[1]}'"):
        logger.error('`매수 할 주식개수(숫자만)` 또는 `풀매수`만 입력해 주세요.')
        await ctx.reply('`매수 할 주식개수(숫자만)` 또는 `풀매수`만 입력해 주세요.')
        
    elif ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.error('매수하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, "'NoneType' object has no attribute 'select_one'"):
        logger.error('매수하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매수하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ .매도

@bot.command(name='매도', aliases=['판매', '주식판매', '주식매도'])
async def _StockSelling(ctx: commands.context.Context, stock_name: str, num: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return

    if num not in ('풀매도', '반매도'):
        num = int(num)
        
        if num <= 0:
            logger.warning('매도 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매도 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    
    ua = UserAgent()
    
    async with ctx.typing():
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

        price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
        title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름

        if any(stock_name in i for i in list(json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'].keys())):
            if num == '풀매도':
                num = json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] #보유주식의 수 만큼 설정
                
            elif num == '반매도':
                num = json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] // 2
                if num == 0:
                    logger.warning(f'매도하려는 {title}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                    return await ctx.reply(f'매도하려는 {title}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                
            
            if num <= json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name]:
                json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] -= num
                json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] += (int(price) * num)
                
                if json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] == 0:
                    del(json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name])
                
                SetUserInformation(json_data)
                
                logger.info(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
                await ctx.reply(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
            else:
                logger.warning(f'매도 하려는 주식개수가 현재 {title}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name]}주)')
                return await ctx.reply(f'매도 하려는 주식개수가 현재 {title}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name]}주)')
        else:
            logger.warning(f'{title}의 주식이 자산에 없습니다.')
            return await ctx.reply(f'{title}의 주식이 자산에 없습니다.')
  
@_StockSelling.error
async def _StockSelling_error(ctx, error):
    PrintLogger(error)
    
    if ErrorCheck(error, "stock_name is a required argument that is missing."):
        logger.error('매도 할 주식을 입력해 주세요.')
        await ctx.reply('매도 할 주식을 입력해 주세요.')
    
    elif ErrorCheck(error, "num is a required argument that is missing."):
        logger.error('매도 할 주식의 수를 입력해 주세요.')
        await ctx.reply('매도 할 주식의 수를 입력해 주세요.')
    
    elif ErrorCheck(error, f"Command raised an exception: ValueError: invalid literal for int() with base 10: '{ctx.args[2]}'"):
        logger.error(f'"{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__" 밑줄 친 부분에는 숫자만 입력해 주세요.')
        await ctx.reply(f'"{ctx.invoked_with} {ctx.args[1]} __{ctx.args[2]}__" 밑줄 친 부분에는 숫자만 입력해 주세요.')
        
    elif ErrorCheck(error, f"Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
        logger.error('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, f"Command raised an exception: AttributeError: 'NoneType' object has no attribute 'select_one'"):
        logger.error('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.error(error)
        await ctx.send(f'{error}')
        
################################################################################ /매도
        
@slash.slash(
    name='매도',
    description='입력한 기업의 주식을 매도합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='기업이름',
            description='"기업이름" 또는 "기업번호"를 적어주세요.',
            option_type=OptionType.STRING,
            required=True
        ),
        create_option(
            name='개수',
            description='"매도 할 주식 개수" 또는 "풀매도" 또는 "반매도"를 적어주세요.',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'기업이름': 'stock_name', '개수': 'num'}
)
async def _StockSelling(ctx: context.SlashContext, stock_name: str, num: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {stock_name} {num}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return

    if num not in ('풀매도', '반매도'):
        num = int(num)
        
        if num <= 0:
            logger.warning('매도 할 개수는 음수이거나 0일 수 없습니다.')
            await ctx.reply('매도 할 개수는 음수이거나 0일 수 없습니다.')
            return
    
    json_data = GetUserInformation()
    
    ua = UserAgent()
    
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

    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
    title = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text #주식회사 이름

    if any(stock_name in i for i in list(json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'].keys())):
        if num == '풀매도':
            num = json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] #보유주식의 수 만큼 설정
            
        elif num == '반매도':
            num = json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] // 2
            if num == 0:
                logger.warning(f'매도하려는 {title}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
                return await ctx.reply(f'매도하려는 {title}의 주식이 1주밖에 없어 반매도 할 수 없습니다.')
            
        
        if num <= json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name]:
            json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] -= num
            json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] += (int(price) * num)
            
            if json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name] == 0:
                del(json_data[GetUserIDArrayNum(ctx=ctx)]['Stock'][stock_name])
            
            SetUserInformation(json_data)
            
            logger.info(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
            await ctx.reply(f'{title}의 주식이 {int(price):,}원에 {num:,}주가 매도되었습니다.')
        else:
            logger.warning(f'매도 하려는 주식개수가 현재 {title}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name]}주)')
            return await ctx.reply(f'매도 하려는 주식개수가 현재 {title}의 주식 보유수량보다 더 높습니다. (현재 보유수량: {json_data[GetUserIDArrayNum(ctx=ctx)]["Stock"][stock_name]}주)')
    else:
        logger.warning(f'{title}의 주식이 자산에 없습니다.')
        return await ctx.reply(f'{title}의 주식이 자산에 없습니다.')
  
@_StockSelling.error
async def _StockSelling_error(ctx, error):
    PrintLogger(error)
    
    if ErrorCheck(error, f"invalid literal for int() with base 10: '{ctx.args[1]}'"):
        logger.error('`매도 할 주식개수(숫자만)` 또는 `풀매도`, `반매도`만 입력해 주세요.')
        await ctx.reply('`매도 할 주식개수(숫자만)` 또는 `풀매도`, `반매도`만 입력해 주세요.')
        
    elif ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
        logger.error('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    elif ErrorCheck(error, "'NoneType' object has no attribute 'select_one'"):
        logger.error('매도하려는 주식을 찾지 못하였습니다.')
        await ctx.reply('매도하려는 주식을 찾지 못하였습니다.')
        
    else:
        logger.error(error)
        await ctx.send(f'{error}')

################################################################################ *지원금

@slash.slash(
    name='지원금',
    description='1만원 ~ 10만원 사이에서 랜덤으로 지원금을 지급합니다.',
    guild_ids=guilds_id,
    options=[]
)
@bot.command(name='지원금', aliases=['돈받기'])
async def _SupportFund(ctx):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    
    cool_down = 3600 * 4 #쿨타임
    
    if json_data[GetUserIDArrayNum(ctx=ctx)]['SupportFundTime'] == 0 or \
    int(time.time()) - json_data[GetUserIDArrayNum(ctx=ctx)]['SupportFundTime'] > cool_down: #만약 저장되있는 현재시간 - 저장된시간이 cool_down을 넘는다면
        
        random_added_deposit = randint(1, 10) * 10000

        json_data[GetUserIDArrayNum(ctx=ctx)]['Deposit'] += random_added_deposit
        json_data[GetUserIDArrayNum(ctx=ctx)]['SupportFund'] += random_added_deposit
        json_data[GetUserIDArrayNum(ctx=ctx)]['SupportFundTime'] = int(time.time())
        
        SetUserInformation(json_data)

        logger.info(f'{random_added_deposit:,}원이 지급되었습니다.')
        await ctx.reply(f'{random_added_deposit:,}원이 지급되었습니다.')
        
    else:
        now_timedelta = timedelta(seconds=json_data[GetUserIDArrayNum(ctx=ctx)]['SupportFundTime'] - int(time.time()) + cool_down)
        logger.warning(f'지원금을 받으려면 {str(now_timedelta)[-8:-6]}시간 {str(now_timedelta)[-5:-3]}분 {str(now_timedelta)[-2:]}초를 더 기다려야 합니다.')
        await ctx.reply(f'지원금을 받으려면 {str(now_timedelta)[-8:-6]}시간 {str(now_timedelta)[-5:-3]}분 {str(now_timedelta)[-2:]}초를 더 기다려야 합니다.')
    
################################################################################ .초기화

@bot.command(name='초기화', aliases=[])
async def _Initialization(ctx: commands.context.Context, *, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '내 자산 초기화':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx=ctx)])
        json_data.append(AddUser_Json(ctx.author.name, ctx.author.id)) #사용자 추가
        SetUserInformation(json_data)
        logger.info('초기화가 완료되었습니다.')
        await ctx.reply('초기화가 완료되었습니다.')
    
    else:
        logger.warning('.초기화 __[문구]__에 "내 자산 초기화"를 입력해야 초기화 할 수 있습니다.')
        await ctx.reply('.초기화 __[문구]__에 "내 자산 초기화"를 입력해야 초기화 할 수 있습니다.')
        
@_Initialization.error
async def _Initialization_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        logger.warning('.초기화 __[문구]__에 "내 자산 초기화"를 입력해야 초기화 할 수 있습니다.')
        await ctx.reply('.초기화 __[문구]__에 "내 자산 초기화"를 입력해야 초기화 할 수 있습니다.')
    
    else:
        logger.error(error)
        await ctx.reply(error)

################################################################################ /초기화

@slash.slash(
    name='초기화',
    description='자신의 자산을 초기화 합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='초기화확인',
            description='"내 자산 초기화" 를 입력해 주세요.',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'초기화문구': 'string'}
)
async def _Initialization(ctx: context.SlashContext, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '내 자산 초기화':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx=ctx)])
        json_data.append(AddUser_Json(ctx.author.name, ctx.author.id)) #사용자 추가
        SetUserInformation(json_data)
        logger.info('초기화가 완료되었습니다.')
        await ctx.reply('초기화가 완료되었습니다.')
    
    else:
        logger.warning('"내 자산 초기화"를 입력해야 초기화 할 수 있습니다.')
        await ctx.reply('"내 자산 초기화"를 입력해야 초기화 할 수 있습니다.')
        
################################################################################ .회원탈퇴

@bot.command(name='회원탈퇴', aliases=['탈퇴'])
async def _Withdrawal(ctx: commands.context.Context, *, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '탈퇴확인':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx=ctx)])
        SetUserInformation(json_data)
        logger.info('회원탈퇴가 완료되었습니다.')
        await ctx.reply('회원탈퇴가 완료되었습니다.')
    
    else:
        logger.warning(f'.{ctx.invoked_with} __[문구]__에 "탈퇴확인"를 입력해야 회원탈퇴 할 수 있습니다.')
        await ctx.reply(f'.{ctx.invoked_with} __[문구]__에 "탈퇴확인"를 입력해야 회원탈퇴 할 수 있습니다.')

@_Withdrawal.error
async def _Withdrawal_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        logger.warning(f'.{ctx.invoked_with} __[문구]__에 "탈퇴확인"를 입력해야 회원탈퇴 할 수 있습니다.')
        await ctx.reply(f'.{ctx.invoked_with} __[문구]__에 "탈퇴확인"를 입력해야 회원탈퇴 할 수 있습니다.')
    
    else:
        logger.error(error)
        await ctx.reply(error)

################################################################################ /회원탈퇴

@slash.slash(
    name='회원탈퇴',
    description='이 봇에 저장되있는 사용자의 정보를 삭제합니다.',
    guild_ids=guilds_id,
    options=[
        create_option(
            name='탈퇴확인',
            description='"탈퇴확인" 이라고 적어주세요.',
            option_type=OptionType.STRING,
            required=True
        )
    ],
    connector={'탈퇴확인': 'string'}
)
async def _Withdrawal(ctx: context.SlashContext, string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.warning('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '탈퇴확인':
        json_data = GetUserInformation()
        del(json_data[GetUserIDArrayNum(ctx=ctx)])
        SetUserInformation(json_data)
        logger.info('회원탈퇴가 완료되었습니다.')
        await ctx.reply('회원탈퇴가 완료되었습니다.')
    
    else:
        logger.warning('"탈퇴확인"를 입력해야 회원탈퇴 할 수 있습니다.')
        await ctx.reply('"탈퇴확인"를 입력해야 회원탈퇴 할 수 있습니다.')

################################################################################ .도움말

@bot.command(name='도움말', aliases=['명령어', '?'])
async def _HelpCommand(ctx: commands.context.Context, command: str=None):
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
        embed.set_footer(text='명령어를 자세히 보려면 \'.도움말 <명령어 이름>\' 을 써 주세요.')
        await ctx.reply(embed=embed)

    elif command == '도움말':
        embed = discord.Embed(title='도움말', description='등록되어있는 명령어들을 출력합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value='명령어, ?', inline=False)
        await ctx.reply(embed=embed)

    elif command == '사용자등록':
        embed = discord.Embed(title='사용자등록', description='데이터 베이스에 사용자를 등록합니다.', color=RandomEmbedColor())
        await ctx.reply(embed=embed)
    
    elif command == '자산정보':
        embed = discord.Embed(title='자산정보', description='자신의 자산정보를 확인합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value='자산조회', inline=False)
        embed.add_field(name='.자산정보 <@유저>', value='@유저의 자산정보를 확인합니다.', inline=False)
        embed.add_field(name='.자산정보 <공개여부>', value='자신의 자산공개여부를 확인합니다.', inline=False)
        embed.add_field(name='.자산정보 <공개>', value='자신의 자산공개여부를 공개로 설정합니다.', inline=False)
        embed.add_field(name='.자산정보 <비공개>', value='자신의 자산공개여부를 비공개로 설정합니다.', inline=False)
        await ctx.reply(embed=embed)
        
    elif command == '주가':
        embed = discord.Embed(title='주가', description='검색한 기업의 현재 주가를 확인합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value='시세', inline=False)
        embed.add_field(name='.주가 [기업이름 | 기업번호]', value='기업이름 또는 기업번호로 검색합니다.', inline=False)
        await ctx.reply(embed=embed)

    elif command == '매수':
        embed = discord.Embed(title='매수', description='입력한 기업의 주식을 매수합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value='구매, 주식구매, 주식매수', inline=False)
        embed.add_field(name='.매수 [기업이름 | 기업번호] [매수 할 주식 개수]', value='입력한 기업의 주식을, 주식 개수만큼 매수합니다.', inline=False)
        embed.add_field(name='.매수 [기업이름 | 기업번호] [풀매수]', value='입력한 기업의 주식을 최대까지 매수합니다.', inline=False)
        await ctx.reply(embed=embed)
        
    elif command == '매도':
        embed = discord.Embed(title='매도', description='입력한 기업의 주식을 매도합니다.', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value='판매, 주식판매, 주식매도', inline=False)
        embed.add_field(name='.매도 [기업이름 | 기업번호] [매도 할 주식 개수]', value='입력한 기업의 주식을, 주식 개수만큼 매도합니다.', inline=False)
        embed.add_field(name='.매도 [기업이름 | 기업번호] [반매도]', value='입력한 기업의 주식의 절반을 매도합니다.', inline=False)
        embed.add_field(name='.매도 [기업이름 | 기업번호] [풀매도]', value='입력한 기업의 주식을 모두 매도합니다.', inline=False)
        await ctx.reply(embed=embed)
    
    elif command == '지원금':
        embed = discord.Embed(title='지원금', description='1만원 ~ 10만원 사이에서 랜덤으로 지급합니다. (쿨타임: 4시간)', color=RandomEmbedColor())
        embed.add_field(name='다른이름', value='돈받기', inline=False)
        await ctx.reply(embed=embed)
        
    elif command == '초기화':
        embed = discord.Embed(title='초기화', description='"내 자산 초기화"를 입력해 자신의 자산정보를 초기화 합니다.', color=RandomEmbedColor())
        embed.add_field(name='.초기화 [초기화 문구]', value='초기화 문구에는 "내 자산 초기화"를 입력해 주세요.')
        await ctx.reply(embed=embed)
        
    else:
        await ctx.reply('알 수 없는 명령어 입니다.')
        
################################################################################

bot.run(Token)