import sys
import os
import time
from datetime import timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
# if sys.platform.startswith('win'):
#     sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
# elif sys.platform == 'darwin':
#     sys.path.append("../")

import configparser
import requests
from concurrent.futures import ProcessPoolExecutor
import common.fun as common
import auth_email.auth_email_main as main_process

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

mode = ""
start_time = time.time()


# 주문 체크
def fetch_order() -> None:
    active_accounts = [
        ['malek_hessen784|mD@#45546486486465|Miroslava_Ilina2456@rambler.ru|yativwer_A2456|49.254.40.101:6918']
    ]
    process_order(active_accounts)


# 주문 실행
def process_order(active_accounts: list):

    max_workers = common.get_optimal_max_workers()
    common.log(f"최대 작업 인스턴스: {max_workers}")

    total_success = 0
    total_fail = 0
    for active_account in active_accounts:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(
                main_process.main_fun
                , index
                , account.split('|')[0]
                , account.split('|')[1]
                , account.split('|')[4]
                , mode
                , account.split('|')[0]
                , account.split('|')[2]
                , account.split('|')[3]
            ) for index, account in enumerate(active_account)]
            results = [future.result() for future in futures]

            total_success += sum(int(result.split(',')[0]) for result in results)
            total_fail += sum(int(result.split(',')[1]) for result in results)

    end_time = time.time()
    global start_time
    elapsed_time = timedelta(seconds=end_time - start_time)
    formatted_time = common.format_timedelta(elapsed_time)
    common.log(f"걸린시간: {formatted_time} 계정개수 {total_success + total_fail}")



def main():
    common.send_message(config['telegram']['chat_order_id'], '시작')
    # 시작 함수
    fetch_order()


if __name__ == '__main__':
    main()
