from discord.ext.commands import Context
from discord_slash import SlashContext

import requests

from ast import literal_eval

from time import time
from datetime import timedelta, datetime

from functools import wraps

from random import randint

from json import load, dump

from os import chdir, getcwd
from platform import system

from traceback import format_exc

from typing import Union

DEBUGGING = system() == "Windows" #윈도우에서 실행될 시 디버그 켜짐

if DEBUGGING:
    guilds_id = (940546043651710986,)
else:
    guilds_id = (925277183147147265, 915543134648287242, 921706352957620285)

################################################################################ 로깅

def _Logging(): #변수의 혼용을 막기위해 함수로 만듦
    import logging

    now = datetime.today().strftime("%Y-%m-%d_%H-%M-%S")

    global logger
    logger = logging.getLogger()
    if DEBUGGING:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter(u"[%(asctime)s][%(levelname)s]: <%(module)s> [%(funcName)s | %(lineno)d] >> %(message)s")

    file_handler = logging.FileHandler(f"./logs/{now}.log", encoding="utf-8")
    # file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    
_Logging()

################################################################################ 함수 선언 ################################################################################

def RandomEmbedColor():
    r = lambda: randint(0,255)
    value = f"0x{r():02x}{r():02x}{r():02x}"
    return int(value, 16)

def AddUser():
    return {
        "Deposit": 10000000,
        "TotalAssets": 10000000,
        "SupportFund": 0,
        "SupportFundTime": 0,
        "Settings": {
            "InformationDisclosure": True,
            "ShowSupportFund": True,
            "ShowStockChartImage": False,
            "ShowSupportFundCooldown": False,
            "ShowComparedPrice": False
        },
        "StockDict": {},
        "InterestStock": [],
        "Stock": {}
    }

def GetStockDictionary() -> dict:
    with open("./json/StockDictionary.json", "r", encoding="utf-8") as Inf:
        return load(Inf)

def GetStockInformation(stock_num: str):
    '''
    ['날짜', '시가', '고가', '저가', '종가', '거래량']
    
    Dictionary Keys:
        date: 날짜 -> str
        opening_price: 시가 -> int
        max_price: 고가 -> int
        min_price: 저가 -> int
        closing_price: 종가 -> int
    '''
    url = f"https://api.finance.naver.com/siseJson.naver?symbol={stock_num}&requestType=1\
&startTime={(datetime.today() - timedelta(days=14)).strftime('%Y%m%d')}&endTime={datetime.today().strftime('%Y%m%d')}&timeframe=day"
    
    stock_value: list = literal_eval(requests.get(url).text.replace(" ", "").replace("\n", "").replace("\t", ""))[-2:]
    stock_key: list = ["date", "opening_price", "max_price", "min_price", "closing_price"]
    stock_list: list = sorted([dict(zip(stock_key, value)) for value in stock_value], key=lambda key: key['date'], reverse=True)
    return None if stock_list[0]['date'] == "날짜" else stock_list

def GetUserInformation() -> dict: #Information.json에 있는 값 불러오기
    with open("./json/UserInformation.json", "r", encoding="utf-8") as Inf:
        return load(Inf)

def _SetUserInformation(json_data: dict):
    with open("./json/UserInformation.json", "w", encoding="utf-8") as Inf:
        dump(json_data, Inf, indent="\t", ensure_ascii=False)

def _IsVaildUser(ctx: Union[Context, SlashContext, str]): #ctx.author.id를 가진 유저가 Information.json에 존재하는지 여부
    if isinstance(ctx, (Context, SlashContext)):
        ctx: str = str(ctx.author.id)
    
    if ctx in GetUserInformation().keys():
        return True
    else:
        return False

def ErrorCheck(error, error_context): #찾으려는 에러가 error.args에 있는지 여부
    return error_context in error.args

async def CheckUser(ctx: Union[Context, SlashContext]):
    if ctx.guild is None:
        logger.info("Guild is None")
        return True
    
    if str(ctx.author.id) in GetUserInformation().keys():
        return False
    else:
        logger.info("먼저 `.사용자등록` 부터 해 주세요.")
        await ctx.reply("먼저 `.사용자등록` 부터 해 주세요.")
        return True

################################################################################ 데코레이터 선언 ################################################################################

def CommandExecutionTime(func): #명령어 실행시간 체크 데코레이터 (코루틴 함수에만 사용가능)
    @wraps(func)
    async def wrapper(*args, **kwargs):
        t = time()
        try:
            await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__}: {time() - t}seconds [ERROR]\n{format_exc()}")
            raise e
        else:
            logger.info(f"{func.__name__}: {time() - t}seconds")
    
    return wrapper

################################################################################ 클래스 선언 ################################################################################

class convertSecToTimeStruct():
    '''
    (day, hour, min, sec)
    '''
    def __init__(self, seconds: int):
        _delta = timedelta(seconds=seconds)
        self.day = _delta.days
        
        _delta = str(timedelta(seconds=_delta.seconds)).split(":")
        self.hour = int(_delta[0])
        self.min = int(_delta[1])
        self.sec = int(_delta[2])
    
    def __str__(self):
        return f"{self.day}일 {self.hour}시 {self.min}분 {self.sec}초"

class setUserInformation():
    '''
    with문이 끝나면 자동으로 저장
    '''
    def __init__(self):
        self.json_data = GetUserInformation()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _SetUserInformation(self.json_data)

class getUserInformation():
    '''
    with문이 끝나도 자동으로 저장이 안됨(읽기 전용)
    '''
    def __init__(self):
        self.json_data = GetUserInformation()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class changeDirectory(): #작업경로 변경
    def __init__(self, path: str):
        self.change_path = path
        self.path = getcwd()
    
    def __enter__(self):
        chdir(self.change_path)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        chdir(self.path)