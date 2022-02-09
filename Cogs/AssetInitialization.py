#초기화

from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.errors import MissingRequiredArgument

from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType as OptionType
from discord_slash.utils.manage_commands import create_option


from typing import Union

from module._define_ import *

######################################################################################################################################################

async def _AssetInitialization_code(ctx: Union[Context, SlashContext], string: str):
    logger.info(f'{ctx.author.name}: {ctx.invoked_with} {string}')
    
    if not IsVaildUser(ctx):
        logger.info('먼저 `.사용자등록` 부터 해 주세요.')
        await ctx.reply('먼저 `.사용자등록` 부터 해 주세요.')
        return
    
    if string == '초기화확인':
        json_data = GetUserInformation()
        del(json_data[GetArrayNum(ctx)])
        json_data.append(AddUser(ctx.author.id)) #사용자 추가
        SetUserInformation(json_data)
        logger.info('초기화가 완료되었습니다.')
        await ctx.reply('초기화가 완료되었습니다.')
    
    else:
        if isinstance(ctx, Context):
            logger.info('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
            await ctx.reply('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        else:
            logger.info('「초기화확인」을 입력해야 초기화 할 수 있습니다.')
            await ctx.reply('「초기화확인」을 입력해야 초기화 할 수 있습니다.')

######################################################################################################################################################

class AssetInitialization_SlashContext(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
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
    async def _AssetInitialization(self, ctx: SlashContext, string: str):
        await _AssetInitialization_code(ctx, string)
        
####################################################################################################

class AssetInitialization_Context(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='초기화', aliases=[])
    async def _AssetInitialization(self, ctx: Context, string: str):
        await _AssetInitialization_code(ctx, string)
        
    @_AssetInitialization.error
    async def _Initialization_error(self, ctx: Context, error):
        if isinstance(error, MissingRequiredArgument):
            logger.warning('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
            await ctx.reply('「.초기화 초기화확인」을 입력해야 초기화 할 수 있습니다.')
        
        else:
            logger.warning(error)
            await ctx.reply(error)

######################################################################################################################################################

def setup(bot: commands.Bot):
    bot.add_cog(AssetInitialization_Context(bot))
    bot.add_cog(AssetInitialization_SlashContext(bot))