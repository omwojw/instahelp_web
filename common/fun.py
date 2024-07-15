import time
from datetime import datetime
import configparser
import os
import sys
import asyncio
import telegram
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import requests
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import traceback
import psutil
import cv2
import threading
import numpy as np
from PIL import Image
import io
import logging
from fake_useragent import UserAgent
from selenium.webdriver.chrome.webdriver import WebDriver
from datetime import timedelta
from typing import List
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from typing import Optional
import re
import math
ua = UserAgent()
user_agent = ua.random


config = configparser.ConfigParser()
current_os = None
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'setting', 'config.ini'), encoding='utf-8')
if sys.platform.startswith('win'):
    current_os = 'WINDOW'
    import pyautogui
elif sys.platform == 'darwin':
    current_os = 'MAC'
    import pyautogui
elif sys.platform == 'linux':
    current_os = 'LINUX'

max_docker_cnt = int(config['selenium']['max_docker_cnt'])
max_order_cnt = int(config['selenium']['max_order_cnt'])
is_headless = bool(config['selenium']['headless'] == 'True')
telegram_token_key = config['telegram']['token_key']

browser_cnt = 0
video_out: Optional[cv2.VideoWriter] = None
video_start_time = 0
recording = True
record_thread: Optional[threading.Thread] = None
screen_size = (480, 960)
# logger: Optional[logging] = None
logger = logging.getLogger(__name__)


# config 셋팅
def get_config(new_confit: configparser.ConfigParser) -> None:
    new_confit.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'setting', 'config.ini'),
                    encoding='utf-8')


# 실행 OS 정보
def get_os() -> str:
    if sys.platform.startswith('win'):
        return 'WINDOW'
    elif sys.platform == 'darwin':
        return 'MAC'
    elif sys.platform == 'linux':
        return 'LINUX'


# 계정 정보 목록
def get_accounts(path: str) -> list:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../setting/{path}"))

    with open(file_path, 'r', encoding='UTF-8') as f:
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
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../log/working/working_accounts_{current_time}.txt'))

    # 파일 읽기 시도
    try:
        with open(file_path, 'r', encoding='UTF-8') as f:
            accounts = f.readlines()
    except FileNotFoundError:
        # 파일이 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='UTF-8') as f:
            f.write("")  # 빈 파일 생성
        accounts = []

    with open(file_path, 'r', encoding='UTF-8') as f:
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

    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../log/working/working_accounts_{current_time}.txt'))

    # 파일 읽기 시도
    try:
        with open(file_path, 'r', encoding='UTF-8') as f:
            accounts = f.readlines()
    except FileNotFoundError:
        # 파일이 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='UTF-8') as f:
            f.write("")  # 빈 파일 생성
        accounts = []

    with open(file_path, 'r', encoding='UTF-8') as f:
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
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../log/working_accounts_save.txt'))

    with open(file_path, 'r', encoding='UTF-8') as f:
        accounts = f.readlines()
    account_list = []
    for account in accounts:
        if len(account.strip()) == 0:
            continue

        pats = account.split("|")
        pats_service = pats[0]
        pats_user_id = pats[3]
        pats_link = pats[4]

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
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../setting/comment_random.txt"))

    with open(file_path, 'r', encoding='UTF-8') as f:
        comments = f.readlines()
    comment_list = []
    for comment in comments:
        if len(comment.strip()) == 0:
            continue
        comment_list.append(comment.strip())

    random.shuffle(comment_list)
    return comment_list


# user agent 목록
def get_user_agent() -> object:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../setting/user_agent.txt"))

    with open(file_path, 'r', encoding='UTF-8') as f:
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
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

    with open(file_path, "a", encoding='UTF-8') as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{text}"
        f.write(f"{message}\n")


# 하루 작업량 업데이트
def write_working_log(service: str, user_id: str, cnt: int) -> None:
    current_time = datetime.now().strftime('%Y%m%d')
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../log/working/working_accounts_{current_time}.txt"))

    # 파일 읽기 시도
    try:
        with open(file_path, 'r', encoding='UTF-8') as f:
            accounts = f.readlines()
    except FileNotFoundError:
        # 파일이 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='UTF-8') as f:
            f.write("")  # 빈 파일 생성
        accounts = []

    with open(file_path, 'r', encoding='UTF-8') as f:
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
            account_list[i] = f"{parts[0]}|{parts[1]}|{int(parts[2]) + cnt}"
            is_dupl = True

    if not is_dupl:
        account_list.append(f"{service}|{user_id}|{cnt}")

    with open(file_path, "w", encoding='UTF-8') as f:
        for account in account_list:
            parts = account.split("|")
            f.write(f"{parts[0]}|{parts[1]}|{parts[2]}\n")


