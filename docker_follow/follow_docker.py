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
import common.fun as common
import docker
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
import traceback
import os


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
        # order_id = common.get_test_order_id()
        # quantity = int(config['item']['test_quantity'])
        # order_url = str(config['item']['test_follow_order_url'])
        # mode = "TEST"
        common.send_message(config['telegram']['chat_order_id'], '주문없음')
        exit()
    else:
        order_id = res['id']
        quantity = int(res['quantity'])
        order_url = res['link']
        # start_count = common.get_follow_count(current_os, order_url)
        # common.set_start_count(order_id, start_count)
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
    browser_cnt, active_accounts = common.account_docker_setting(sorted_accounts, quantity)

    # 컨테이너와 계정 일치하는지 체크
    act_cnt = 0
    for idx, active_ac in enumerate(active_accounts):
        act_cnt += len(active_ac)
    if quantity != act_cnt and len(sorted_accounts) != act_cnt:
        common.cul_working_accounts(order_log_path, order_service, order_id, quantity)
        return

    # 현황 로그
    common.log(
        f'주문번호[{order_id}], 주문건수[{quantity}], 가용 가능한 계정[{len(sorted_accounts)}], 컨테이너 사용개수[{len(active_accounts)}], 컨테이너별 브라우저 사용개수[{browser_cnt}], 배열의 계정개수[{len(active_accounts)}]{[len(a) for a in active_accounts]}')

    # 프로세스 실행
    process_order(order_id, quantity, order_url, active_accounts)


# 주문 실행
def process_order(order_id: str, quantity: int, order_url: str, active_accounts: list):
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    subprocess.run(
        ["docker-compose", "up", "-d", "--scale", f"s={len(active_accounts)}", "--build"],
        check=True,
        cwd=project_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

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
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(
            open_docker
            , index
            , account
            , order_id
            , quantity
            , order_url
        ) for index, account in enumerate(active_accounts)]
        results = [future.result() for future in futures]

        total_success += sum(int(result.split(',')[0]) for result in results)
        total_fail += sum(int(result.split(',')[1]) for result in results)

    end_time = time.time()
    global start_time
    elapsed_time = timedelta(seconds=end_time - start_time)
    formatted_time = common.format_timedelta(elapsed_time)
    common.log(f"걸린시간: {formatted_time}, 계정개수 {total_success + total_fail}")

    if mode == 'LIVE':
        common.result_api(order_id, total_success, total_fail, quantity)

    # 주문 최종 결과 로그 저장
    common.write_order_log(order_log_path, order_service, order_id, quantity, total_success, total_fail, formatted_time)


def open_docker(index: int, active_account: list, order_id: str, quantity: int, order_url: str) -> str:
    client = docker.from_env()
    containers = client.containers.list()
    container = containers[index]
    # common.log(f"컨테이너 실행성공", container.name, index + 1)

    try:
        # 컨테이너 내에서 명령 실행
        command = f'python /instahelp_web/docker_follow/follow_index.py \'{json.dumps(active_account)}\' {order_id} {quantity} {order_url}'
        exec_id = client.api.exec_create(container.id, command)
        output = client.api.exec_start(exec_id, stream=True)

        result_print = ""
        for line in output:
            result_print += line.decode("utf-8")

        success = common.extract_final_results(result_print, 'SUCCESS')
        fail = common.extract_final_results(result_print, 'FAIL')

        if not success:
            success = 0
        if not fail:
            fail = 0

        if (success + fail) != len(active_account):
            common.remove_from_error(result_print, order_id, container.name)

        common.log(f"컨테이너 실행종료, 실행개수: [{success + fail}], 성공: [{success}], 실패: [{fail}]", container.name, index + 1)
        return f"{success},{fail}"
    except Exception as e:
        common.remove_from_error(traceback.format_exc(), order_id, container.name)
        return f"0,0"
    finally:
        if container:
            container.stop()


def main():
    # 시작 함수
    common.send_message(config['telegram']['chat_order_id'], '시작')
    fetch_order()

    # from datetime import datetime
    # now = datetime.now()
    # current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # common.log(current_time)
    # common.auth_outlook(current_os, 5, '203.109.6.85:6441', 'buhelejyaaga85', 1)


if __name__ == '__main__':
    main()
