from email.message import Message
import nest_asyncio; nest_asyncio.apply()

import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandNotFound
from discord.utils import get

from discord_slash import SlashCommand, SlashContext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.model import SlashCommandPermissionType as PermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission

import os

from time import time

from platform import platform

from module.__define__ import *

test_guilds_id = (714012054721396786,)
permission_setting = {
    id: [
        create_permission(
            id=642288666156466176,
            id_type=PermissionType.USER,
            permission=True
        )
    ] for id in test_guilds_id
}

################################################################################ 기본값 설정 ################################################################################

def _InitialVarSetting():
    global operation_time, bot, slash, Token

    operation_time = time() #가동된 현재 시간

    intents = discord.Intents.all()

    if DEBUGGING:
        game = discord.Game('봇 테스트') # ~하는 중
        bot = commands.Bot(command_prefix=';', status=discord.Status.do_not_disturb, activity=game, intents=intents)
    else:
        game = discord.Game('주식투자') # ~하는 중
        bot = commands.Bot(command_prefix='.', help_command=None, status=discord.Status.online, activity=game, intents=intents)

    slash = SlashCommand(bot, sync_commands=True)

    with open('./etc/Token.txt', 'r', encoding='utf-8') as Token_txt:
        Token = Token_txt.read()
        
    for cog_file in os.listdir('./Cogs'): #코그 설정
        if cog_file.endswith('.py'):
            bot.load_extension(f'Cogs.{cog_file[:-3]}')
            
_InitialVarSetting()
        
################################################################################ 봇 이벤트 ################################################################################

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name + " 디버깅으" if DEBUGGING else bot.user.name}로 로그인')
    print(f'{bot.user.name + " 디버깅으" if DEBUGGING else bot.user.name}로 로그인')
    
################################################################################

@bot.event
async def on_message(msg: discord.Message):
    await bot.process_commands(msg)

################################################################################

@bot.event
async def on_command_error(ctx: Context, error):
    if isinstance(error, CommandNotFound):
        logger.warning(f'{ctx.author.name}: {error}')

################################################################################ 관리자 전용 명령어 ################################################################################

################################################################################ /정보

@slash.slash(
    name='정보',
    description='현재 봇의 정보를 확인합니다.',
    guild_ids=test_guilds_id,
    options=[],
    default_permission=False,
    permissions=permission_setting
)
async def _BotInformation(ctx: SlashContext):
    logger.info('봇 정보')

    now_time = ConvertSecToTimeStruct(int(time() - operation_time))
    async def reply(msg):
        logger.info(f'{msg}')
        await ctx.reply(f'{msg}', hidden=True)
        
    await reply(f"현재 플렛폼: {platform()}\n\
가동시간: {now_time}\n\
지연시간: {bot.latency}ms\n\
불러온 명령어들: {list(bot.cogs.keys())}")

################################################################################ /업로드

@slash.slash(
    name='업로드',
    description='파일을 업로드합니다.',
    guild_ids=test_guilds_id,
    options=[
        create_option(
            name='파일타입',
            description='업로드할 파일 타입을 선택해주세요.',
            option_type=OptionType.STRING,
            required=True,
            choices=[
                create_choice(
                    name='logs',
                    value='logs'
                ),
                create_choice(
                    name='UserInformation.json',
                    value='userinfo'
                ),
                create_choice(
                    name='StockDictionary.json',
                    value='stockdict'
                ),
                create_choice(
                    name='그 외',
                    value='other'
                )
            ]
        ),
        create_option(
            name='경로',
            description='업로드할 경로를 입력해 주세요.',
            option_type=OptionType.STRING,
            required=False
        )
    ],
    default_permission=False,
    permissions=permission_setting,
    connector={'파일타입': 'file_type', '경로': 'path'}
)
async def _UploadFile(ctx: SlashContext, file_type: str, path: str = None):    
    logger.info(f'업로드: {file_type}')
    
    await ctx.defer()
    
    if file_type == 'logs':
        from os import chdir, listdir, remove
        from zipfile import ZipFile
        
        chdir('./logs') #실행폴더 변경
        zipfile = ZipFile(f'logs.zip', 'w')

        logs_dir = [i for i in listdir('./') if i.endswith('.log')]
        for n, file in enumerate(logs_dir):
            zipfile.write(file)
            if len(logs_dir)-1 != n:
                remove(file)

        zipfile.close()
        chdir('../')
        
        await ctx.send(f'{len(logs_dir)}개의 파일이 압축되어 업로드되었습니다.', file=discord.File('./logs/logs.zip'))
        
    elif file_type == 'userinfo':
        await ctx.send('성공적으로 업로드되었습니다.', file=discord.File('./json/UserInformation.json'))

    elif file_type == 'stockinfo':
        await ctx.send('성공적으로 업로드되었습니다.', file=discord.File('./json/StockDictionary.json'))
        
    elif file_type == 'other':
        if path is None:
            await ctx.send('경로를 입력해 주세요.')
            return
        
        await ctx.send('성공적으로 업로드되었습니다.', file=discord.File(path))
        
@_UploadFile.error
async def _UploadFile_error(ctx: SlashContext, error):
    await ctx.send(error)

################################################################################ /다운로드