# 작업로그
# 어떤계정이 어떤링크에 작업을 했는지 로그 쌓기
# 예시로 특정 계정이 이미 팔로우등 5가지 작업이 되어잇는지 체크
def write_working_save_log(service: str, order_id: str, user_id: str, link: str) -> None:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../log/working_accounts_save.txt"))

    with open(file_path, "a", encoding='UTF-8') as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{order_id}|{user_id}|{link}"
        f.write(f"{message}\n")


# 주문 결과 로그 추가
def write_order_log(path: str, service: str, order_id: str, quantity: int, success: int, fail: int, order_time: str) -> None:
    log(f"총 성공: [{success}], 총 실패: [{fail}]")
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

    with open(file_path, "a", encoding='UTF-8') as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}|{current_time}|{order_id}|{quantity}|{success}|{fail}|{order_time}"
        f.write(f"{message}\n")
        send_message(config['telegram']['chat_order_id'], message)


# 태스크 로그 추가
def write_task_log(path: str, service: str, order_id: str, user_id: str, result: bool, err_msg: str, order_url: str) -> None:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

    with open(file_path, "a", encoding='UTF-8') as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f'{service}|{current_time}|{order_id}|{order_url}|{user_id}|{result}|{err_msg}'
        f.write(f"{message}\n")

    # if not result:
    #     send_message(config['telegram']['chat_error_task'], message)


# 에러 계정 추가
def remove_from_accounts(service: str, order_id: str, current_user_id: str, err_msg: str, is_login=False) -> None:
    if config['log']['error_accounts_copy'] == 'True':
        if is_login:
            account_file_path = os.path.abspath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "../setting/account.txt"))

            with open(account_file_path, "r", encoding='UTF-8') as f:
                lines = f.readlines()

            with open(account_file_path, "w", encoding='UTF-8') as f:
                for line in lines:
                    if line.split("|")[0] != current_user_id:
                        f.write(line)

        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../log/error_accounts.txt"))

        with open(file_path, "a", encoding='UTF-8') as f:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"{service}|{current_time}|{order_id}|{current_user_id}|{err_msg}"
            f.write(f"{message}\n")

        # send_message(config['telegram']['chat_error_account'], message)


# 에러 로그 추가
def remove_from_error(log_txt: str, order_id: str, docker_name: str) -> None:
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../log/error/{order_id}/{docker_name}_error_log.txt"))
    make_dir(file_path)
    with open(file_path, "a", encoding='UTF-8') as f:
        f.write(f"{log_txt}")


# 텔레그램 메시지 보내기 1번
def send_message(chat_id: str, message: str) -> None:
    if config['log']['telegram'] == 'True':
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(send_alert(chat_id, message))


# 텔레그램 메시지 보내기 2번
async def send_alert(chat_id: str, message: str) -> None:
    text = f'{message}'
    bot = telegram.Bot(token=telegram_token_key)
    await bot.sendMessage(chat_id=chat_id, text=text)


# element 찾는 공통 함수 오브젝트
def find_element(selector_type: str, selector_name: str, driver: WebDriver, wait: WebDriverWait) -> WebElement:
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
def find_elements(selector_type: str, selector_name: str, driver: WebDriver, wait: WebDriverWait) -> List[WebElement]:
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
def find_children_element(selector_type: str, selector_name: str, driver: WebDriver, element: WebElement) -> WebElement:
    if not is_display(selector_type, selector_name, driver):
        sleep(1)
        if not is_display(selector_type, selector_name, driver):
            sleep(1)

    if selector_type == 'ID':
        return element.find_element(By.ID, selector_name)
    elif selector_type == 'NAME':
        return element.find_element(By.NAME, selector_name)
    elif selector_type == 'TAG_NAME':
        return element.find_element(By.TAG_NAME, selector_name)
    elif selector_type == 'CLASS_NAME':
        return element.find_element(By.CLASS_NAME, selector_name)
    elif selector_type == 'CSS_SELECTOR':
        return element.find_element(By.CSS_SELECTOR, selector_name)


