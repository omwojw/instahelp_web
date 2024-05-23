import time
from datetime import datetime
import configparser
import os
import sys
import asyncio
import telegram
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import pyautogui

# Config 읽기
import common.fun

config = configparser.ConfigParser()
current_os = None
if sys.platform.startswith('win'):
    config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'setting', 'config.ini'),
                encoding='utf-8')
    current_os = 'WINDOW'
elif sys.platform == 'darwin':
    config.read('../setting/config.ini', encoding='utf-8')
    current_os = 'MAC'

browser_cnt = int(config['selenium']['browser_cnt'])
telegram_token_key = config['telegram']['token_key']


# config 셋팅
def get_config(new_confit) -> None:
    if sys.platform.startswith('win'):
        new_confit.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'setting', 'config.ini'),
                        encoding='utf-8')
    elif sys.platform == 'darwin':
        new_confit.read('../setting/config.ini', encoding='utf-8')


# 실행 OS 정보
def get_os() -> str:
    if sys.platform.startswith('win'):
        return 'WINDOW'
    elif sys.platform == 'darwin':
        return 'MAC'


# 계정 정보 목록
def get_accounts(path: str) -> list:
    if current_os == 'MAC':
        file_path = f'../setting/{path}'
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../setting/{path}"))

    with open(file_path, 'r', encoding='UTF8') as f:
        accounts = f.readlines()
    account_list = []
    for account in accounts:
        if len(account.strip()) == 0:
            continue
        account_list.append(account.strip())

    # random.shuffle(account_list)
    return account_list


# 계정 태스크가 적은 계정 오름차순 정렬
def set_sort_accouts(service: str, filter_accounts: list) -> list:
    current_time = datetime.now().strftime('%Y%m%d')

    if current_os == 'MAC':
        file_path = f'../log/working/working_accounts_{current_time}.txt'
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../log/working/working_accounts_{current_time}.txt'))

    # 파일 읽기 시도
    try:
        with open(file_path, 'r', encoding='UTF8') as f:
            accounts = f.readlines()
    except FileNotFoundError:
        # 파일이 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='UTF8') as f:
            f.write("")  # 빈 파일 생성
        accounts = []

    with open(file_path, 'r', encoding='UTF8') as f:
        accounts = f.readlines()

    account_list = []
    for account in accounts:
        if len(account.strip()) == 0:
            continue
        if account.split("|")[0] == service:
            account_list.append(account)
    accounts_dict = {item.split('|')[1]: int(item.split('|')[2]) for item in account_list}

    def get_sort_key(a):
        sort_id = a.split('|')[0]
        return accounts_dict.get(sort_id, -1), sort_id

    sorted_filter_accounts = sorted(filter_accounts, key=get_sort_key)
    return sorted_filter_accounts


# 할당량이 넘은 계정 조회
def get_accounts_max_working(service: str) -> list:
    current_time = datetime.now().strftime('%Y%m%d')

    if current_os == 'MAC':
        file_path = f'../log/working/working_accounts_{current_time}.txt'
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../log/working/working_accounts_{current_time}.txt'))

    # 파일 읽기 시도
    try:
        with open(file_path, 'r', encoding='UTF8') as f:
            accounts = f.readlines()
    except FileNotFoundError:
        # 파일이 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='UTF8') as f:
            f.write("")  # 빈 파일 생성
        accounts = []

    with open(file_path, 'r', encoding='UTF8') as f:
        accounts = f.readlines()
    account_list = []
    for account in accounts:
        if len(account.strip()) == 0:
            continue

        pats = account.split("|")
        if pats[0] == service:
            if service == config['item']['follow'] and int(pats[2]) >= int(config['item']['follow_today_cnt']):
                account_list.append(pats[1])
            elif service == config['item']['save'] and int(pats[2]) >= int(config['item']['save_today_cnt']):
                account_list.append(pats[1])
            elif service == config['item']['like'] and int(pats[2]) >= int(config['item']['like_today_cnt']):
                account_list.append(pats[1])
            elif service == config['item']['comment_fix'] and int(pats[2]) >= int(config['item']['comment_fix_today_cnt']):
                account_list.append(pats[1])
            elif service == config['item']['comment_random'] and int(pats[2]) >= int(config['item']['comment_random_today_cnt']):
                account_list.append(pats[1])
    return account_list


