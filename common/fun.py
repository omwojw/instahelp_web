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


# 주문 결과 로그 추가
def write_order_log(path: str, service: str, order_id: str, quantity: int, success: int, fail: int) -> None:
    with open(path, "a") as f:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{service}/{current_time}/{order_id}/{quantity}/{success}/{fail}"
        f.write(f"{message}\n")
        send_message(config['telegram']['chat_order_id'], message)


# 태스크 로그 추가
def write_task_log(path: str, service: str, order_id: str, user_id: str, result: str, err_msg: str) -> None:
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
def log(text: str, tab_index='ALL') -> None:
    if config['log']['show'] == 'True':
        print(f'[{tab_index}][{get_current_time()}] {text}')


# 주문의 남은 수량 변경
def setRemains(order_id: str, remains: int) -> None:
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
    try:
        res = requests.get(f"{config['api_v2']['url']}/{order_id}?apikey={config['api_v2']['key']}", timeout=10).json()
        return int(res['data']['remains'])
    except Exception as ex:
        raise Exception('퍼팩트 패널  남은개수 가져오기 에러')


# 엘리머튼 정보 콘솔출력
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
def openSelenium(curt_os: str, wait_time: int, ip: str) -> object:
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
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=450x975')

    user_agent = get_user_agent()
    options.add_argument(f'--user-agent={user_agent}')

    # options.add_argument("--lang=ko_KR")

    # 프록시 설정은 윈도우에서만 가능
    if current_os == 'WINDOW':
        options.add_argument(f'--proxy-server={ip}')

    options.binary_location = chrome_path

    # 웹 드라 이버 시작
    service = ChromeService(executable_path=chromedriver_path)
    selenium_driver = webdriver.Chrome(service=service, options=options)
    selenium_driver.implicitly_wait(wait_time)
    selenium_driver.set_window_size(450, 975)

    return selenium_driver


# 화면에 동의요청 화면이 나왔는지 체크
def agree_check(tab_index, driver) -> bool:
    log('동의여부 체크 시작', tab_index)
    is_agree = is_display("CSS_SELECTOR", ".wbloks_1>.wbloks_1>.wbloks_1>.wbloks_1>.wbloks_1.wbloks_1>span",
                          driver)
    log(f'동의여부 체크 종료 : {"동의 되어있지 않음" if is_agree else "동의 되어있음"}', tab_index)
    return is_agree


# 동의 하기
def agree_active(tab_index, driver, wait) -> tuple:
    try:
        log('동의하기 클릭 시작', tab_index)
        agree_elements = find_elements("TAG_NAME", "input", driver, wait)
        filter_agree_elements = search_elements("ATTR", agree_elements, "checkbox", "type")
        for agree in filter_agree_elements:
            agree.click()

        agrees = find_elements("CLASS_NAME", "wbloks_1", driver, wait)
        for agree in agrees:
            if agree.get_attribute("aria-label") == '동의함':
                agree.click()

                agrees_close = find_elements("CLASS_NAME", "wbloks_1", driver, wait)
                for agree_close in agrees_close:
                    if agree_close.get_attribute("aria-label") == '닫기':
                        agree_close.click()
                        log('동의하기 클릭 종료', tab_index)
                        return True, ''
        log('동의하기 클릭 종료', tab_index)
        return False, ''
    except Exception as ex:
        raise Exception(ex)
        return False, ''


# 로그인
def login(account_id: str, account_pw: str, tab_index, driver, wait) -> bool:
    try:
        # 로그인
        log('로그인 시작', tab_index)

        # 로그인 버튼 클릭
        find_btns = common.fun.find_elements("CSS_SELECTOR", "button.x5yr21d", driver, wait)
        login_btn = None
        for find_btn in find_btns:
            if find_btn.text == 'Log in' or find_btn.text == '로그인':
                login_btn = find_btn

        if login_btn:
            login_btn.click()
        else:
            return False

        # 계정을 입력합니다.
        id_input = find_element('NAME', "username", driver, wait)
        id_input.click()
        id_input.send_keys(account_id)

        # 비밀번호를 입력합니다.
        pw_input = find_element('NAME', "password", driver, wait)
        pw_input.click()
        pw_input.send_keys(account_pw)

        # 로그인 버튼을 클릭(탭)합니다.
        login_btns = find_elements('TAG_NAME', "button", driver, wait)
        # for s in login_btns:
        #     print(s.text)

        login_btn = search_element('ATTR', login_btns, 'submit', "type")
        login_btn.click()
        log('로그인 종료', tab_index)
        sleep(5)

        log('로그인 정보 저장 시작', tab_index)
        btn = find_element("TAG_NAME", "button", driver, wait)
        log('로그인 정보 저장 종료', tab_index)
        if not btn:
            return False
        else:
            return True

    except Exception as ex:
        return False