# element 찾는 공통 함수 오브젝트
def find_children_elements(element: WebElement, selector_type: str, selector_name: str, driver) -> List[WebElement]:
    if not is_display(selector_type, selector_name, driver):
        sleep(1)
        if not is_display(selector_type, selector_name, driver):
            sleep(1)

    if selector_type == 'ID':
        return element.find_elements(By.ID, selector_name)
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
    count = 0
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
def search_elements(selector_type: str, search_list: list, search_text: str, attr_name="") -> List[WebElement]:
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
def search_element(selector_type: str, search_list: list, search_text: str, attr_name="") -> Optional[WebElement]:
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
def log(text: str, user_id='-', tab_index=0) -> None:
    if tab_index == 0:
        tab_index_text = '-'
    else:
        tab_index_text = str(tab_index)

    if config['log']['show'] == 'True':
        print(f'[{tab_index_text}][{user_id}] {text}')

        global logger
        if logger:
            logger.debug(f'[{tab_index_text}][{user_id}] {text}')


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
def result_api(order_id: str, total_success: int, total_fail: int, quantity: int) -> None:

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
    log(f"총 성공: [{total_success}], 총 실패: [{total_fail}]")




# 엘리먼트 정보 콘솔출력
def element_log(element: WebElement) -> None:
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
def open_selenium(curt_os: str, wait_time: int, ip: str, session_id: str, idx: int) -> object:
    log('셀레니움 연결', session_id, idx)
    driver_path = ''
    chrome_path = ''
    if curt_os == 'MAC':
        driver_path = config['selenium']['driver_path_mac']
        chrome_path = config['selenium']['chrome_path_mac']
    elif curt_os == 'WINDOW':
        driver_path = config['selenium']['driver_path_window']
        chrome_path = config['selenium']['chrome_path_window']
    elif curt_os == 'LINUX':
        driver_path = config['selenium']['driver_path_linux']
        chrome_path = config['selenium']['chrome_path_linux']

    # Chrome 웹 드라이버 경로 설정
    chromedriver_path = driver_path

    # Chrome 웹 드라이버 설정
    options = webdriver.ChromeOptions()

    # 셀레니움 로그레벨
    options.add_argument("--log-level=3")  # INFO, WARNING, LOG, ERROR

    # 셀레니움 헤더 에이전트 랜덤
    # options.add_argument(f'--user-agent={get_user_agent()}')
    options.add_argument(f'--user-agent={user_agent}')


    # 크롬 확장프로그램 비활성화
    # 확장 프로그램이 성능을 저하시키거나 불필요한 리소스를 사용할 수 있으므로 이를 비활성화하여 성능을 최적화합니다.
    options.add_argument("--disable-extensions")

    # GPU 하드웨어 가속을 비활성화
    # GPU 가속이 필요 없는 경우 이를 비활성화하여 리소스를 절약합니다. 특히 헤드리스 모드에서는 유용합니다.
    options.add_argument("--disable-gpu")

    # 샌드박스 모드를 비활성화
    # 샌드박스 모드를 비활성화하면 성능이 향상될 수 있지만, 보안상의 이유로 사용에 주의가 필요합니다.
    options.add_argument("--no-sandbox")

    # 공유메모리를 사용하지 않도록 설정
    # 공유 메모리 크기가 작은 환경에서는 이를 비활성화하여 크롬이 디스크를 대신 사용하도록 합니다. Docker 같은 환경에서 유용합니다.
    options.add_argument("--disable-dev-shm-usage")

    # 브라우저측 네비게이션 비활성화
    # 이 옵션은 특정 상황에서 성능을 최적화할 수 있습니다.
    options.add_argument("--disable-browser-side-navigation")

    # 자동화된 브라우저 환경을 위해 설정합니다.
    # 크롬이 자동화된 환경에서 실행되고 있음을 나타내어 특정 최적화 및 기능을 활성화합니다.
    options.add_argument("enable-automation")

    # "Chrome is being controlled by automated test software" 메시지 바를 비활성화합니다.
    # 사용자 경험을 방해하지 않도록 메시지 바를 숨깁니다.
    options.add_argument("--disable-infobars")

    # AutomationControlled 기능을 비활성화합니다.
    # 사이트가 브라우저 자동화를 감지하지 못하게 합니다.
    options.add_argument("--disable-blink-features=AutomationControlled")

    # 원격 디버깅 포트를 설정합니다.
    # 디버깅 및 성능 최적화를 위해 사용될 수 있습니다. 여러 인스턴스 실행 시 겹치지 않는 포트를 설정해야 합니다.
    # chrome_options.add_argument("--remote-debugging-port=9222")

    # 사이트 격리 기능을 비활성화합니다.
    # 성능 향상을 위해 사이트 간 격리를 비활성화합니다. 보안 기능을 일부 희생할 수 있습니다.
    options.add_argument("--disable-site-isolation-trials")

    # 네트워크 서비스 기능을 비활성화합니다.
    # 네트워크 서비스 관련 기능이 성능을 저하시키는 경우 이를 비활성화하여 성능을 최적화할 수 있습니다.
    options.add_argument("--disable-features=NetworkService")

    # Viz Display Compositor 기능을 비활성화합니다.
    # 렌더링 관련 성능 문제를 해결하기 위해 사용합니다. 특정 환경에서 성능 향상이 있을 수 있습니다.
    options.add_argument("--disable-features=VizDisplayCompositor")

    # 세션
    if current_os == 'MAC':
        options.add_argument(
            f'--user-data-dir=/Users/ohhyesung/Library/Application Support/Google/Chrome/Default/instahelp_{session_id}')
    elif current_os == 'WINDOW':
        options.add_argument(
            f'--user-data-dir=C:/workspace/instahelp_session/instahelp_{session_id}')
        options.add_argument(f'--profile-directory=Default')  # 프로필 디렉토리 지정
    elif current_os == 'LINUX':
        options.add_argument(
            f'--user-data-dir=/instahelp_session/instahelp_{session_id}')

    # 헤드리스 모드
    if is_headless:
        options.add_argument('--headless')

        # 헤드리스 모드일때 한국어로
        options.add_argument('--lang=ko')

    # 프록시 설정은 윈도우에서만 가능
    if current_os == 'WINDOW':
        options.add_argument(f'--proxy-server={ip}')
    # elif current_os == 'LINUX':
    #     options.add_argument(f'--proxy-server={ip}')

    options.binary_location = chrome_path

    # 웹 드라 이버 시작
    global screen_size
    width = screen_size[0]
    margin = 50

    service = ChromeService(executable_path=chromedriver_path)
    selenium_driver = webdriver.Chrome(service=service, options=options)
    selenium_driver.implicitly_wait(wait_time)
    selenium_driver.set_window_size(width, screen_size[1])
    if current_os == 'MAC':
        screen_width, screen_height = pyautogui.size()
        selenium_driver.set_window_position(screen_width + (width + margin) * (1 - 1), 0)
    elif current_os == 'WINDOW':
        screen_width, screen_height = pyautogui.size()
        # if idx > 3:
        #     selenium_driver.set_window_position(screen_width + (width + margin) * (idx%3 - 1), 200)
        # else:
        #     selenium_driver.set_window_position(screen_width + (width + margin) * (idx - 1), 200)

        selenium_driver.set_window_position(0, 0)
        # selenium_driver.set_window_position(1820-(width+margin), screen_height+margin)
    elif current_os == 'LINUX':
        selenium_driver.set_window_position(0, 0)
    return selenium_driver