# 이미 작업이 되어있는 계정
def get_used_working_accounts(service: str, user_id: str, link: str) -> list:
    if current_os == 'MAC':
        file_path = f'../log/working_accounts_save.txt'
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../log/working_accounts_save.txt'))

    with open(file_path, 'r', encoding='UTF8') as f:
        accounts = f.readlines()
    account_list = []
    for account in accounts:
        if len(account.strip()) == 0:
            continue

        pats = account.split("|")
        pats_service = pats[0]
        pats_user_id = pats[2]
        pats_link = pats[3]

        if pats_service == service:

            if service == config['api']['follow_service']:
                if 'instagram.com' not in pats_link:
                    pats_link = f'https://www.instagram.com/{pats_link}'

                if 'instagram.com' not in link:
                    link = f'https://www.instagram.com/{link}'

            if pats_user_id == user_id and pats_link.strip().upper() == link.strip().upper():
                account_list.append(pats)
    return account_list


# 댓글 랜덤 목록
def get_comment_randoms() -> list:
    if current_os == 'MAC':
        file_path = f'../setting/comment_random.txt'
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../setting/comment_random.txt"))

    with open(file_path, 'r', encoding='UTF8') as f:
        comments = f.readlines()
    comment_list = []
    for comment in comments:
        if len(comment.strip()) == 0:
            continue
        comment_list.append(comment.strip())

    random.shuffle(comment_list)
    return comment_list


# user agent 목록
def get_user_agent() -> list:
    if current_os == 'MAC':
        file_path = f'../setting/user_agent.txt'
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../setting/user_agent.txt"))

    with open(file_path, 'r', encoding='UTF8') as f:
        user_agents = f.readlines()
    user_agent_list = []
    for user_agent in user_agents:
        if len(user_agent.strip()) == 0:
            continue
        user_agent_list.append(user_agent.strip())

    random.shuffle(user_agent_list)
    return user_agent_list[0]


