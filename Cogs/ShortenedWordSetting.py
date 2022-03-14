#단축어설정

from discord.ext import commands

from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option, create_choice

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from re import match

from typing import Union

from module.__define__ import *

######################################################################################################################################################

@CommandExecutionTime
async def _ShortenedWordSetting_code(ctx: Union[Context, SlashContext], setting_name: str, add_stock_name: str = None, add_stock_num: str = None):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {setting_name} {add_stock_name} {add_stock_num}")
    
    if not IsVaildUser(ctx):
        logger.info("먼저 `.사용자등록` 부터 해 주세요.")
        await ctx.reply("먼저 `.사용자등록` 부터 해 주세요.")
        return
    
    async def reply(msg: str):
        if isinstance(ctx, Context):
            await ctx.reply(msg)
        else:
            await ctx.reply(msg, hidden=True)
        
    if setting_name == "목록":
        value: str = "단축어 목록\n"
        
        with getUserInformation() as data:
            for stock_name in data.json_data[GetArrayNum(ctx)]['StockDict']:
                value += f"> {stock_name}: {data.json_data[GetArrayNum(ctx)]['StockDict'][stock_name]}\n"
        
        await reply(value)
        
    elif setting_name == "추가":
        if add_stock_num is None:
            if isinstance(ctx, SlashContext):
                logger.info("**기업번호**는 필수 입력 항목 입니다.")
                await reply("**기업번호**는 필수 입력 항목 입니다.")
                return
            else:
                logger.info("**-기업번호**는 필수 입력 항목 입니다.")
                await reply("**-기업번호**는 필수 입력 항목 입니다.")
                return
            
        elif not match("[0-9]+", add_stock_num): #기업번호에 숫자만 있는지 확인
            logger.info("숫자만 입력해 주세요.")
            await reply("숫자만 입력해 주세요.")
            return
        
        if not add_stock_name: #add_stock_name이 None일 경우 인터넷에서 검색
            url = f"https://finance.naver.com/item/main.naver?code={add_stock_num}"
            soup = bs(requests.get(url, headers={"User-agent" : UserAgent().random}).text, "lxml")
            
            add_stock_name = soup.select_one("#middle > div.h_company > div.wrap_company > h2 > a").text.lower() #주식회사 이름
            add_stock_num = soup.select_one("#middle > div.h_company > div.wrap_company > div > span.code").text #기업코드
            
        if add_stock_name in GetUserInformation()[GetArrayNum(ctx)]['StockDict'].keys():
            logger.info("이미 추가되있는 기업이름입니다.")
            await reply("이미 추가되있는 기업이름입니다.")
            return
        
        with setUserInformation() as data:
            data.json_data[GetArrayNum(ctx)]['StockDict'][add_stock_name] = add_stock_num
        
        logger.info(f"`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.")
        await reply(f"`{add_stock_name}: {add_stock_num}`이/가 추가되었습니다.")
        
    elif setting_name == "제거":
        if not add_stock_name:
            if isinstance(ctx, SlashContext):
                logger.info("**기업이름**는 필수 입력 항목 입니다.")
                await reply("**기업이름**는 필수 입력 항목 입니다.")
                return
            else:
                logger.info("**-기업이름**는 필수 입력 항목 입니다.")
                await reply("**-기업이름**는 필수 입력 항목 입니다.")
                return
        
        for k in GetUserInformation()[GetArrayNum(ctx)]['StockDict']:
            if k == add_stock_name:
                with setUserInformation() as data:
                    del(data.json_data[GetArrayNum(ctx)]['StockDict'][k])
                
                with getUserInformation() as data:
                    logger.info(f"`{k}: {data.json_data[GetArrayNum(ctx)]['StockDict'][k]}`이/가 제거되었습니다.")
                    await reply(f"`{k}: {data.json_data[GetArrayNum(ctx)]['StockDict'][k]}`이/가 제거되었습니다.")
                return
            
        logger.info(f"{add_stock_name}이/가 목록에 존재하지 않습니다.")
        await reply(f"{add_stock_name}이/가 목록에 존재하지 않습니다.")
        return

