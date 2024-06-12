import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import os


# 예제 main_fun 정의 (사용자 정의 함수)
def main_fun(index, username, password, param4, order_id, quantity, order_url, mode):
    log_filename = f"process_{index}.log"

    # 로그 설정
    logger = logging.getLogger(f"Process_{index}")
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러 추가
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 로그 예제 출력
    logger.debug(f"Starting process {index} with user {username}")

    # 실제 작업 로직을 여기에 추가합니다.
    # 작업 완료 후 로그 출력 예제
    logger.debug(f"Finished process {index}")

    return "1,0"  # 예제 반환값, 성공과 실패 수를 반환


# 병렬 처리 설정
def parallel_process(active_account, order_id, quantity, order_url, mode, max_workers=4):
    total_success = 0
    total_fail = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                main_fun,
                index,
                account.split('|')[0],
                account.split('|')[1],
                account.split('|')[4],
                order_id,
                quantity,
                order_url,
                mode
            )
            for index, account in enumerate(active_account)
        ]
        results = [future.result() for future in futures]

        total_success += sum(int(result.split(',')[0]) for result in results)
        total_fail += sum(int(result.split(',')[1]) for result in results)

    return total_success, total_fail


# 예제 실행
if __name__ == "__main__":
    active_account = [
        "user1|pass1|param3|param4|param5",
        "user2|pass2|param3|param4|param5",
        # 추가 계정
    ]
    order_id = "order123"
    quantity = 10
    order_url = "http://example.com/order"
    mode = "test"

    total_success, total_fail = parallel_process(active_account, order_id, quantity, order_url, mode)
    print(f"Total Success: {total_success}, Total Fail: {total_fail}")