# 공통 로그 추가
def write_common_log(path: str, service: str, text: str) -> None:

    if current_os == 'MAC':
        file_path = path
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

    with open(file_path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{text}"
        f.write(f"{message}\n")


# 하루 작업량 업데이트
def write_working_log(service: str, user_id: str, cnt: int) -> None:
    current_time = datetime.now().strftime('%Y%m%d')
    if current_os == 'MAC':
        file_path = f"../log/working/working_accounts_{current_time}.txt"
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../log/working/working_accounts_{current_time}.txt"))

    # 파일 읽기 시도
    try:
        with open(file_path, 'r', encoding='UTF8') as f:
            accounts = f.readlines()
    except FileNotFoundError:
        # 파일이 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='UTF8') as f:
            f.write("")  # 빈 파일 생성
        accounts = []

    with open(file_path, 'r', encoding='UTF8') as f:
        accounts = f.readlines()
    account_list = []
    for account in accounts:
        if len(account.strip()) == 0:
            continue
        account_list.append(account.strip())

    is_dupl = False
    for i in range(len(account_list)):
        account = account_list[i]
        parts = account.split("|")
        if parts[0] == service and parts[1] == user_id:
            parts[2] = int(parts[2]) + cnt
            account_list[i] = f"{parts[0]}|{parts[1]}|{parts[2]}\n"
            is_dupl = True

    if not is_dupl:
        account_list.append(f"{service}|{user_id}|{cnt}")

    with open(file_path, "w") as f:
        for account in account_list:
            parts = account.split("|")
            f.write(f"{parts[0]}|{parts[1]}|{parts[2]}\n")


# 작업로그
# 어떤계정이 어떤링크에 작업을 했는지 로그 쌓기
# 예시로 특정 계정이 이미 팔로우등 5가지 작업이 되어잇는지 체크
def write_working_save_log(service: str, user_id: str, link: str) -> None:

    if current_os == 'MAC':
        file_path = f"../log/working_accounts_save.txt"
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../log/working_accounts_save.txt"))

    with open(file_path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{user_id}|{link}"
        f.write(f"{message}\n")


# 주문 결과 로그 추가
def write_order_log(path: str, service: str, order_id: str, quantity: int, success: int, fail: int) -> None:
    if current_os == 'MAC':
        file_path = path
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

    with open(file_path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{order_id}|{quantity}|{success}|{fail}"
        f.write(f"{message}\n")
        send_message(config['telegram']['chat_order_id'], message)


# 태스크 로그 추가
def write_task_log(path: str, service: str, order_id: str, user_id: str, result: str, err_msg: str, order_url: str) -> None:
    if current_os == 'MAC':
        file_path = path
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

    with open(file_path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f'{service}|{current_time}|{order_id}|{order_url}|{user_id}|{result}|{err_msg}'
        f.write(f"{message}\n")

    if result != 'OK':
        send_message(config['telegram']['chat_error_task'], message)


# 에러 계정 추가
def remove_from_accounts(service: str, current_user_id: str, err_msg: str, is_login = False) -> None:

    if is_login:
        if current_os == 'MAC':
            account_file_path = "../setting/account.txt"
        else:
            account_file_path = os.path.abspath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "../setting/account.txt"))

        with open(account_file_path, "r") as f:
            lines = f.readlines()

        with open(account_file_path, "w") as f:
            for line in lines:
                if line.split("|")[0] != current_user_id:
                    f.write(line)

    if current_os == 'MAC':
        file_path = "../log/error_accounts.txt"
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../log/error_accounts.txt"))

    with open(file_path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{current_user_id}|{err_msg}"
        f.write(f"{message}\n")

    send_message(config['telegram']['chat_error_account'], message)


# 에러 로그 추가
def remove_from_error(log_txt: str, device_name: str) -> None:
    if current_os == 'MAC':
        file_path = "../log/error_log.txt"
    else:
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../log/error_log.txt"))

    with open(file_path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{device_name}|{current_time}|{log_txt}\n")


# 텔레그램 메시지 보내기 1번
def send_message(chat_id: str, message: str) -> None:
    if config['log']['telegram'] == 'True':
        asyncio.run(send_alert(chat_id, message))


# 텔레그램 메시지 보내기 2번
async def send_alert(chat_id: str, message: str):
    text = f'{message}'
    bot = telegram.Bot(token=telegram_token_key)
    await bot.sendMessage(chat_id=chat_id, text=text)


# 대기
def sleep(second: int) -> None:
    time.sleep(second)


# element 찾는 공통 함수 오브젝트
def find_element(selector_type: str, selector_name: str, driver, wait) -> object:
    if not is_display(selector_type, selector_name, driver):
        sleep(1)
        if not is_display(selector_type, selector_name, driver):
            sleep(1)

    if selector_type == 'ID':
        return wait.until(EC.presence_of_element_located((By.ID, selector_name)))
    elif selector_type == 'NAME':
        return wait.until(EC.presence_of_element_located((By.NAME, selector_name)))
    elif selector_type == 'TAG_NAME':
        return wait.until(EC.presence_of_element_located((By.TAG_NAME, selector_name)))
    elif selector_type == 'CLASS_NAME':
        return wait.until(EC.presence_of_element_located((By.CLASS_NAME, selector_name)))
    elif selector_type == 'CSS_SELECTOR':
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_name)))


# element 찾는 공통 함수 배열
def find_elements(selector_type: str, selector_name: str, driver, wait) -> list:
    if not is_display(selector_type, selector_name, driver):
        sleep(1)
        if not is_display(selector_type, selector_name, driver):
            sleep(1)

    if selector_type == 'ID':
        return wait.until(EC.presence_of_all_elements_located((By.ID, selector_name)))
    elif selector_type == 'NAME':
        return wait.until(EC.presence_of_all_elements_located((By.NAME, selector_name)))
    elif selector_type == 'TAG_NAME':
        return wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, selector_name)))
    elif selector_type == 'CLASS_NAME':
        return wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, selector_name)))
    elif selector_type == 'CSS_SELECTOR':
        return wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector_name)))