# 화면에 동의요청 화면이 나왔는지 체크
def agree_check(user_id: str, tab_index: int, driver: WebDriver, wait: WebDriverWait) -> bool:
    log('동의여부 체크 시작', user_id, tab_index)
    agrees = find_elements("TAG_NAME", "span", driver, wait)
    is_agree = False
    for agree in agrees:
        if agree.text == 'Instagram 앱을 사용하려면 다음 항목에 동의해야 합니다':
            is_agree = True
    log(f'동의여부 체크 종료 : {"동의 필요함" if is_agree else "동의 필요하지 않음"}', user_id, tab_index)
    return is_agree


# 동의 하기
def agree_active(user_id: str, tab_index: int, driver: WebDriver, wait: WebDriverWait) -> tuple:
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
                        log('동의하기 클릭 종료 - 성공', user_id, tab_index)
                        return True, '성공'
        log('동의하기 클릭 종료 - 에러', user_id, tab_index)
        return False, '동의하기 에러'
    except Exception as ex:
        raise Exception(ex)


# 로그인
def login(account_id: str, account_pw: str, tab_index: int, driver: WebDriver, wait: WebDriverWait) -> tuple:

    try:
        # 로그인
        log('로그인 시작', account_id, tab_index)

        login_url = 'https://www.instagram.com/accounts/login/'
        move_page(driver, login_url)
        sleep(3)
        if login_url != driver.current_url:
            return False, '로그인 페이지를 벗어남'


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

        try:
            spans = find_elements("TAG_NAME", "span", driver, wait)
            for span in spans:
                if span.text == '비밀번호 오류':
                    return False, '비밀번호 오류'

            divs = find_elements("TAG_NAME", "div", driver, wait)
            for div in divs:
                if div.text == '잘못된 비밀번호입니다. 다시 확인하세요.':
                    return False, '비밀번호 오류'
        except Exception as e:
            sleep(1)

        log('로그인 검증 시작', account_id, tab_index)
        home_url = "https://www.instagram.com/"
        move_page(driver, home_url)
        sleep(3)

        is_login1 = False
        is_login2 = False
        message = ''


        # 로그인 성공
        if home_url == driver.current_url:
            is_login1 = True

            buttons = find_elements("TAG_NAME", "button", driver, wait)
            for button in buttons:
                if button.text == '로그인':
                    is_login1 = False
                    message = '신규 로그인 실패'
                    break

            if is_login1:
                # 검증이 성공했다고 해도 동의하기가 나올수도 있음
                if agree_check(account_id, tab_index, driver, wait):
                    sleep(1)
                    is_agree, agree_message = agree_active(account_id, tab_index, driver, wait)

                    if not is_agree:
                        is_login1 = False
                        message = '동의하기 에러'
                    sleep(1)

        # 로그인 실패
        else:

            # 계정 정지
            if 'accounts/suspended' in driver.current_url:
                message = '계정정지'

            # 메타 정보동의
            elif '/consent/' in driver.current_url:
                message = '광고설정'

                divs = find_elements("TAG_NAME", "div", driver, wait)
                for div in divs:
                    if div.text == '시작하기':
                        click(div)
                        sleep(1)

                        spans = find_elements("TAG_NAME", "span", driver, wait)
                        for span in spans:
                            if span.text == '무료 사용':
                                click(span)
                                sleep(1)

                                span_agrees = find_elements("TAG_NAME", "span", driver, wait)
                                for span_agree in span_agrees:
                                    if span_agree.text == '동의':
                                        click(span_agree)
                                        sleep(1)
                                        is_login1 = True
                                        message = ''
                                        break

            # 인증 후 살리기
            elif 'challenge/action' in driver.current_url:
                message = '인증필요'
                # TODO 이메일 이증

            # 계정 봇 의심 경고 경우
            elif 'challenge' in driver.current_url:
                message = '의심경고'
                divs = find_elements("TAG_NAME", "div", driver, wait)
                for div in divs:
                    if div.get_attribute("aria-label") == '닫기' or div.get_attribute('aria-label') == 'Dismiss':
                        click(div)
                        sleep(3)
                        is_login1 = True
                        message = ''
                        break
            else:
                message = '원인불명'

        sleep(3)
        # 로그인 2차 검증
        if is_login1:
            if is_display("TAG_NAME", "svg", driver):
                svgs = find_elements("TAG_NAME", "svg", driver, wait)
                for svg in svgs:
                    if svg.get_attribute("aria-label") == '홈' or svg.get_attribute("aria-label") == 'Home':
                        is_login2 = True
                        message = ''
                        break

            if not is_login2:
                message = '로그인(2차) 검증 에러'
        is_login = is_login1 and is_login2

        log('로그인 검증 종료', account_id, tab_index)
        log(f'로그인 성공여부 {is_login1} - {is_login2}', account_id, tab_index)
        return is_login, message
    except Exception as ex:
        log(traceback.format_exc(), account_id, tab_index)
        return False, '로그인 실패'


