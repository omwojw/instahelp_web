## 인스타헬프 매크로

### Introduction
1.인스타헬프(퍼팩트패널) 주문\
2.1분마다 배치파일 실행(5가지)\
3.신규 주문이 들어온 경우 각 상품별로 주문 진행(매크로 진행)\
4.매크로 완료 후 퍼팩트패널 API를 통한 주문 status 관리\
5.주문완료

### Features
1.팔로우\
2.저장\
3.좋아요\
4.댓글(고정)\
5.댓글(랜덤)

### Installation
1.pip를 통한 모듈 실행\
2.python으로 프로그램 실행(Window는 .bat를 실행하면 됨)\
3.'하이아이피' 프로그램 설치 및 proxy ip 셋팅

### Package
instahelp_web

├── comment_fix #댓글(고정)\
│   ├── comment_fix_index.py #실행\
│   └── comment_fix_main.py #로직\
├── comment_random #댓글(랜덤)\
│   ├── comment_random_index.py #실행\
│   └── comment_random_main.py #로직\
├── common #공통함수\
│   └── fun.py #공통함수\
├── follow #팔로우\
│   ├── follow_index.py #실행\
│   └── follow_main.py #로직\
├── like #좋아요\
│   ├── like_index.py #실행\
│   └── like_main.py #로직\
├── log #로그모음\
│   ├── working #당일 계정별 작업 로그 모음\
│   │   └── working_accounts_XXXXXXXX.txt #일자별 계정별 작업량\
│   ├── dupl_history.txt #주문 진행중 추가 주문 로그\
│   ├── error_accounts.txt #에러 계정 모음\
│   ├── error_log.txt #에러 로그\
│   ├── order_history.txt #주문 로그\
│   ├── task_history.txt #주문별 테스크 로그\
│   └── working_accounts_save.txt #계정별 작업 모음\
├── remove #삭제 예정 파일\
├── resources #리소스 모음\
│   ├── chromedriver #맥북 크롬 드라이버\
│   └── chromedriver.exe #윈도우 크롬 드라이버\
├── save #저장\
│   ├── save_index.py #실행\
│   └── save_main.py #로직\
├── setting #셋팅 데이터모음\
│   ├── account.txt #계정\
│   ├── comment_random.txt #댓글(랜덤)시 댓글 모음\
│   ├── config.ini #각종 설정\
│   └── user_agent.txt #에이전트 모음\
├── venv #파이썬 가상환경\
├── .gitignore #GIT 관리제외 설정파일\
├── comment_fix.bat #댓글(고정) 배치파일\
├── comment_random.bat #댓글(랜덤) 배치파일\
├── follow.bat #팔로우 배치파일\
├── like.bat #좋아요 배치파일\
├── README.md\
└── save.bat #저장 배치파일\
    