# element 찾는 공통 함수 오브젝트
def find_children_element(selector_type: str, selector_name: str, driver, element) -> object:
    if not is_display(selector_type, selector_name, driver):
        sleep(1)
        if not is_display(selector_type, selector_name, driver):
            sleep(1)

    if selector_type == 'ID':
        return element.find_element(By.Id, selector_name)
    elif selector_type == 'NAME':
        return element.find_element(By.NAME, selector_name)
    elif selector_type == 'TAG_NAME':
        return element.find_element(By.TAG_NAME, selector_name)
    elif selector_type == 'CLASS_NAME':
        return element.find_element(By.CLASS_NAME, selector_name)
    elif selector_type == 'CSS_SELECTOR':
        return element.find_element(By.CSS_SELECTOR, selector_name)


# element 찾는 공통 함수 오브젝트
def find_children_elements(element, selector_type: str, selector_name: str, driver) -> object:
    if not is_display(selector_type, selector_name, driver):
        sleep(1)
        if not is_display(selector_type, selector_name, driver):
            sleep(1)

    if selector_type == 'ID':
        return element.find_elements(By.Id, selector_name)
    elif selector_type == 'NAME':
        return element.find_elements(By.NAME, selector_name)
    elif selector_type == 'TAG_NAME':
        return element.find_elements(By.TAG_NAME, selector_name)
    elif selector_type == 'CLASS_NAME':
        return element.find_elements(By.CLASS_NAME, selector_name)
    elif selector_type == 'CSS_SELECTOR':
        return element.find_elements(By.CSS_SELECTOR, selector_name)


# 디스 플레이 체크 여부
def is_display(selector_type: str, selector_name: str, driver) -> bool:
    is_displayed = False
    if selector_type == 'ID':
        count = len(driver.find_elements(By.ID, selector_name))
    elif selector_type == 'NAME':
        count = len(driver.find_elements(By.NAME, selector_name))
    elif selector_type == 'TAG_NAME':
        count = len(driver.find_elements(By.TAG_NAME, selector_name))
    elif selector_type == 'CLASS_NAME':
        count = len(driver.find_elements(By.CLASS_NAME, selector_name))
    elif selector_type == 'CSS_SELECTOR':
        count = len(driver.find_elements(By.CSS_SELECTOR, selector_name))

    if count > 0:
        is_displayed = True
    return is_displayed


# 배열에서 특정 엘리먼트 찾기
def search_elements(selector_type: str, search_list: list, search_text: str, attr_name="") -> list:
    result = []
    for search_item in search_list:
        if selector_type == 'TEXT':
            if search_item.text == search_text:
                result.append(search_item)
        elif selector_type == 'ATTR':
            if search_item.get_attribute(attr_name) == search_text:
                result.append(search_item)

    return result


# 배열에서 특정 엘리먼트 찾기
def search_element(selector_type: str, search_list: list, search_text: str, attr_name="") -> object:
    for search_item in search_list:
        if selector_type == 'TEXT':
            if search_item.text == search_text:
                return search_item
        elif selector_type == 'ATTR':
            if search_item.get_attribute(attr_name) == search_text:
                return search_item

    return None


# 현재 시간을 format해 반환하는 함수
def get_current_time() -> str:
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')


# 커스텀 로그
def log(text: str, user_id='-', tab_index='-') -> None:
    if config['log']['show'] == 'True':
        print(f'[{tab_index}][{user_id}] {text}')


# 주문의 남은 수량 변경
def set_remains(order_id: str, remains: int) -> None:
    try:
        prev_remains = get_remains(order_id)
    except Exception as ex:
        raise Exception(ex)
    try:
        res = requests.post(config['api']['url'], data={
            'key': config['api']['key'],
            'action': 'setRemains',
            'id': order_id,
            'remains': prev_remains - remains
        }, timeout=10)
    except Exception as ex:
        raise Exception('퍼팩트 패널 남은개수 수정 에러')


# 주문의 남은 수량 가져오기
def get_remains(order_id: str) -> int:
    try:
        res = requests.get(f"{config['api_v2']['url']}/{order_id}?apikey={config['api_v2']['key']}", timeout=10).json()
        return int(res['data']['remains'])
    except Exception as ex:
        raise Exception('퍼팩트 패널  남은개수 가져오기 에러')


