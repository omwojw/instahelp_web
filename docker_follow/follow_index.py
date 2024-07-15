import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
# if sys.platform.startswith('win'):
#     sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
# elif sys.platform == 'darwin':
#     sys.path.append("../")

import configparser
from concurrent.futures import ProcessPoolExecutor
import common.fun as common
import docker_follow.follow_main as main_process
import json

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 계정 읽기
accounts = json.loads(sys.argv[1])

order_id = sys.argv[2]
quantity = int(sys.argv[3])
order_url = sys.argv[4]

# 글로벌 변수
order_service = config['item']['follow']
order_log_path = "../log/order_history.txt"

mode = ""


# 주문 체크
def fetch_order() -> None:
    global accounts
    process_order(accounts)


# 주문 실행
def process_order(active_accounts: list):
    # active_accounts = ['cuoyuecatybo67|hacolidu44|aleksandrlebedevvs2786@rambler.ru|AiiUurOrndHy176|115.144.250.217:5321']

    max_workers = common.get_optimal_max_workers()
    common.log(f"최대 작업 인스턴스: {max_workers}")

    total_success = 0
    total_fail = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(
            main_process.main_fun
            , index
            , account.split('|')[0]
            , account.split('|')[1]
            , account.split('|')[4]
            , order_id
            , quantity
            , order_url
            , mode
            , account.split('|')[0]
        ) for index, account in enumerate(active_accounts)]
        results = [future.result() for future in futures]

        total_success += sum(int(result.split(',')[0]) for result in results)
        total_fail += sum(int(result.split(',')[1]) for result in results)

    # 실제 콘솔에 찍는 내용보다는 _docker.py 에서 결과 출력하기 위한 콘솔용
    common.log(f'최종결과[{total_success},{total_fail}]')


def main():
    # 시작 함수
    fetch_order()
    # return common.log(f'최종결과[1,1]')


if __name__ == '__main__':
    main()
