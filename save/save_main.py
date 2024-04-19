import sys
import os


if sys.platform.startswith('win'):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
elif sys.platform == 'darwin':
    sys.path.append("../")

import configparser
import common.fun as common
import traceback

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 글로벌 변수
tab_index = None
user_id = None
user_pw = None
ip = None
order_id = None
quantity = None
order_url = None
wait_time = int(config['selenium']['wait_time'])
driver = None
act_chis = None
wait = None
task_service = "SAVE"
task_log_path = "../log/task_history.txt"


# 셀레 니움 실행
def setup() -> str:
    if current_os == 'MAC':
        driver_path = config['selenium']['driver_path_mac']
        chrome_path = config['selenium']['chrome_path_mac']
    else:
        driver_path = config['selenium']['driver_path_window']
        chrome_path = config['selenium']['chrome_path_window']
    # Chrome 웹 드라이버 경로 설정
    chromedriver_path = driver_path

    # Chrome 웹 드라이버 설정
    options = webdriver.ChromeOptions()


    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    # options.add_argument('--proxy-server={}'.format(ip))
    options.binary_location = chrome_path
    # 웹 드라 이버 시작
    service = ChromeService(executable_path=chromedriver_path)
    selenium_driver = webdriver.Chrome(service=service, options=options)
    selenium_driver.implicitly_wait(wait_time)
    selenium_driver.set_window_size(450, 975)

    global driver
    driver = selenium_driver
    return dashboard()


# 대시 보드
def dashboard() -> str:
    global driver, act_chis, wait
    act_chis = ActionChains(driver)
    wait = WebDriverWait(driver, wait_time, poll_frequency=1)

    # 페이지 띄우기
    driver.get("https://www.instagram.com/")

    # common.sleep(5)
    # # 현재 IP 주소를 가져옵니다.
    # current_ip = driver.find_element_by_css_selector('.ip').text
    # print("Current IP address:", current_ip)

    success = 0
    fail = 0

    # 로그인 여부 체크
    is_login = common.is_display("TAG_NAME", "loginForm", driver)

    # 로그인 안된 경우
    if not is_login:
        if not login(user_id, user_pw):
            common.remove_from_accounts(task_service, user_id, '로그인 실패')
            return f'0,0'

    try:
        remains = common.getRemains(order_id)
        common.log(f'남은 수량 : {remains}', tab_index)

        # 남은 개수가 0개면 완료처리
        if remains == 0:
            return f'0,0'

        result, message = fetch_order()
        if result:
            common.setRemains(order_id, 1)
            success += 1
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'OK', '없음')
        else:
            fail += 1
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', message)
    except Exception as ex:
        fail += 1
        common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', ex)
        common.remove_from_accounts(task_service, user_id, '태스크 실패')
        common.remove_from_error(traceback.format_exc(), order_id)
        print(traceback.format_exc())
    return f'{success},{fail}'


# 주문 프로 세스
def fetch_order() -> tuple:
    try:
        driver.get(order_url)
        result, message = save()
        return result, message
    except Exception as ex:
        raise Exception(ex)
        return False, ''


# 주문 수행
def save() -> tuple:
    try:
        save_element = common.find_element("CSS_SELECTOR", ".x1gslohp>.x6s0dn4>.x11i5rnm>div", driver, wait)
        save_svg = common.find_children_element("TAG_NAME", "svg", driver, save_element)
        if save_svg.get_attribute('aria-label') == '저장':
            save_element.click()
            return True, ''
        else:
            return False, '이미 저장 되어 있음'

    except Exception as ex:
        raise Exception(ex)
        return False, ''


# 로그인
def login(account_id: str, account_pw: str) -> None:
    try:
        # 로그인
        common.log('로그인 시작', tab_index)

        # 계정을 입력합니다.
        id_input = common.find_element('NAME', "username", driver, wait)
        id_input.click()
        id_input.send_keys(account_id)

        # 비밀번호를 입력합니다.
        pw_input = common.find_element('NAME', "password", driver, wait)
        pw_input.click()
        pw_input.send_keys(account_pw)

        # 로그인 버튼을 클릭(탭)합니다.
        login_btns = common.find_elements('TAG_NAME', "button", driver, wait)
        login_btn = common.search_element('TEXT', login_btns, '로그인')
        login_btn.click()
        common.log('로그인 종료', tab_index)
        common.sleep(5)

        btns = common.find_elements("TAG_NAME", "button", driver, wait)
        find_btn = common.search_element("TEXT", btns, '정보 저장')
        if not find_btn:
            return False
        else:
            return True

    except Exception as ex:
        return False


def mainFun(_tab_index, _user_id, _user_pw, _ip, _order_id, _quantity, _order_url) -> str:
    global tab_index, user_id, user_pw, ip, order_id, quantity, order_url
    tab_index = _tab_index + 1
    user_id = _user_id
    user_pw = _user_pw
    ip = _ip
    order_id = _order_id
    quantity = _quantity
    order_url = _order_url

    # 시작 함수
    try:
        return setup()
    except Exception as ex:
        common.remove_from_error(traceback.format_exc(), order_id)
        print(traceback.format_exc())
        return f'0,0'

