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
import follow.follow_main as follow_main

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 계정 읽기
accounts = common.get_accounts('account.txt')

# 글로벌 변수
order_service = "FOLLOW"
order_log_path = "../log/order_history.txt"

mode = None


# 주문 체크
def fetch_order() -> bool:
    global mode
    # 신규 주문건 체크
    res = requests.get(config['api']['url'],
                        data={
                            'key': config['api']['key'],
                            'action': 'getOrder',
                            'type': config['api']['follow_service']
                        }, timeout=10).json()
    # 결과가 성공이 아니면
    if res['status'] != 'success':
        order_id = config['item']['test_follow_order_id']
        quantity = int(config['item']['test_follow_quantity'])
        order_url = str(config['item']['test_follow_order_url'])
        mode = "TEST"
    else:
        order_id = res['id']
        quantity = int(res['quantity'])
        order_url = res['link']
        mode = "LIVE"

    if 'instagram.com' not in order_url:
        order_url = f'https://www.instagram.com/{order_url}/'

    if len(accounts) > quantity:
        active_accounts = accounts[:quantity]
    else:
        active_accounts = accounts
    common.log(f'모드 : {mode}')
    process_order(order_id, quantity, order_url, active_accounts)


# 주문 실행
def process_order(order_id: str, quantity: int, order_url: str, active_accounts: list):

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(
            follow_main.mainFun
            , index
            , account.split('|')[0]
            , account.split('|')[1]
            , account.split('|')[4]
            , order_id
            , quantity
            , order_url
            , mode
        ) for index, account in enumerate(active_accounts)]
        results = [future.result() for future in futures]

        total_success = sum(int(result.split(',')[0]) for result in results)
        total_fail = sum(int(result.split(',')[1]) for result in results)

        if total_success == quantity:  # 전체 성공
            res = requests.post(config['api']['url'], data={
                'key': config['api']['key'],
                'action': 'setCompleted',
                'id': order_id
            }, timeout=10)
            common.log("[Success] -  작업 완료")
            common.log(f"[Success] -  주문 번호 : {order_id}")
            common.log(f"[Success] -  주문 수량 : {quantity}")
            common.log(f"[Success] -  상태 변경 결과 : {res}")
        else:  # 부분 성공
            res = requests.post(config['api']['url'], data={
                'key': config['api']['key'],
                'action': 'setPartial',
                'id': order_id,
                'remains': quantity - total_success
            }, timeout=10)
            common.log("[Success] -  작업 부분 완료")
            common.log(f"[Success] -  주문 번호 : {order_id}")
            common.log(f"[Success] -  주문 수량 : {quantity}")
            common.log(f"[Success] -  남은 수량 : {quantity - total_success}")
            common.log(f"[Success] -  상태 변경 결과 : {res}")
            common.log(f"총 성공: {total_success}, 총 실패: {total_fail}")

        # 주문 최종 결과 로그 저장
        common.write_order_log(order_log_path, order_service, order_id, quantity, total_success, total_fail)


def main():
    # 시작 함수
    fetch_order()


if __name__ == '__main__':
    main()