# 주문의 남은 수량 변경
def status_change(order_id: str, action: str) -> None:
    try:
        res = requests.post(config['api']['url'], data={
            'key': config['api']['key'],
            'action': action,
            'id': order_id,
        }, timeout=10)
    except Exception as ex:
        raise Exception('퍼팩트 패널 상태 변경 수정 에러')


# 최종 결과 API 연동
def result_api(order_id: str, total_success: int, total_fail: int, quantity: int, order_log_path: str, order_service: str) -> None:

    if total_success == quantity:  # 전체 성공
        res = requests.post(config['api']['url'], data={
            'key': config['api']['key'],
            'action': 'setCompleted',
            'id': order_id
        }, timeout=10)
        log("[Success] -  작업 완료")
    else:  # 부분 성공
        res = requests.post(config['api']['url'], data={
            'key': config['api']['key'],
            'action': 'setPartial',
            'id': order_id,
            'remains': quantity - total_success
        }, timeout=10)
        log("[Success] -  작업 부분 완료")

    log(f"[Success] -  주문 번호 : {order_id}")
    log(f"[Success] -  주문 수량 : {quantity}")
    log(f"[Success] -  남은 수량 : {quantity - total_success}")
    log(f"[Success] -  상태 변경 결과 : {res}")
    log(f"총 성공: {total_success}, 총 실패: {total_fail}")

    # 주문 최종 결과 로그 저장
    write_order_log(order_log_path, order_service, order_id, quantity, total_success, total_fail)


# 엘리먼트 정보 콘솔출력
def element_log(element) -> None:
    # 태그 이름
    print(f"Tag Name: {element.tag_name}")

    # 텍스트 내용
    print(f"Text: {element.text}")

    # aria-label 속성 값
    aria_label_attr = element.get_attribute('aria-label')
    if element.get_attribute('aria-label'):
        print(f"aria-label: {aria_label_attr}")
    else:
        print("aria-label: None")

    # outerHTML 속성 값
    outerHTML_attr = element.get_attribute('outerHTML')
    if element.get_attribute('outerHTML'):
        print(f"outerHTML: {outerHTML_attr}")
    else:
        print("outerHTML: None")

    # innerHTML 속성 값
    innerHTML_attr = element.get_attribute('innerHTML')
    if element.get_attribute('innerHTML'):
        print(f"innerHTML: {innerHTML_attr}")
    else:
        print("innerHTML: None")

    # title 속성 값
    title_attr = element.get_attribute('title')
    if element.get_attribute('title'):
        print(f"title: {title_attr}")
    else:
        print("title: None")

    # style 속성 값
    style_attr = element.get_attribute('style')
    if element.get_attribute('style'):
        print(f"style: {style_attr}")
    else:
        print("style: None")

    # value 속성 값
    value_attr = element.get_attribute('value')
    if element.get_attribute('value'):
        print(f"value: {value_attr}")
    else:
        print("value: None")

    # src 속성 값
    src_attr = element.get_attribute('src')
    if element.get_attribute('src'):
        print(f"src: {src_attr}")
    else:
        print("src: None")

    # id 속성 값
    id_attr = element.get_attribute('id')
    if id_attr:
        print(f"id: {id_attr}")
    else:
        print("id: None")

    # class 속성 값
    class_attr = element.get_attribute('class')
    if class_attr:
        print(f"class: {class_attr}")
    else:
        print("class: None")

    # 부모 요소
    parent = element.find_element(By.XPATH, "..")
    print(f"parent Tag: {parent.tag_name}")

    # 행 구분
    print("-" * 20)