# 랜덤시간 추출
def random_delay() -> int:
    return random.choice([1, 2])


# 클릭 이벤트
def click(element: WebElement):
    sleep(random_delay())
    element.click()


# 브라우저 + 계정 셋팅
def account_setting(accounts: list, quantity: int) -> list:
    global browser_cnt
    if browser_cnt == 0:
        browser_cnt = 300
    if len(accounts) > quantity:
        temp_active_accounts = accounts[:quantity]
    else:
        temp_active_accounts = accounts

    active_accounts = []
    for i in range(0, len(temp_active_accounts), browser_cnt):
        active_accounts.append(temp_active_accounts[i:i + browser_cnt])
    return active_accounts


def account_docker_setting(accounts: list, quantity: int) -> tuple:
    if len(accounts) > quantity:
        temp_active_accounts = accounts[:quantity]
    else:
        temp_active_accounts = accounts

    global browser_cnt, max_docker_cnt
    if max_docker_cnt > quantity:
        max_docker_cnt = quantity
        browser_cnt = 1
    else:
        browser_cnt = math.ceil(len(temp_active_accounts)/max_docker_cnt)

    active_accounts = [[] for _ in range(max_docker_cnt)]

    for i, account in enumerate(temp_active_accounts):
        active_accounts[i % max_docker_cnt].append(account)

    # 빈 배열 제거
    active_accounts = [acc for acc in active_accounts if acc]

    return browser_cnt, active_accounts


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

                    write_order_log(order_log_path, order_service, current_order['id'], current_order['quantity'], 0, 0, '-')
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


