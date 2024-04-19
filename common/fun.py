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

# Config 읽기
config = configparser.ConfigParser()
current_os = None
if sys.platform.startswith('win'):
    config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'setting', 'config.ini'), encoding='utf-8')
    current_os = 'WINDOW'
elif sys.platform == 'darwin':
    config.read('../setting/config.ini', encoding='utf-8')
    current_os = 'MAC'


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


# 주문 결과 로그 추가
def write_order_log(path: str, service: str, order_id: str, quantity: int, success: int, fail: int) -> None:
    with open(path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}/{current_time}/{order_id}/{quantity}/{success}/{fail}"
        f.write(f"{message}\n")
        send_message(config['telegram']['chat_order_id'], message)


# 태스크 로그 추가
def write_task_log(path: str, service: str, order_id: str, user_id: str, result: str, err_msg: str ) -> None:
    with open(path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f'{service}/{current_time}/{order_id}/{user_id}/{result}/{err_msg}'
        f.write(f"{message}\n")

    if result != 'OK':
        send_message(config['telegram']['chat_error_task'], message)


# 에러 계정 추가
def remove_from_accounts(service: str, current_user_id: str, err_msg: str) -> None:
    with open("../log/error_accounts.txt", "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}/{current_time}/{current_user_id}/{err_msg}"
        f.write(f"{message}\n")

    send_message(config['telegram']['chat_error_account'], message)


# 에러 로그 추가
def remove_from_error(log_txt: str, device_name: str) -> None:
    with open("../log/error_log.txt", "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{device_name}/{current_time}/{log_txt}\n")


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
def log(text: str, tab_index='ALL') -> None:
    if config['log']['show'] == 'True':
        print(f'[{tab_index}][{get_current_time()}] {text}')


# 주문의 남은 수량 변경
def setRemains(order_id: str, remains: int) -> None:
    if config['task']['mode'] == 'TEST':
        return
    try:
        prev_remains = getRemains(order_id)
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
def getRemains(order_id: str) -> int:
    if config['task']['mode'] == 'TEST':
        return 1
    try:
        res = requests.post(f"{config['api_v2']['url']}/{order_id}",
                            data={
                                'apikey': config['api_v2']['key'],
                            }, timeout=10).json()
        return int(res['remains'])
    except Exception as ex:
        raise Exception('퍼팩트 패널  남은개수 가져오기 에러')