# 셀레니움 연결
def open_selenium(curt_os: str, wait_time: int, ip: str, session_id: str) -> object:
    log('셀레니움 연결', session_id)
    if curt_os == 'MAC':
        driver_path = config['selenium']['driver_path_mac']
        chrome_path = config['selenium']['chrome_path_mac']
    else:
        driver_path = config['selenium']['driver_path_window']
        chrome_path = config['selenium']['chrome_path_window']
    # Chrome 웹 드라이버 경로 설정
    chromedriver_path = driver_path

    # Chrome 웹 드라이버 설정
    options = webdriver.ChromeOptions()

    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=450x975')
    options.add_argument(f'--user-agent={get_user_agent()}')

    if current_os == 'MAC':
        options.add_argument(f'--user-data-dir=/Users/ohhyesung/Library/Application Support/Google/Chrome/Default/instahelp_{session_id}')

    # options.add_argument(f'--profile-directory=instahelp_{session_id}')  # 프로필 디렉토리 지정
    # options.add_argument("--lang=ko_KR")
    # options.add_argument('--headless')

    # 프록시 설정은 윈도우에서만 가능
    if current_os == 'WINDOW':
        options.add_argument(f'--proxy-server={ip}')

    options.binary_location = chrome_path

    # 웹 드라 이버 시작
    screen_width, _ = pyautogui.size()
    width = 480
    margin = 50
    service = ChromeService(executable_path=chromedriver_path)
    selenium_driver = webdriver.Chrome(service=service, options=options)
    selenium_driver.implicitly_wait(wait_time)
    selenium_driver.set_window_size(width, 960)
    selenium_driver.set_window_position(screen_width + (width + margin) * (1 - 1), 0)
    return selenium_driver


# 화면에 동의요청 화면이 나왔는지 체크
def agree_check(user_id, tab_index, driver) -> bool:
    log('동의여부 체크 시작', user_id, tab_index)
    is_agree = is_display("CSS_SELECTOR", ".wbloks_1>.wbloks_1>.wbloks_1>.wbloks_1>.wbloks_1.wbloks_1>span",
                          driver)
    log(f'동의여부 체크 종료 : {"동의 되어있지 않음" if is_agree else "동의 되어있음"}', user_id, tab_index)
    return is_agree


# 동의 하기
def agree_active(user_id, tab_index, driver, wait) -> tuple:
    try:
        log('동의하기 클릭 시작', user_id, tab_index)
        agree_elements = find_elements("TAG_NAME", "input", driver, wait)
        filter_agree_elements = search_elements("ATTR", agree_elements, "checkbox", "type")
        for agree in filter_agree_elements:
            click(agree)

        agrees = find_elements("CLASS_NAME", "wbloks_1", driver, wait)
        for agree in agrees:
            if agree.get_attribute("aria-label") == '동의함':
                click(agree)

                agrees_close = find_elements("CLASS_NAME", "wbloks_1", driver, wait)
                for agree_close in agrees_close:
                    if agree_close.get_attribute("aria-label") == '닫기':
                        click(agree_close)
                        log('동의하기 클릭 종료', user_id, tab_index)
                        return True, ''
        log('동의하기 클릭 종료', user_id, tab_index)
        return False, ''
    except Exception as ex:
        raise Exception(ex)
        return False, ''


# 로그인
def login(account_id: str, account_pw: str, tab_index, driver, wait) -> bool:
    try:
        # 로그인
        log('로그인 시작', account_id, tab_index)

        # 로그인 버튼 클릭
        find_btns = find_elements("CSS_SELECTOR", "button.x5yr21d", driver, wait)
        login_btn = None
        for find_btn in find_btns:
            if find_btn.text == 'Log in' or find_btn.text == '로그인':
                login_btn = find_btn

        if login_btn:
            click(login_btn)
        else:
            return False

        # 계정을 입력합니다.
        id_input = find_element('NAME', "username", driver, wait)
        click(id_input)
        id_input.send_keys(account_id)

        # 비밀번호를 입력합니다.
        pw_input = find_element('NAME', "password", driver, wait)
        click(pw_input)
        pw_input.send_keys(account_pw)

        # 로그인 버튼을 클릭(탭)합니다.
        login_btns = find_elements('TAG_NAME', "button", driver, wait)

        login_btn = search_element('ATTR', login_btns, 'submit', "type")
        click(login_btn)
        log('로그인 종료', account_id, tab_index)
        sleep(5)

        spans = find_elements("TAG_NAME", "span", driver, wait)
        for span in spans:
            if span.text == '비밀번호 오류':
                return False

        log('로그인 정보 저장 시작', account_id, tab_index)
        is_login = False
        account_save_btns = find_elements("TAG_NAME", "button", driver, wait)
        for account_save_btn in account_save_btns:
            if account_save_btn.text == '정보 저장':
                is_login = True
        log('로그인 정보 저장 종료', account_id, tab_index)
        log(f'로그인 성공여부 {is_login}', account_id, tab_index)
        return is_login
    except Exception as ex:
        return False