# 대기
def sleep(second: int, second_range=1) -> None:
    if config['selenium']['is_sleep'] == 'True':
        times = random_delay_range(second, second_range)
        time.sleep(times)


# 랜덤시간 추출
def random_delay_range(second: int, second_range: int) -> int:
    return random.choice(get_surrounding_numbers(second, second_range))


# 랜덤 숫자 배열만들기
def get_surrounding_numbers(base_number, delta) -> List[int]:
    return [base_number + i for i in range(delta + 1)]


# 작업 가능한 계정이 없는경우 취소처리
def not_working_accounts(order_log_path: str, order_service: str, order_id: str, quantity: int) -> None:
    log('가용 가능한 계정이 존재하지 않습니다.')
    status_change(order_id, 'setCanceled')
    write_order_log(order_log_path, order_service, order_id, quantity, 0, 0, '-')


def cul_working_accounts(order_log_path: str, order_service: str, order_id: str, quantity: int) -> None:
    log('컨테이너별 브라우저 계정 셋팅에 에러가 있습니다.')
    status_change(order_id, 'setCanceled')
    write_order_log(order_log_path, order_service, order_id, quantity, 0, 0, '-')


def max_order_log(order_log_path: str, order_service: str, order_id: str, quantity: int) -> None:
    log('주문개수가 최대 주문개수를 초과하였습니다.')
    status_change(order_id, 'setCanceled')
    write_order_log(order_log_path, order_service, order_id, quantity, 0, 0, '-')


def measure_memory_usage() -> float:
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert bytes to MB


def sample_memory_usage_per_instance() -> float:
    memory_usage = measure_memory_usage()
    return memory_usage


def get_optimal_max_workers() -> int:
    cpu_count = os.cpu_count()
    # log(f"개발서버 CPU 코어 개수: {cpu_count}")

    total_memory = psutil.virtual_memory().total
    total_memory_gb = total_memory / (1024 ** 3)
    # log(f"개발서버 메모리: {total_memory_gb:.2f} GB")

    memory_usage_per_instance = sample_memory_usage_per_instance()
    # log(f"인스턴스당 메모리 사용량: {memory_usage_per_instance:.2f} MB")

    # Calculate max workers based on memory usage per instance
    max_memory_based_workers = int(total_memory // (memory_usage_per_instance * 1024 * 1024))

    # Calculate max workers based on both CPU and memory constraints
    optimal_max_workers = min(cpu_count * 2, max_memory_based_workers)

    # Ensure at least 1 worker and at most 300 workers
    return max(1, min(300, optimal_max_workers))


def format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds}"


