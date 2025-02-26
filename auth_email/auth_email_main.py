import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
# if sys.platform.startswith('win'):
#     sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
# elif sys.platform == 'darwin':
#     sys.path.append("../")

import configparser
import common.fun as common
import traceback
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from typing import Optional


# Config 읽기
config = configparser.ConfigParser()
common.get_config(config)

# OS 읽기
current_os = common.get_os()

# 글로벌 변수
tab_index = 0
user_id = ''
user_pw = ''
ip = ''
order_id = ''
quantity = 0
order_url = ''
session_id = ''
mode = ''
email = ''
email_pw = ''

wait_time = int(config['selenium']['wait_time'])
driver: Optional[WebDriver] = None
act_chis = None
wait: Optional[WebDriverWait] = None
task_service = config['item']['email']
task_log_path = "../log/task_history.txt"


# 셀레 니움 실행
def setup() -> str:
    global driver
    try:
        driver = common.open_selenium(current_os, wait_time, ip, session_id, tab_index)
    except Exception as e:
        common.sleep(3)
        driver = common.open_selenium(current_os, wait_time, ip, session_id, tab_index)

    # 인스턴스 종료
    if driver:
        return dashboard()
    else:
        return f'0,1,셀레니움 오픈 실패'


# 대시 보드
def dashboard() -> str:
    global driver, act_chis, wait

    # 녹화시작
    common.record_start(order_id, user_id, driver)

    act_chis = ActionChains(driver)
    wait = WebDriverWait(driver, wait_time, poll_frequency=1)
    success = 0
    fail = 0

    # 로그인 여부 체크
    try:

        # 페이지 띄우기
        login_url = "https://www.instagram.com/accounts/login/"
        home_url = "https://www.instagram.com/"
        driver.get(login_url)
        common.set_lang(driver)
        common.sleep(3)

        is_login1 = False
        is_login2 = False

        # 자동 로그인 성공
        if home_url == driver.current_url:
            is_login1 = True

        # 자동 로그인 실패
        else:
            # 계정 정지
            if 'accounts/suspended' in driver.current_url:
                raise Exception('계정정지')

            # 메타 정보동의
            elif '/consent/' in driver.current_url:
                raise Exception('광고설정')

            # 인증 후 살리기
            elif 'challenge/action' in driver.current_url:
                raise Exception('인증필요')

            # 계정 봇 의심 경고 경우
            elif 'challenge' in driver.current_url:
                 raise Exception('의심경고')

        common.sleep(3)
        # 로그인 2차 검증
        if is_login1:
            if common.is_display("TAG_NAME", "svg", driver):
                svgs = common.find_elements("TAG_NAME", "svg", driver, wait)
                for svg in svgs:
                    if svg.get_attribute("aria-label") == '홈' or svg.get_attribute("aria-label") == 'Home':
                        is_login2 = True
                        break

            if common.is_display("TAG_NAME", "button", driver):
                btns = common.find_elements("TAG_NAME", "button", driver, wait)
                for btn in btns:
                    if btn.text == '나중에 하기' or btn.text == 'Do it later':
                        is_login2 = True
                        break
            if common.is_display("TAG_NAME", "span", driver):
                spans = common.find_elements("TAG_NAME", "span", driver, wait)
                for span in spans:
                    if span.text == '나중에 하기' or span.text == 'Do it later':
                        is_login2 = True
                        break

            if not is_login2:
                raise Exception('로그인(2차) 검증 에러')

        is_login = is_login1 and is_login2

        # 로그인 안된 경우
        if not is_login:
            login, message = common.login(
                user_id
                , user_pw
                , tab_index
                , driver
                , wait
                , email
                , email_pw
                , ip
            )
            if not login:
                raise Exception(message)
            else:
                is_login = True
        else:
            common.log(f'자동 로그인 성공여부 {is_login1} - {is_login2}', user_id, tab_index)
    except Exception as ex:
        common.remove_from_accounts(task_service, order_id, user_id, str(ex), True)
        return f'0,1,{str(ex)}'

    if is_login:
        success = 1
    else:
        fail = 1

    return f'{success},{fail},성공'


def main_fun(_tab_index: int, _user_id: str, _user_pw: str, _ip: str, _mode: str, _session_id: str, _email: str, _email_pw: str) -> str:
    global tab_index, user_id, user_pw, ip, mode, session_id, email, email_pw
    tab_index = _tab_index + 1
    user_id = _user_id
    user_pw = _user_pw
    ip = _ip
    mode = _mode
    session_id = _session_id
    email = _email
    email_pw = _email_pw

    # 시작 함수
    try:
        # 로그객체 생성
        common.set_logger(order_id, user_id, tab_index)

        initial_memory_usage = common.measure_memory_usage()
        common.log(f"초기 메모리 사용량: {initial_memory_usage:.2f} MB", user_id, tab_index)

        result = setup()
        success = int(result.split(',')[0])
        fail = int(result.split(',')[1])
        message = result.split(',')[2]

        is_result = False
        if success > 0:
            is_result = True

        if fail > 0:
            is_result = False

        common.write_task_log(task_log_path, task_service, order_id, user_id, is_result, message, order_url)
        common.log(f'Task[{result}]', user_id, tab_index)
        return result
    except Exception as ex:
        common.write_task_log(task_log_path, task_service, order_id, user_id, False, '에러발생', order_url)
        common.log(traceback.format_exc(), user_id, tab_index)
        common.log(f'Task[0,1,에러발생]', user_id, tab_index)
        return f'0,1,에러발생'
    finally:

        global driver

        # 마지막 최종 메모리 사용량 로그
        common.last_memory_used(user_id, tab_index)

        # 녹화 종료
        common.record_end(user_id, tab_index)

        # 스크린샷 저장
        common.save_screenshot(order_id, user_id, tab_index, driver)

        # 인스턴스 종료
        if driver:
            driver.quit()