# 랜덤시간 추출
def random_delay() -> int:
    return random.choice([1, 2])


# 클릭 이벤트
def click(element):
    sleep(random_delay())
    element.click()


# 브라우저 + 계정 셋팅
def account_setting(accounts, quantity) -> list:
    if len(accounts) > quantity:
        temp_active_accounts = accounts[:quantity]
    else:
        temp_active_accounts = accounts

    active_accounts = []
    for i in range(0, len(temp_active_accounts), browser_cnt):
        active_accounts.append(temp_active_accounts[i:i + browser_cnt])
    return active_accounts


# 중복주문 체크
def dupl_check(service: int, order_service: str, order_log_path: str) -> bool:
    # 신규주문건을 전체조회한다.(대기중인것만) 최신순이니 마지막 요소(제일 오래된)를 찾는다
    res_new = requests.get(
        f"{config['api_v2']['url']}?apikey={config['api_v2']['key']}&service_ids={service}&order_status=pending",
        timeout=10).json()

    current_order = None
    if res_new['data']:
        new_orders = res_new['data']['list']
        if len(new_orders) > 0:
            current_order = new_orders[len(new_orders)-1]

    # 요소가 있다면
    # 전체조회를 해서 *중복링크 + 대기중, 진행중, 처리중 인경우 주문 막기
    if current_order:
        res_dupl = requests.get(
            f"{config['api_v2']['url']}?apikey={config['api_v2']['key']}&service_ids={service}",
            timeout=10).json()
        # 결과가 성공이 아니면
        if res_dupl['data']:
            orders = res_dupl['data']['list']
            for order in orders:
                if current_order['id'] == order['id']:
                    continue

                link = order['link']
                order_url = current_order['link']

                created = order['created'][:10]
                current_order_created = current_order['created'][:10]

                if service == config['api']['follow_service']:
                    if 'instagram.com' not in link:
                        link = f'https://www.instagram.com/{link}'

                    if 'instagram.com' not in order_url:
                        order_url = f'https://www.instagram.com/{order_url}'
                if (
                        order['status'] == 'pending'
                        # TODO : 개발편의상 대기중 상태만 체크하도록 넣어둠 고객사 요청사항은 대기중, 처리중, 진행중 까지였음
                        # or order['status'] == 'in_progress' or order[
                        #     'status'] == 'processing'
                    ) and link.strip() == order_url.strip() \
                    and created == current_order_created:
                    write_common_log("../log/dupl_history.txt", order_service,
                                     f"{order['id']}|{current_order['id']}|{order_url}|{get_status_text(order['status'])}")

                    write_order_log(order_log_path, order_service, current_order['id'], current_order['quantity'], 0, 0)
                    return True

    return False


# pending 대기중
# processing 처리중
# in_progress 진행중
# completed 완료
# partial 부분완료
# canceled 취소
# error 오류
# fail 실패
# 주문상태 한글명으로 변경
def get_status_text(status: str) -> str:
    if status == 'pending':
        return '대기중'
    elif status == 'in_progress':
        return '진행중'
    elif status == 'processing':
        return '처리중'
    elif status == 'completed':
        return '완료'
    elif status == 'partial':
        return '부분완료'
    elif status == 'canceled':
        return '취소'
    elif status == 'error':
        return '오류'
    elif status == 'fail':
        return '실패'
    else:
        return '없음'


def set_filter_accounts(order_service: str, order_url: str, accounts: list) -> list:
    # 할당량을 다 한 계정 추출
    not_accounts = get_accounts_max_working(order_service)

    # 할당량을 다 한 계정 제거
    filter_accounts = [account for account in accounts if account.split('|')[0] not in not_accounts]

    # 이미 작업을 한 계정 제거
    filter_accounts = [account for account in filter_accounts if
                       len(get_used_working_accounts(order_service, account.split('|')[0], order_url)) == 0]
    return filter_accounts