def save_screenshot(order_id: str, user_id: str, tab_index: int, driver: WebDriver) -> None:
    if config['log']['file'] == 'True':
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         f'../log/file/{order_id}/{user_id}/{user_id}.png'))
        make_dir(file_path)
        driver.save_screenshot(file_path)
        log(f"스크린샷이 완료되었습니다. '{user_id}.png' 파일이 저장되었습니다.", user_id, tab_index)


def record_start(order_id: str, user_id: str, driver: WebDriver) -> None:
    if config['log']['file'] == 'True':
        global video_out, video_start_time, record_thread, recording

        fourcc = cv2.VideoWriter_fourcc(*"XVID")

        file_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         f'../log/file/{order_id}/{user_id}/{user_id}.avi'))

        make_dir(file_path)

        global screen_size
        video_out = cv2.VideoWriter(f'{file_path}', fourcc, 5.0, screen_size)
        video_start_time = time.time()
        record_thread = threading.Thread(target=record_screen, args=(driver,))
        record_thread.start()


# 녹화 시작 (별도의 스레드나 비동기 처리를 사용하는 방법도 있음)
def record_screen(driver: WebDriver) -> None:
    global recording
    while recording:
        frame = capture_screenshot(driver)
        video_out.write(frame)
        time.sleep(1 / 5.0)  # 20 FPS로 녹화


def capture_screenshot(driver: WebDriver) -> np.ndarray:
    global screen_size
    png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(png))
    img = img.resize(screen_size)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def record_end(user_id: str, tab_index: int) -> None:
    if config['log']['file'] == 'True':
        global recording, record_thread, video_out
        recording = False
        record_thread.join()
        video_out.release()
        log(f"녹화가 완료되었습니다. '{user_id}.avi' 파일이 저장되었습니다.", user_id, tab_index)


def last_memory_used(user_id: str, tab_index: int):
    final_memory_usage = measure_memory_usage()
    log(f"마지막 메모리 사용량: {final_memory_usage:.2f} MB", user_id, tab_index)


def make_dir(file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def set_logger(order_id: str, user_id: str, tab_index: int) -> None:
    log_filename = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     f'../log/file/{order_id}/{user_id}/{user_id}.txt'))

    make_dir(log_filename)

    # 로그 설정
    logging_ele = logging.getLogger(f"Process_{tab_index}")
    logging_ele.setLevel(logging.DEBUG)

    # 파일 핸들러 추가
    fh = logging.FileHandler(log_filename, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    logging_ele.addHandler(fh)

    global logger
    logger = logging_ele


def get_test_order_id() -> int:
    return random.randint(9000, 9999)


def set_lang(driver: WebDriver) -> None:
    # 언어 설정을 한국어로 변경하는 JavaScript 실행
    driver.execute_script("""
                document.cookie = "ig_lang=ko";
                location.reload();
            """)
    #
    # if '약관' in driver.page_source:
    #     print("'약관' 단어를 찾았습니다.")
    # else:
    #     print("'약관' 단어를 찾지 못했습니다.")


def move_page(driver: WebDriver, url: str):
    driver.get(url)
    set_language_cookie(driver)  # 페이지 이동 후 쿠키 설정


# 페이지 이동 전후로 쿠키를 다시 설정하는 함수
def set_language_cookie(driver):
    driver.execute_script("""
        document.cookie = "ig_lang=ko";
    """)


def extract_final_results(text: str, result_type: str):
    # 정규 표현식 패턴 정의: "최종결과["와 "]" 사이의 내용을 매칭
    pattern = r"최종결과\[(.*?)\]"

    # 정규 표현식을 사용하여 매칭되는 부분 추출
    match = re.search(pattern, text)

    if match:
        # 매칭된 부분을 쉼표로 분할하여 리스트로 변환
        result_str = match.group(1)
        result_list = [int(num.strip()) for num in result_str.split(',')]

        # 결과 타입에 따라 값 반환
        if result_type == 'SUCCESS' and len(result_list) > 0:
            return result_list[0]
        elif result_type == 'FAIL' and len(result_list) > 1:
            return result_list[1]
        else:
            return None
    else:
        return None


def order_max_check(quantity: int) -> bool:
    if max_order_cnt < quantity:
        return True
    else:
        return False