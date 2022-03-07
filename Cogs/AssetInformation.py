#자산정보

import discord
from discord.ext import commands
from discord.ext.commands import Context

from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option, create_choice

import asyncio
from functools import partial

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from time import time

from typing import Union

from module.__define__ import *

################################################################################ 자산정보 코루틴 선언 ################################################################################

async def get_text_from_url(author_id, stock_num):  # 코루틴 정의
    loop = asyncio.get_event_loop()
    ua = UserAgent().random

    url = f"https://finance.naver.com/item/sise.naver?code={stock_num}" #네이버 금융에 검색
    request = partial(requests.get, url, headers={"user-agent": ua})
    timer = time()
    res = await loop.run_in_executor(None, request)
    
    soup = bs(res.text, "lxml")
    stock_name: str = soup.select_one("#middle > div.h_company > div.wrap_company > h2 > a").text #주식명
    price: int = int(soup.select_one("#_nowVal").text.replace(",", "")) #현재 시세
    yesterday_price: int = int(
        soup.select_one("#content > div.section.inner_sub > div:nth-child(1) > table > tbody > tr:nth-child(3) > td:nth-child(4) > span").text.replace(",", "")) #어제 시세
    compared_price: int = price - yesterday_price #어제대비 가격
    compared_per: int = round((price - yesterday_price) / yesterday_price * 100, 2) #어제대비 가격%
    balance: int = GetUserInformation()[GetArrayNum(author_id)]['Stock'][stock_num] #가지고 있는 주식 수량
    price_sign = "" if compared_price <= 0 else "+" #부호설정
    
    logger.info(f"Done. {time() - timer}seconds")

    return [f"{stock_name} | {int(price):,}원 | {price_sign}{compared_per}%", balance, int(price) * balance]

################################################################################

async def get_text_(author_id):
    # 아직 실행된 것이 아니라, 실행할 것을 계획하는 단계
    futures: list[asyncio.Task] = [
        asyncio.ensure_future(get_text_from_url(author_id, keyword))
            for keyword in GetUserInformation()[GetArrayNum(author_id)]['Stock']
    ]

    await asyncio.gather(*futures)
    
    stock_list = [task.result() for task in futures]
    TotalAssets = 0
    for i in stock_list:
        TotalAssets += i[2]
        
    return {"stock_list": stock_list, "TotalAssets": TotalAssets}

######################################################################################################################################################

async def _AssetInformation_code(ctx: Union[Context, SlashContext], option: Union[discord.User, str]):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {option}")
    
    if not IsVaildUser(ctx):
        logger.info("먼저 `.사용자등록` 부터 해 주세요.")
        await ctx.reply("먼저 `.사용자등록` 부터 해 주세요.")
        return
    
    author_id = ctx.author.id
    
    if option is not None: #부가 옵션이 전달되어 있을 때
        if option in ("랭킹", "순위"):
            members: list[discord.Member] = ctx.guild.members
            member_assets = []
            
            for member in members:
                if IsVaildUser(member.id):
                    if GetUserInformation()[GetArrayNum(member.id)]['Settings']['InformationDisclosure']:
                        member_assets.append((member.name, GetUserInformation()[GetArrayNum(member.id)]['TotalAssets']))
                    
            member_assets.sort(key=lambda total: total[1], reverse=True) #총 자산을 기준으로 리스트 정렬
            
            embed = discord.Embed(title="자산랭킹", color=RandomEmbedColor())
            embed.set_footer(text="등록되어 있지 않은 유저, 자산정보가 비공개인 유저는 자산랭킹에 보이지 않습니다.")
            for num, asset in enumerate(member_assets):
                if num <= 10:
                    embed.add_field(name=f"{num+1}위 {asset[0]}", value=f"{asset[1]:,}원", inline=False)
                else: break
            
            await ctx.reply(embed=embed)
            return
        
        else:
            author_id: int = option.id
            user_name: str = option.name
            
            if not GetUserInformation()[GetArrayNum(author_id)]['Settings']['InformationDisclosure']:
                logger.info(f"{user_name}님의 정보가 비공개되어 있습니다.")
                await ctx.reply(f"{user_name}님의 정보가 비공개되어 있습니다.")
                return
    
    async def _crawling():
        start_time = time() #크롤링 시간
        
        crawling_data = await get_text_(author_id)
        
        with setUserInformation() as data:
            data.json_data[GetArrayNum(author_id)]['TotalAssets'] = \
                crawling_data['TotalAssets'] + data.json_data[GetArrayNum(author_id)]['Deposit'] #다 합친걸 총 자산에 저장
        
        with getUserInformation() as data:
            embed = discord.Embed(title=f"{ctx.author.name if option is None else user_name}님의 자산정보", color=RandomEmbedColor())
            embed.add_field(name="예수금", value=f"{data.json_data[GetArrayNum(author_id)]['Deposit']:,}원")
            embed.add_field(name="총 자산", value=f"{data.json_data[GetArrayNum(author_id)]['TotalAssets']:,}원")
            if data.json_data[GetArrayNum(author_id)]['Settings']['ShowSupportFund']:
                embed.add_field(name="지원금으로 얻은 돈", value=f"{data.json_data[GetArrayNum(author_id)]['SupportFund']:,}원", inline=False)
            if len(data.json_data[GetArrayNum(author_id)]['Stock']) != 0:
                embed.add_field(name="="*25, value="_ _", inline=False)
        
        for add_embed in crawling_data['stock_list']:
            embed.add_field(name=add_embed[0], value=f"잔고수량: {add_embed[1]:,} | {add_embed[2]:,}원", inline=False)
        
        logger.info(f"All Done. {time() - start_time} seconds")
        return embed
    
    if isinstance(ctx, Context):
        async with ctx.typing():
            await ctx.reply(embed=await _crawling())
    else:
        hidden = not GetUserInformation()[GetArrayNum(author_id)]['Settings']['InformationDisclosure']
        await ctx.defer(hidden=hidden)
        await ctx.reply(embed=await _crawling())

