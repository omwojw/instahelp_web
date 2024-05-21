import sys
import os


if sys.platform.startswith('win'):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
elif sys.platform == 'darwin':
    sys.path.append("../")

import configparser
import common.fun as common
import traceback
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
mode = None
session_id = None


# 셀레 니움 실행
def setup() -> str:
    global driver
    driver = common.open_selenium(current_os, wait_time, ip, session_id)
    return dashboard()


# 대시 보드
def dashboard() -> str:
    global driver, act_chis, wait
    act_chis = ActionChains(driver)
    wait = WebDriverWait(driver, wait_time, poll_frequency=1)

    # 페이지 띄우기
    driver.get("https://instagram.com/")

    success = 0
    fail = 0

    # 로그인 여부 체크
    # is_login = common.is_display("ID", "loginForm", driver)
    # is_login = common.is_display("ID", "splash-screen", driver)
    try:
        is_login = False
        svgs = common.find_elements("TAG_NAME", "svg", driver, wait)
        for svg in svgs:
            if svg.get_attribute("aria-label") == '홈':
                is_login = True

        # 로그인 안된 경우
        if not is_login:
            if not common.login(user_id, user_pw, tab_index, driver, wait):
                common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '로그인 실패', order_url)
                common.remove_from_accounts(task_service, user_id, '로그인 실패')
                return f'0,1'
    except Exception as ex:
        common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '로그인 실패', order_url)
        common.remove_from_accounts(task_service, user_id, '로그인 실패')
        return f'0,1'

    try:
        if mode == 'LIVE':
            remains = common.getRemains(order_id)
        else:
            remains = 1
        common.log(f'남은 수량 : {remains}', tab_index)

        # 남은 개수가 0개면 완료처리
        if remains == 0:
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '남은 개수 없음', order_url)
            common.remove_from_accounts(task_service, user_id, '남은 개수 없음')
            return f'0,1'

        result, message = fetch_order()
        if result:
            if mode == 'LIVE':
                common.setRemains(order_id, 1)
            success += 1
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'OK', '없음', order_url)
        else:
            fail += 1
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', message, order_url)
    except Exception as ex:
        fail += 1
        common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '에러발생', order_url)
        common.remove_from_accounts(task_service, user_id, '태스크 실패')
        print(traceback.format_exc())

    # 3초간 체류하기
    if success > 0:
        common.write_working_log(task_service, user_id, success)
    common.sleep(3)
    return f'{success},{fail}'


# 주문 프로 세스
def fetch_order() -> tuple:
    try:
        driver.get(order_url)
        common.sleep(1)

        # if common.agree_check(tab_index, driver):
        #     common.sleep(1)
        #     common.agree_active(tab_index, driver, wait)
        #     common.sleep(1)

        result, message = save()
        return result, message
    except Exception as ex:
        raise Exception(ex)
        return False, ''


# 주문 수행
def save() -> tuple:
    try:
        common.log('저장하기 시작', tab_index)
        save_element = common.find_element("CSS_SELECTOR", ".x1gslohp>.x6s0dn4>.x11i5rnm>div", driver, wait)
        save_svg = common.find_children_element("TAG_NAME", "svg", driver, save_element)

        is_save = False
        message = '이미 저장 되어 있음'
        if save_svg.get_attribute('aria-label') == 'Save' or save_svg.get_attribute('aria-label') == '저장':
            common.click(save_element)
            is_save = True
            message = ""
        common.log('저장하기 종료', tab_index)
        return is_save, message
    except Exception as ex:
        raise Exception(ex)
        return False, ''


def mainFun(_tab_index, _user_id, _user_pw, _ip, _order_id, _quantity, _order_url, _mode, _session_id) -> str:
    global tab_index, user_id, user_pw, ip, order_id, quantity, order_url, mode, session_id
    tab_index = _tab_index + 1
    user_id = _user_id
    user_pw = _user_pw
    ip = _ip
    order_id = _order_id
    quantity = _quantity
    order_url = _order_url
    mode = _mode
    session_id = _session_id

    # 시작 함수
    try:
        return setup()
    except Exception as ex:
        print(traceback.format_exc())
        return f'0,0'

