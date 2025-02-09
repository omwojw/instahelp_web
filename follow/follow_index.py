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
import follow.follow_main as main_process

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 계정 읽기
accounts = common.get_accounts('account.txt')

# 글로벌 변수
order_service = config['item']['follow']
order_log_path = "../log/order_history.txt"

mode = ""
start_time = time.time()


# 주문 체크
def fetch_order() -> None:
    # 주문 중복체크
    is_dupl_order = common.dupl_check(int(config['api']['follow_service']), order_service, order_log_path)
    if is_dupl_order:
        return

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
        order_id = common.get_test_order_id()
        quantity = int(config['item']['test_quantity'])
        order_url = str(config['item']['test_follow_order_url'])
        mode = "TEST"
    else:
        order_id = res['id']
        quantity = int(res['quantity'])
        order_url = res['link']
        mode = "LIVE"
    common.log(f'모드 : {mode}')

    if 'instagram.com' not in order_url:
        order_url = f'https://www.instagram.com/{order_url}'

    # 계정 선별
    filter_accounts = common.set_filter_accounts(order_service, order_url, accounts)

    # 할당량이 많은 남은 순으로 정렬
    sorted_accounts = common.set_sort_accouts(order_service, filter_accounts)

    # 작업 가능한 계정이 없는경우 취소처리
    if len(sorted_accounts) == 0:
        common.not_working_accounts(order_log_path, order_service, order_id, quantity)
        return

    # 최대 개수 체크
    if common.order_max_check(quantity):
        common.max_order_log(order_log_path, order_service, order_id, quantity)
        return

    # 계정 개수에 따른 브라우저 셋팅
    active_accounts = common.account_setting(sorted_accounts, quantity)

    # 현황 로그
    common.log(
        f'주문번호[{order_id}], 주문건수[{quantity}], 가용 가능한 계정[{len(sorted_accounts)}]')

    # 프로세스 실행
    process_order(order_id, quantity, order_url, active_accounts)


# 주문 실행
def process_order(order_id: str, quantity: int, order_url: str, active_accounts: list):

    # 테스트 환경에서만 활용
    # order_url = common.get_target('target.txt').split('|')[0]
    # active_accounts = [
    #     [
    #         "monika3_e2024|anha33|monika3e@inbox.lv|sdfgdrfgtg34#|121.126.28.216:5128"
    #         , "nafs_a46d|anha33|nafsa46d@inbox.lv|Fiza667#|49.254.126.142:5606"
    #         , "mohima_t3|anha33|mohimat3@inbox.lv|Raisa566#|121.126.47.35:5835"
    #         , "raisa5_6ty|anha33|raisa56ty@inbox.lv|nafsa46d#|124.198.21.50:6017"
    #         , "nafs_a565r|anha33|nafsa565r@inbox.lv|nafsa575#|121.126.139.175:5644"
    #         , "mohim_a4637|anha33|monika565@inbox.lv|nafsa6758#|121.126.106.175:5471"
    #         , "monik_a66ty|anha33|monika66ty@inbox.lv|Raisa665#|49.254.24.198:6825"
    #         , "rais_a383s|anha33|raisa383s@inbox.lv|Fiza8477#|183.78.134.78:6371"
    #         , "mohim_a576h|anha33|mohima576h@inbox.lv|Raisa676#|121.126.129.151:5255"
    #         , "mohim_a465|anha33|mohima4655@inbox.lv|Munia5643#|49.254.190.27:6680"
    #         , "fibiijn_kg4|anha33|fibiijnkg4@inbox.lv|nafsadhkb4#|124.198.43.139:6082"
    #         , "raisarg_h4|anha33|raisargh4@inbox.lv|Evanauio34#|49.254.23.118:6801"
    #         , "nafsad_yg4|anha33|nafsadyg@inbox.lv|Umkzkzk3#|49.254.224.178:5027"
    #         , "peetergf64422|Chjdw467hh|Peetergf6442@outlook.com|jft965eurrig|49.254.24.197:6824"
    #         , "russellhamiltony65333|Vfs345fgjjx|RussellHamiltony6533@outlook.com|itte865ehffu|115.144.234.138:5370"
    #      ]
    # ]


    for active_account in active_accounts[0][:]:
        active_id = active_account.split('|')[0]
        if active_id == order_url:
            active_accounts[0].remove(active_account)

    if not order_url:
        return

    if 'instagram.com' not in order_url:
        order_url = f'https://www.instagram.com/{order_url}'


    max_workers = common.get_optimal_max_workers()
    common.log(f"최대 작업 인스턴스: {max_workers}")

    total_success = 0
    total_fail = 0
    for active_account in active_accounts:
        common.sleep(1)
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

    if mode == 'LIVE':
        common.result_api(order_id, total_success, total_fail, quantity)

    # 주문 최종 결과 로그 저장
    common.write_order_log(order_log_path, order_service, order_id, quantity, total_success, total_fail, formatted_time)


def main():
    common.send_message(config['telegram']['chat_order_id'], '시작')
    # 시작 함수
    fetch_order()


if __name__ == '__main__':
    main()