######################################################################################################################################################

class AssetInformation_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @cog_ext.cog_slash(
        name="자산정보",
        description="현재 자신의 자산정보를 확인합니다.",
        guild_ids=guilds_id,
        options=[
            create_option(
                name="유저",
                description="다른유저의 자산정보를 확인합니다.",
                option_type=OptionType.USER,
                required=False
            ),
            create_option(
                name="추가옵션",
                description="추가옵션을 선택해 주세요.",
                option_type=OptionType.STRING,
                required=False,
                choices=[
                    create_choice(
                        name="랭킹",
                        value="랭킹"
                    )
                ]
            )
        ],
        connector={"유저": "option", "추가옵션": "option"}
    )
    async def _AssetInformation(self, ctx: SlashContext, option: Union[discord.User, str]=None):
        await _AssetInformation_code(ctx, option)
        
    @_AssetInformation.error
    async def _AssetInformation_error(self, ctx, error):
        if ErrorCheck(error, "'NoneType' object has no attribute 'text'"):
            logger.warning("검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.")
            await ctx.reply("검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.")
            
        elif isinstance(error, TypeError):
            logger.warning("등록되어 있지 않은 유저입니다.")
            await ctx.reply("등록되어 있지 않은 유저입니다.")
            
        else:
            logger.warning(error)
            await ctx.send(f"{error}")
        
class AssetInformation_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name="자산정보", aliases=["자산조회"])
    async def _AssetInformation(self, ctx: Context, option: Union[discord.Member, str]=None):
        await _AssetInformation_code(ctx, option)
    
    @_AssetInformation.error
    async def _AssetInformation_error(self, ctx, error):
        if ErrorCheck(error, "Command raised an exception: AttributeError: 'NoneType' object has no attribute 'text'"):
            logger.warning("검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.")
            await ctx.reply("검색하던중 알 수 없는 에러가 발생하였습니다. 다시 입력해 주세요.")
            
        elif ErrorCheck(error, "Command raised an exception: AttributeError: 'str' object has no attribute 'id'"):
            logger.warning("다시 입력해 주세요.")
            await ctx.reply("다시 입력해 주세요.")
            
        elif isinstance(error.original, TypeError):
            logger.warning("등록되어 있지 않은 유저입니다.")
            await ctx.reply("등록되어 있지 않은 유저입니다.")
            
        else:
            logger.warning(error)
            await ctx.send(f"{error}")
            
def setup(bot: commands.Bot):
    bot.add_cog(AssetInformation_Context(bot))
    bot.add_cog(AssetInformation_SlashContext(bot))