@slash.slash(
    name='다운로드',
    description='파일을 다운로드 합니다.',
    guild_ids=test_guilds_id,
    options=[
        create_option(
            name='파일타입',
            description='다운로드할 파일 타입을 선택해주세요.',
            option_type=OptionType.STRING,
            required=True,
            choices=[
                create_choice(
                    name='Cogs',
                    value='cogs'
                ),
                create_choice(
                    name='UserInformation.json',
                    value='userinfo'
                ),
                create_choice(
                    name='StockDictionary.json',
                    value='stockdict'
                ),
                create_choice(
                    name='그 외',
                    value='other'
                )
            ]
        ),
        create_option(
            name='링크',
            description='다운로드 할 링크를 입력해 주세요.',
            option_type=OptionType.STRING,
            required=True
        ),
        create_option(
            name='경로',
            description='다운로드 할 경로를 입력해 주세요.',
            option_type=OptionType.STRING,
            required=False
        )
    ],
    default_permission=False,
    permissions=permission_setting,
    connector={'파일타입': 'file_type', '링크': 'link', '경로': 'path'}
)
async def _DownloadFile(ctx: SlashContext, file_type: str, link: str, path: str=None):
    logger.info(f'다운로드: {file_type}')
    
    await ctx.defer()
    
    import requests as r
    
    if file_type == 'cogs':
        if link.find('.py') == -1:
            await ctx.send('올바르지 않은 링크입니다. 다시 확인해 주세요.')
            return
        
        file_name = link.split("/")[-1]
        
        with open(f'./Cogs/{file_name}', 'wb') as f:
            f.write(r.get(link, allow_redirects=True).content)
        
        await ctx.send(f'{file_name}가 성공적으로 다운로드가 완료되었습니다.')
    
    elif file_type == 'userinfo':
        if link.find('UserInformation.json') == -1:
            await ctx.send('올바르지 않은 링크입니다. 다시 확인해 주세요.')
            return
        
        await ctx.send('백업파일이 업로드 되었습니다.', file=discord.File('./json/UserInformation.json'))
        
        with open('./json/UserInformation.json', 'wb') as f:
            f.write(r.get(link, allow_redirects=True).content)
        
        await ctx.send('성공적으로 다운로드가 완료되었습니다.')

    elif file_type == 'stockdict':
        if link.find('StockDictionary.json') == -1:
            await ctx.send('올바르지 않은 링크입니다. 다시 확인해 주세요.')
            return
        
        await ctx.send('백업파일이 업로드 되었습니다.', file=discord.File('./json/StockDictionary.json'))
        
        with open('./json/StockDictionary.json', 'wb') as f:
            f.write(r.get(link, allow_redirects=True).content)
        
        await ctx.send('성공적으로 다운로드가 완료되었습니다.')
    
    elif file_type == 'other':
        if path is None:
            await ctx.send('경로를 입력해 주세요.')
            return
        
        with open(path, 'wb') as f:
            f.write(r.get(link, allow_redirects=True).content)
        
        await ctx.send(f'{link.split("/")[-1]}가 {path}에 성공적으로 다운로드가 완료되었습니다.')

@_DownloadFile.error
async def _DownloadFile_error(ctx: SlashContext, error):
    await ctx.send(error)

################################################################################ /리로드

@slash.slash(
    name='리로드',
    description='명령어를 다시 불러옵니다.',
    guild_ids=test_guilds_id,
    options=[],
    default_permission=False,
    permissions=permission_setting
)
async def reload_commands(ctx: SlashContext):
    logger.info('명령어 다시불러오는 중...')
    
    await ctx.defer()
    
    for cog_file in os.listdir('Cogs'):
        if cog_file.endswith('.py'):
            # bot.unload_extension(f'Cogs.{cog_file[:-3]}')
            # bot.load_extension(f'Cogs.{cog_file[:-3]}')
            bot.reload_extension(f'Cogs.{cog_file[:-3]}')
            logger.info(f'리로드 완료: Cogs.{cog_file[:-3]}')
    
    logger.info('모든 명령어를 다시 불러왔습니다.')
    await ctx.send('모든 명령어를 다시 불러왔습니다.')

################################################################################ /역할

@slash.slash(
    name='역할',
    description='봇 테스트 중 역할을 추가하거나 제거합니다.',
    guild_ids=test_guilds_id,
    options=[
        create_option(
            name='역할설정',
            description='역할을 추가하거나 제거합니다.',
            option_type=OptionType.STRING,
            required=True,
            choices=[
                create_choice(
                    name='추가',
                    value='add'
                ),
                create_choice(
                    name='제거',
                    value='delete'
                )
            ]
        )
    ],
    default_permission=False,
    permissions=permission_setting,
    connector={'역할설정': 'rule_setting'}
)
async def _RuleSetting(ctx: SlashContext, rule_setting: str):
    logger.info(f'역할: {rule_setting}')
    
    await ctx.defer()
    
    if rule_setting == 'add':
        for guild in guilds_id:
            guild: discord.Guild = bot.get_guild(guild)
            role: discord.Role = get(guild.roles, name='봇 테스트 중')
            member: discord.Member
            
            for member in guild.members:
                if not member.bot:
                    await member.add_roles(role)
            logger.info(f'{guild}: added')
        
        await ctx.send('추가완료.')
            
    elif rule_setting == 'delete':
        for guild in guilds_id:
            guild: discord.Guild = bot.get_guild(guild)
            role: discord.Role = get(guild.roles, name='봇 테스트 중')
            member: discord.Member
            
            for member in guild.members:
                if not member.bot:
                    await member.remove_roles(role)
            logger.info(f'{guild}: removed')
            
        await ctx.send('제거완료.')

################################################################################

bot.run(Token)