######################################################################################################################################################

class ShortenedWordSetting_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @cog_ext.cog_slash(
        name="단축어설정",
        description="단축어목록을 확인하거나, 추가 또는 제거합니다.",
        guild_ids=guilds_id,
        options=[
            create_option(
                name="옵션",
                description="설정할 옵션을 선택하세요.",
                option_type=OptionType.STRING,
                required=True,
                choices=[
                    create_choice(
                        name="목록",
                        value="목록"
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
                name="기업이름",
                description="옵션이 추가 또는 제거일 때 사용할 기업이름을 입력 해 주세요.",
                option_type=OptionType.STRING,
                required=False
            ),
            create_option(
                name="기업번호",
                description="옵션이 추가 또는 제거일 때 사용할 기업번호를 입력 해 주세요.",
                option_type=OptionType.STRING,
                required=False
            )
        ],
        connector={
            "옵션": "setting_name",
            "기업이름": "add_stock_name",
            "기업번호": "add_stock_num"
        }
    )
    async def _ShortenedWordSetting(self, ctx: SlashContext, setting_name: str, add_stock_name: str = None, add_stock_num: str = None):
        await _ShortenedWordSetting_code(ctx, setting_name, add_stock_name, add_stock_num)

    @_ShortenedWordSetting.error
    async def _ShortenedWordSetting_error(self, ctx: SlashContext, error):
        if isinstance(error, AttributeError):
            logger.warning("존재하지 않는 기업번호입니다.")
            await ctx.reply("존재하지 않는 기업번호입니다.", hidden=True)
            
        else:
            logger.warning(f"{error}")
            await ctx.send(f"{error}", hidden=True)

######################################################################################################################################################

class ShortenedWordSetting_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="단축어설정", aliases=["단축어"])
    async def _ShortenedWordSetting(self, ctx: Context, setting_name: str, *, add_stock: str=None):
        logger.info(f"{ctx.author.name} {add_stock}")
        
        if setting_name not in ("목록", "추가", "제거"):
            logger.warning("목록, 추가, 제거 중 하나를 선택해 주세요.")
            await ctx.reply("목록, 추가, 제거 중 하나를 선택해 주세요.")
            return
        
        if setting_name != "목록":
            if match("(-(기업)?(이름|번호)\s[\w|ㄱ-ㅎ|ㅏ-ㅣ|가-힣]+\s?)+$", add_stock):
                add_stock: dict = dict([split.strip().replace("기업", "").split()
                                for split in add_stock.split("-") if split != ""])
                await _ShortenedWordSetting_code(ctx, setting_name, add_stock.get("이름"), add_stock.get("번호"))
            else:
                await ctx.reply("다시 입력해 주세요.")
                return
        else:
            await _ShortenedWordSetting_code(ctx, setting_name)
            
    @_ShortenedWordSetting.error
    async def _ShortenedWordSetting_error(self, ctx: Context, error):
        if isinstance(error, AttributeError):
            logger.warning("존재하지 않는 기업번호입니다.")
            await ctx.reply("존재하지 않는 기업번호입니다.")
            
        elif ErrorCheck(error, "setting_name is a required argument that is missing."):
            logger.warning("목록, 추가, 제거 중 하나를 선택해 주세요.")
            await ctx.reply("목록, 추가, 제거 중 하나를 선택해 주세요.")
            
        elif isinstance(error.original, TypeError):
            logger.warning("설정할 기업이름과 기업번호를 입력해 주세요.")
            await ctx.reply("설정할 기업이름과 기업번호를 입력해 주세요.")
            
        else:
            logger.warning(f"{error}")
            await ctx.send(f"{error}")
            
######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(ShortenedWordSetting_SlashContext(bot))
    bot.add_cog(ShortenedWordSetting_Context(bot))