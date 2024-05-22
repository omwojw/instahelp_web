import sys
import os

if sys.platform.startswith('win'):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
elif sys.platform == 'darwin':
    sys.path.append("../")

import configparser
import requests
from concurrent.futures import ProcessPoolExecutor
import common.fun as common
import comment_random.comment_random_main as comment_random_main

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 계정 읽기
accounts = common.get_accounts('account.txt')

# 랜덤 댓글 읽기
comments = common.get_comment_randoms()

# 글로벌 변수
order_service = config['item']['comment_random']
order_log_path = "../log/order_history.txt"

mode = None


# 주문 체크
def fetch_order() -> bool:
    # 주문 중복체크
    is_dupl_order = common.dupl_check(config['api']['comment_random_service'], order_service, order_log_path)
    if is_dupl_order:
        return

    global mode
    # 신규 주문건 체크
    res = requests.get(config['api']['url'],
                        data={
                            'key': config['api']['key'],
                            'action': 'getOrder',
                            'type': config['api']['comment_random_service']
                        }, timeout=10).json()
    # 결과가 성공이 아니면
    if res['status'] != 'success':
        order_id = config['item']['test_comment_random_order_id']
        quantity = int(config['item']['test_comment_random_quantity'])
        order_url = str(config['item']['test_comment_random_order_url'])
        mode = "TEST"
    else:
        order_id = res['id']
        quantity = int(res['quantity'])
        order_url = res['link']
        mode = "LIVE"

    # 계정 선별
    filter_accounts = common.set_filter_accounts(order_service, order_url, accounts)

    # 할당량이 많은 남은 순으로 정렬
    sorted_accounts = common.set_sort_accouts(order_service, filter_accounts)

    # 작업 가능한 계정이 없는경우 취소처리
    if len(sorted_accounts) == 0:
        common.status_change(order_id, 'setCanceled')
        common.write_order_log(order_log_path, order_service, order_id, quantity, 0, 0)
        return

    # 계정 개수에 따른 브라우저 셋팅
    active_accounts = common.account_setting(sorted_accounts, quantity)

    common.log(f'모드 : {mode}')
    process_order(order_id, quantity, order_url, active_accounts)


# 주문 실행
def process_order(order_id: str, quantity: int, order_url: str, active_accounts: list):

    total_success = 0
    total_fail = 0
    for active_account in active_accounts:
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(
                comment_random_main.mainFun
                , index
                , account.split('|')[0]
                , account.split('|')[1]
                , account.split('|')[4]
                , order_id
                , quantity
                , comments[index]
                , order_url
                , mode
                , account.split('|')[0]
            ) for index, account in enumerate(active_account)]
            results = [future.result() for future in futures]

            total_success += sum(int(result.split(',')[0]) for result in results)
            total_fail += sum(int(result.split(',')[1]) for result in results)

    common.result_api(order_id, total_success, total_fail, quantity, order_log_path, order_service)


def main():
    # 시작 함수
    fetch_order()


if __name__ == '__main__':
    main()
