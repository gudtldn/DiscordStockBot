from discord.ext.commands import Context

from discord_slash import SlashContext

from datetime import timedelta, datetime

from json import load, dump

from random import randint

from typing import Union

DEBUGGING = True

# guilds_id = (925277183147147265, 915543134648287242, 921706352957620285)
guilds_id = (940546043651710986,)

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
        'Settings': {
            'InformationDisclosure': True,
            'ShowSupportFund': True
        },
        'StockDict': {},
        'Stock': {}
    }
    return dictionary

def GetStockDictionary() -> dict:
    with open('./json/StockDictionary.json', 'r', encoding='utf-8') as Inf:
        return load(Inf)

def GetUserInformation() -> list[dict]: #Information.json에 있는 값 불러오기
    with open('./json/UserInformation.json', 'r', encoding='utf-8') as Inf:
        return load(Inf)

def SetUserInformation(json_data: list[dict]):
    with open('./json/UserInformation.json', 'w', encoding='utf-8') as Inf:
        dump(json_data, Inf, indent='\t', ensure_ascii=False)

def GetArrayNum(ctx: Union[Context, SlashContext, int]): #ctx.author.id가 들어있는 배열의 번호를 반환
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
    # return any(error_context in i for i in error.args)
    return error_context in error.args

################################################################################ 클래스 선언 ################################################################################

class ConvertSecToTimeStruct():
    '''
    (day, hour, min, sec)
    '''
    def __init__(self, seconds: int):
        _delta = timedelta(seconds=seconds)
        self.day = _delta.days
        
        _delta = str(timedelta(seconds=_delta.seconds)).split(':')
        self.hour24 = int(_delta[0])
        self.min = int(_delta[1])
        self.sec = int(_delta[2])
        
        self.hour12 = int(_delta[0])-12 if self.hour24 >= 12 else int(_delta[0])