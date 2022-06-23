#개인설정

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.errors import MissingRequiredArgument

from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option, create_choice

from typing import Union

from define import *

######################################################################################################################################################

@CommandExecutionTime
async def _PersonalSettings_code(ctx: Union[Context, SlashContext], setting: str, boolean: Union[bool, str]=None):
    logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {setting} {boolean}")
    
    if await CheckUser(ctx): return
    
    async def reply(msg: str):
        if isinstance(ctx, Context):
            await ctx.reply(msg)
        else:
            await ctx.reply(msg, hidden=True)
            
    if isinstance(boolean, str):
        d = {
            "참": True, "공개": True, "true": True, "표시": True,
            "거짓": False, "비공개": False, "false": False, "미표시": False
        }
        boolean = d[boolean.lower()]
        
    if setting == "설정정보":
        string = ""
        d = {
            "InformationDisclosure": "자산정보 공개 여부",
            "ShowSupportFund": "지원금으로 얻은 돈 표시 여부",
            "ShowStockChartImage": "주식차트 표시 여부",
            "ShowSupportFundCooldown": "지원금 쿨타임 바로 표시 여부",
            "ShowComparedPrice": "자산정보에 어제 대비 가격 표시 여부",
            "ShowInterestStockList": "관심주가 공개표시 여부"
        }

        for _key, _value in GetUserInformation()[str(ctx.author.id)]['Settings'].items():
            string += f"{d[_key]} = {_value}\n"

        await reply(string)
        return
    
    else:
        if boolean is None:
            logger.warning("설정할 값(「true」또는「false」)를 입력해 주세요.")
            await ctx.reply("설정할 값(「true」또는「false」)를 입력해 주세요.")
            return
        
    if setting in ("InformationDisclosure", "자산정보"):
        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Settings']['InformationDisclosure'] = boolean
        
        await reply(f"자산정보 공개여부가 {boolean}로 설정되었습니다.")
        return
        
    elif setting in ("ShowSupportFund", "지원금표시"):
        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Settings']['ShowSupportFund'] = boolean
        
        await reply(f"지원금으로 얻은 돈 표시여부가 {boolean}로 설정되었습니다.")
        return
        
    elif setting in ("ShowStockChartImage", "차트표시"):
        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Settings']['ShowStockChartImage'] = boolean
        
        await reply(f"주식차트 표시여부가 {boolean}로 설정되었습니다.")
        return

    elif setting in ("ShowSupportFundCooldown", "쿨타임표시"):
        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Settings']['ShowSupportFundCooldown'] = boolean
        
        await reply(f"지원금 쿨타임 바로표시여부가 {boolean}로 설정되었습니다.")
        return

    elif setting in ("ShowComparedPrice", "어제대비가격"):
        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Settings']['ShowComparedPrice'] = boolean
        
        await reply(f"자산정보에 어제 대비 가격 표시 여부가 {boolean}로 설정되었습니다.")
        return

    elif setting in ("ShowInterestStockList", "관심주가"):
        with setUserInformation() as data:
            data.json_data[str(ctx.author.id)]['Settings']['ShowInterestStockList'] = boolean
        
        await reply(f"관심주가 공개표시 여부가 {boolean}로 설정되었습니다.")
        return
        
    else:
        await reply("다시 입력해 주세요.")
        return
        
######################################################################################################################################################

class PersonalSettings_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @cog_ext.cog_slash(
        name="개인설정",
        description="개인설정을 확인 또는 수정 합니다.",
        guild_ids=guilds_id,
        options=[
            create_option(
                name="설정리스트",
                description="설정할 수 있는 리스트을 확인합니다.",
                option_type=OptionType.STRING,
                required=True,
                choices=[
                    create_choice(
                        name="설정정보",
                        value="설정정보"
                    ),
                    create_choice(
                        name="자산정보 공개하기",
                        value="InformationDisclosure"
                    ),
                    create_choice(
                        name="지원금으로 얻은 돈 표시",
                        value="ShowSupportFund"
                    ),
                    create_choice(
                        name="주식차트 표시",
                        value="ShowStockChartImage"
                    ),
                    create_choice(
                        name="지원금 쿨타임 바로표시여부",
                        value="ShowSupportFundCooldown"
                    ),
                    create_choice(
                        name="자산정보에 어제 대비 가격 표시 여부",
                        value="ShowComparedPrice"
                    ),
                    create_choice(
                        name="관심주가 공개표시 여부",
                        value="ShowInterestStockList"
                    )
                ]
            ),
            create_option(
                name="boolean",
                description="참(True), 거짓(False)를 설정합니다.",
                option_type=OptionType.BOOLEAN,
                required=False
            )
        ],
        connector={"설정리스트": "setting", "boolean": "boolean"}
    )
    async def _PersonalSettings(self, ctx: SlashContext, setting: str, boolean: Union[bool, str]=None):
        await _PersonalSettings_code(ctx, setting, boolean)
        
    @_PersonalSettings.error
    async def _PersonalSettings_error(self, ctx: SlashContext, error):
        logger.waring(error)
        await ctx.send(f"에러가 발생하였습니다.\n```{error}```")

######################################################################################################################################################

class PersonalSettings_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="개인설정", aliases=["설정"])
    async def _PersonalSettings(self, ctx: Context, setting: str, boolean: Union[bool, str]=None):
        await _PersonalSettings_code(ctx, setting, boolean)
    
    @_PersonalSettings.error
    async def _PersonalSettings_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            logger.warning("「설정타입」을 입력해 주세요.")
            await ctx.reply("「설정타입」을 입력해 주세요.")
        
        elif isinstance(error.original, KeyError):
            logger.warning("「true」또는「false」만 입력해 주세요.")
            await ctx.reply("「true」또는「false」만 입력해 주세요.")
            
        else:
            logger.warning(error)
            await ctx.send(f"에러가 발생하였습니다.\n```{error}```")
    
######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(PersonalSettings_Context(bot))
    bot.add_cog(PersonalSettings_SlashContext(bot))