#자산정보

import discord
from discord.ext import commands
from discord.ext.commands import Context

from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option, create_choice

import asyncio
import nest_asyncio; nest_asyncio.apply()
from functools import partial

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from time import time

from typing import Union

from module._define_ import *

################################################################################ 자산정보 코루틴 선언 ################################################################################

async def get_text_from_url(author_id, num, stock_num):  # 코루틴 정의
    global stock_num_array
    global TotalAssets
    
    json_data = GetUserInformation()
    
    loop = asyncio.get_event_loop()
    ua = UserAgent().random

    url = f'https://finance.naver.com/item/main.naver?code={stock_num}' #네이버 금융에 검색
    request = partial(requests.get, url, headers={'user-agent': ua})
    timer = time()
    res = await loop.run_in_executor(None, request)
    
    soup = bs(res.text, 'lxml')
    stock_name = soup.select_one('#middle > div.h_company > div.wrap_company > h2 > a').text
    price = soup.select_one('#chart_area > div.rate_info > div > p.no_today').select_one('span.blind').text.replace('\n', '').replace(',', '') #현재 시세
    lastday_per = soup.select_one('#chart_area > div.rate_info > div > p.no_exday > em:nth-child(4)').select_one('span.blind').text.replace('\n', '') #어제 대비 시세%
    balance = json_data[GetArrayNum(author_id)]['Stock'][stock_num] #현재 주식 수량
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
    
    logger.info(f'{num} Done. {time() - timer}seconds')
    
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

######################################################################################################################################################

async def _AssetInformation_code(ctx: Union[Context, SlashContext], option: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {option}')
        
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    json_data = GetUserInformation()
    author_id = ctx.author.id
    
    if option is not None: #부가 옵션이 전달되어 있을 때
        if option in ('랭킹', '순위'):
            members: list[discord.Member] = ctx.guild.members
            member_assets = []
            
            for member in members:
                if IsVaildUser(member.id):
                    if json_data[GetArrayNum(member.id)]['Settings']['InformationDisclosure']:
                        member_assets.append((member.name, json_data[GetArrayNum(member.id)]['TotalAssets']))
                    
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
            
            elif not json_data[GetArrayNum(author_id)]['Settings']['InformationDisclosure']:
                logger.info(f'{user_name}님의 정보가 비공개되어 있습니다.')
                await ctx.reply(f'{user_name}님의 정보가 비공개되어 있습니다.')
                return
    
    async def _crawling():
        global stock_num_array
        global TotalAssets
        
        stock_num_array = [[] for i in range(len(json_data[GetArrayNum(author_id)]['Stock']))] #현재 주식 종류의 개수만큼 배열을 만듦
        TotalAssets = 0 #총 자산
        
        start_time = time() #크롤링 시간
        
        asyncio.get_event_loop().run_until_complete(
            get_text_(author_id, json_data[GetArrayNum(author_id)]['Stock'])
        )
        
        TotalAssets += json_data[GetArrayNum(author_id)]['Deposit'] #예수금
        
        json_data[GetArrayNum(author_id)]['TotalAssets'] = TotalAssets #다 합친걸 총 자산에 저장
        
        SetUserInformation(json_data)
        
        embed = discord.Embed(title=f'{ctx.author.name if option is None else user_name}님의 자산정보', color=RandomEmbedColor())
        embed.add_field(name='예수금', value=f'{json_data[GetArrayNum(author_id)]["Deposit"]:,}원')
        embed.add_field(name='총 자산', value=f'{json_data[GetArrayNum(author_id)]["TotalAssets"]:,}원')
        if json_data[GetArrayNum(author_id)]['Settings']['ShowSupportFund']:
            embed.add_field(name='지원금으로 얻은 돈', value=f'{json_data[GetArrayNum(author_id)]["SupportFund"]:,}원', inline=False)
        if len(json_data[GetArrayNum(author_id)]['Stock']) != 0:
            embed.add_field(name='='*25, value='_ _', inline=False)
        
        for add_embed in stock_num_array:
            embed.add_field(name=add_embed[0], value=f'잔고수량: {add_embed[1]:,} | {add_embed[2]:,}원', inline=False)
        
        logger.info(f'All Done. {time() - start_time} seconds')
        await ctx.reply(embed=embed)
    
    if isinstance(ctx, Context):
        async with ctx.typing():
            await _crawling()
    else:
        hidden = not json_data[GetArrayNum(author_id)]['Settings']['InformationDisclosure']
        await ctx.defer(hidden=hidden)
        await _crawling()

######################################################################################################################################################

class AssetInformation_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @cog_ext.cog_slash(
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
    async def _AssetInformation(self, ctx: SlashContext, option: Union[discord.User, str]=None):
        await _AssetInformation_code(ctx, option)
        
    @_AssetInformation.error
    async def _AssetInformation_error(self, ctx, error):
        if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
            logger.warning('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
            await ctx.reply('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
            
        elif ErrorCheck(error, "list indices must be integers or slices, not NoneType"):
            logger.warning('등록되어 있지 않은 유저입니다.')
            await ctx.reply('등록되어 있지 않은 유저입니다.')
            
        else:
            logger.warning(error)
            await ctx.send(f'{error}')
        
class AssetInformation_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name='자산정보', aliases=['자산조회'])
    async def _AssetInformation(self, ctx: Context, option: Union[discord.Member, str]=None):
        await _AssetInformation_code(ctx, option)
    
    @_AssetInformation.error
    async def _AssetInformation_error(self, ctx, error):
        if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
            logger.warning('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
            await ctx.reply('검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.')
            
        elif ErrorCheck(error, "Command raised an exception: TypeError: list indices must be integers or slices, not NoneType"):
            logger.warning('등록되어 있지 않은 유저입니다.')
            await ctx.reply('등록되어 있지 않은 유저입니다.')
            
        elif ErrorCheck(error, f"Command raised an exception: ValueError: invalid literal for int() with base 10: '{ctx.args[2].replace('<@', '').replace('>', '')}'")or \
            ErrorCheck(error, "Command raised an exception: ValueError: invalid literal for int() with base 10: '{0}'".format(ctx.args[2].replace('@', '@\u200b'))):
            logger.warning('다시 입력해 주세요.')
            await ctx.reply('다시 입력해 주세요.')
            
        elif ErrorCheck(error, "Command raised an exception: AttributeError: 'str' object has no attribute 'id'"):
            logger.warning('다시 입력해 주세요.')
            await ctx.reply('다시 입력해 주세요.')
            
        else:
            logger.warning(error)
            await ctx.send(f'{error}')
            
def setup(bot: commands.Bot):
    bot.add_cog(AssetInformation_Context(bot))
    bot.add_cog(AssetInformation_SlashContext(bot))