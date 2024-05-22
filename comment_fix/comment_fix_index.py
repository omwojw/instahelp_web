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
import comment_fix.comment_fix_main as comment_fix_main

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 계정 읽기
accounts = common.get_accounts('account.txt')

# 글로벌 변수
order_service = config['item']['comment_fix']
order_log_path = "../log/order_history.txt"

mode = None


# 주문 체크
def fetch_order() -> bool:
    # 주문 중복체크
    is_dupl_order = common.dupl_check(config['api']['comment_service'], order_service, order_log_path)
    if is_dupl_order:
        return

    global mode
    # 신규 주문건 체크
    res = requests.get(config['api']['url'],
                        data={
                            'key': config['api']['key'],
                            'action': 'getOrder',
                            'type': config['api']['comment_service']
                        }, timeout=10).json()
    # 결과가 성공이 아니면
    if res['status'] != 'success':
        order_id = config['item']['test_comment_fix_order_id']
        quantity = int(config['item']['test_comment_fix_quantity'])
        comments = config['item']['test_comment_fix_comment'].split("\\n")
        order_url = str(config['item']['test_comment_fix_order_url'])
        mode = "TEST"
    else:
        order_id = res['id']
        quantity = int(res['quantity'])
        comments = res['comments'].split("\\n")
        order_url = res['link']
        mode = "LIVE"

    # 할당량을 다 한 계정 추출
    not_accounts = common.get_workings(order_service)

    # 할당량을 다 한 계정 제거
    filter_accounts = [account for account in accounts if account.split('|')[0] not in not_accounts]

    if len(filter_accounts) == 0:
        common.status_change(order_id, 'setCanceled')

    # 계정 개수에 따른 브라우저 셋팅
    active_accounts = common.account_setting(filter_accounts, quantity)

    common.log(f'모드 : {mode}')
    process_order(order_id, quantity, comments, order_url, active_accounts)


# 주문 실행
def process_order(order_id: str, quantity: int, comments: list, order_url: str, active_accounts: list):

    total_success = 0
    total_fail = 0
    for active_account in active_accounts:
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(
                comment_fix_main.mainFun
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
