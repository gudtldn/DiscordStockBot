#도움말

import discord
from discord.ext import commands
from discord.ext.commands import Context

from module.__define__ import *

class HelpCommand_Context(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="도움말", aliases=["명령어", "?"])
    async def _HelpCommand(self, ctx: Context, command: str=None):
        logger.info(f"[{type(ctx)}] {ctx.author.name}: {ctx.invoked_with} {command}")
        
        if command is not None:
            command = command.replace(".", "")
        
        if command is None:
            embed = discord.Embed(title="도움말", description="[] <-- 필수 입력항목 | <> <-- 선택 입력항목", color=RandomEmbedColor())
            embed.add_field(name=".사용자등록", value="데이터 베이스에 사용자를 등록합니다.", inline=False)
            embed.add_field(name=".자산정보", value="현재 자신의 자산정보를 확인합니다.", inline=False)
            embed.add_field(name=".주가", value="현재 주가를 검색합니다.", inline=False)
            embed.add_field(name=".매수", value="입력한 기업의 주식을 매수합니다.", inline=False)
            embed.add_field(name=".매도", value="입력한 기업의 주식을 매도합니다.", inline=False)
            embed.add_field(name=".지원금", value="1만원 ~ 10만원 사이에서 랜덤으로 지원금을 지급합니다.", inline=False)
            embed.add_field(name=".초기화", value="자신의 자산정보를 초기화 합니다.", inline=False)
            embed.add_field(name=".탈퇴", value="이 봇에 저장되어있는 사용자의 정보를 삭제합니다.", inline=False)
            embed.add_field(name=".개인설정", value="개인설정을 확인 또는 수정합니다.", inline=False)
            embed.set_footer(text="명령어를 자세히 보려면 「.도움말 <명령어 이름>」 을 써 주세요.")
            await ctx.reply(embed=embed)

        elif command in ("도움말", "명령어", "?"):
            command_list = ["도움말", "명령어", "?"]
            command_list.remove(command)
            
            embed = discord.Embed(title="도움말", description="등록되어있는 명령어들을 출력합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            await ctx.reply(embed=embed)

        elif command in ("사용자등록", "등록"):
            command_list = ["사용자등록", "등록"]
            command_list.remove(command)
            
            embed = discord.Embed(title="사용자등록", description="데이터 베이스에 사용자를 등록합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            await ctx.reply(embed=embed)
        
        elif command in ("자산정보", "자산조회"):
            command_list = ["자산정보", "자산조회"]
            command_list.remove(command)
            
            embed = discord.Embed(title="자산정보", description="자신의 자산정보를 확인합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            embed.add_field(name=".자산정보 <@유저>", value="@유저의 자산정보를 확인합니다.", inline=False)
            embed.add_field(name=".자산정보 <랭킹 | 순위>", value="이 서버에 있는 유저의 자산랭킹을 나열합니다.", inline=False)
            await ctx.reply(embed=embed)
        
        elif command in ("주가", "시세"):
            command_list = ["주가", "시세"]
            command_list.remove(command)
            
            embed = discord.Embed(title="주가", description="검색한 기업의 현재 주가를 확인합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            embed.add_field(name=".주가 [기업이름 | 기업번호]", value="기업이름 또는 기업번호로 검색합니다.", inline=False)
            await ctx.reply(embed=embed)

        elif command in ("매수", "구매", "주식구매", "주식매수"):
            command_list = ["매수", "구매", "주식구매", "주식매수"]
            command_list.remove(command)
            
            embed = discord.Embed(title="매수", description="입력한 기업의 주식을 매수합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            embed.add_field(name=".매수 [기업이름 | 기업번호] [매수 할 주식 개수]", value="입력한 기업의 주식을, 주식 개수만큼 매수합니다.", inline=False)
            embed.add_field(name=".매수 [기업이름 | 기업번호] [풀매수 | 모두]", value="입력한 기업의 주식을 최대까지 매수합니다.", inline=False)
            await ctx.reply(embed=embed)
        
        elif command in ("매도", "판매", "주식판매", "주식매도"):
            command_list = ["매도", "판매", "주식판매", "주식매도"]
            command_list.remove(command)
            
            embed = discord.Embed(title="매도", description="입력한 기업의 주식을 매도합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            embed.add_field(name=".매도 [기업이름 | 기업번호] [매도 할 주식 개수]", value="입력한 기업의 주식을, 주식 개수만큼 매도합니다.", inline=False)
            embed.add_field(name=".매도 [기업이름 | 기업번호] [반매도]", value="입력한 기업의 주식의 절반을 매도합니다.", inline=False)
            embed.add_field(name=".매도 [기업이름 | 기업번호] [풀매도 | 모두]", value="입력한 기업의 주식을 모두 매도합니다.", inline=False)
            await ctx.reply(embed=embed)
        
        elif command in ("지원금", "돈받기"):
            command_list = ["지원금", "돈받기"]
            command_list.remove(command)
            
            embed = discord.Embed(title="지원금", description="1만원 ~ 10만원 사이에서 랜덤으로 지급합니다. (쿨타임: 4시간)", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            await ctx.reply(embed=embed)
            
        elif command == "초기화":
            embed = discord.Embed(title="초기화", description="「초기화확인」를 입력해 자신의 자산정보를 초기화 합니다.", color=RandomEmbedColor())
            embed.add_field(name=".초기화 [확인문구]", value="확인문구에는 「초기화확인」를 입력해 주세요.")
            await ctx.reply(embed=embed)
            
        elif command in ("탈퇴", "회원탈퇴"):
            command_list = ["탈퇴", "회원탈퇴"]
            command_list.remove(command)
            
            embed = discord.Embed(title="탈퇴", description="「탈퇴확인」를 입력해 저장되어있는 자신의 정보를 삭제합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            embed.add_field(name=".탈퇴 [확인문구]", value="확인문구에는 「탈퇴확인」를 입력해 주세요.")
            await ctx.reply(embed=embed)
            
        elif command in ("개인설정", "설정"):
            command_list = ["개인설정", "설정"]
            command_list.remove(command)
            
            embed = discord.Embed(title="개인설정", description="개인설정을 확인 또는 수정합니다.", color=RandomEmbedColor())
            embed.add_field(name="다른이름", value=f"{', '.join(command_list)}", inline=False)
            embed.add_field(name=".개인설정 [설정정보]", value="설정할 수 있는 목록을 나열합니다.", inline=False)
            embed.add_field(name=".개인설정 [자산정보] [true | false]", value="자산정보 공개여부를 설정합니다.", inline=False)
            embed.add_field(name=".개인설정 [지원금표시] [true | false]", value="지원금으로 얻은 돈 표시여부를 설정합니다.", inline=False)
            embed.add_field(name=".개인설정 [차트표시] [true | false]", value="`주가`명령어에 차트를 표시합니다.", inline=False)
            embed.add_field(name=".개인설정 [쿨타임표시] [true | false]", value="`지원금`명령어에 쿨타임을 바로 표시합니다.", inline=False)
            await ctx.reply(embed=embed)
            
        else:
            await ctx.reply("알 수 없는 명령어 입니다.")
            
def setup(bot: commands.Bot):
    bot.add_cog(HelpCommand_Context(bot))