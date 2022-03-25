DiscordStockBot.py
==================

## 명령어 목록
**봇 접두사: `.` 또는 `/`**

### [사용자등록](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/AddUser.py "소스코드로 가기")
---
> 데이터 베이스에 사용자를 등록합니다.
>* 다른이름: 등록
>> 사용방법
>>* 사용자등록

### [지원금](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/SupportFund.py "소스코드로 가기")
---
> 1만원 ~ 10만원 사이의 돈을 랜덤으로 지급합니다.
>* 다른이름: 돈받기
>> 사용방법
>>* 지원금

### [개인설정](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/PersonalSettings.py "소스코드로 가기")
---
> 개인설정을 확인 또는 수정합니다.
>* 다른이름: 설정
>> 사용방법
>>* 개인설정 **설정정보**
>>* 개인설정 **자산정보** [true | false]
>>* 개인설정 **지원금표시** [true | false]
>>* 개인설정 **차트표시** [true | false]
>>* 개인설정 **쿨타임표시** [true | false]

### [자산정보](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/AssetInformation.py "소스코드로 가기")
---
> 자신의 자산정보를 확인합니다.
>* 다른이름: 자산조회
>> 사용방법
>>* 자산정보
>>* 자산정보 [@유저]
>>* 자산정보 [랭킹 | 순위]

### [주가](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/StockPrices.py "소스코드로 가기")
---
> 입력한 기업의 현재 주가를 확인합니다.
>* 다른이름: 시세
>> 사용방법
>>* 주가 [기업이름 | 기업번호]

### [매수](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/StockPurchase.py "소스코드로 가기")
---
> 입력한 기업의 주식을 매수합니다.
>* 다른이름: 구매, 주식구매, 주식매수
>> 사용방법
>>* 매수 [기업이름 | 기업번호] [매수 할 주식 개수]
>>* 매수 [기업이름 | 기업번호] [풀매수 | 모두]

### [매도](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/StockSelling.py "소스코드로 가기")
---
> 입력한 기업의 주식을 매도합니다.
>* 다른이름: 판매, 주식판매, 주식매도
>> 사용방법
>>* 매도 [기업이름 | 기업번호] [매도 할 주식 개수]
>>* 매도 [기업이름 | 기업번호] [풀매도 | 모두]

### [초기화](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/AssetInitialization.py "소스코드로 가기")
---
> 「초기화확인」를 입력해 자신의 자산정보를 초기화 합니다.
>> 사용방법
>>* 초기화 **초기화확인**

### [회원탈퇴](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/Withdrawal.py "소스코드로 가기")
---
> 「탈퇴확인」를 입력해 데이터 베이스에서 자신의 자산정보를 삭제합니다.
>* 다른이름: 탈퇴
>> 사용방법
>>* 회원탈퇴 **탈퇴확인**

### [단축어설정](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/ShortenedWordSetting.py "소스코드로 가기")
---
> 단축어목록을 확인하거나, 추가 또는 제거합니다.
>> 사용방법 (빗금 명령어)
>>* /단축어설정 **목록**
>>* /단축어설정 **추가** [단축어로 설정하고 싶은 이름] [기업번호]
>>* /단축어설정 **제거** [단축어로 설정한 이름]
>
>> 사용방법 (일반 명령어)
>>* .단축어설정 **목록**
>>* .단축어설정 **추가** -이름 [단축어로 설정하고 싶은 이름] -번호 [기업번호]
>>* .단축어설정 **추가** -번호 [기업번호]
>>* .단축어설정 **제거** -이름 [단축어로 설정한 이름]

### [도움말](https://github.com/gudtldn/DiscordStockBot/blob/main/Cogs/HelpCommand.py "소스코드로 가기")
---
> 등록되어있는 명령어들을 나열합니다. (일반 명령어 전용)
>* 다른이름: 명령어, ?
>> 사용방법
>>* .도움말
>>* .도움말 [명령어]