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
from selenium.webdriver.common.by import By
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
comment = ''
mode = ''

wait_time = int(config['selenium']['wait_time'])
driver: Optional[WebDriver] = None
act_chis = None
wait: Optional[WebDriverWait] = None
task_service = config['item']['comment_fix']
task_log_path = "../log/task_history.txt"


# 셀레 니움 실행
def setup() -> str:
    global driver
    driver = common.open_selenium(current_os, wait_time, ip, session_id, tab_index)
    return dashboard()


# 대시 보드
def dashboard() -> str:
    global driver, act_chis, wait

    # 녹화시작
    common.record_start(order_id, user_id, driver)

    # 로그객체 생성
    common.set_logger(order_id, user_id, tab_index)

    act_chis = ActionChains(driver)
    wait = WebDriverWait(driver, wait_time, poll_frequency=1)
    success = 0
    fail = 0

    # 로그인 여부 체크
    try:

        # 페이지 띄우기
        home_url = "https://www.instagram.com/"
        driver.get(home_url)
        common.set_lang(driver)

        is_login1 = False
        is_login2 = False
        if home_url == driver.current_url:
            is_login1 = True
        else:
            if 'challenge' in driver.current_url:
                divs = common.find_elements("CLASS_NAME", "wbloks_1", driver, wait)
                for div in divs:
                    if div.get_attribute("aria-label") == '닫기':
                        common.click(div)
                        common.sleep(3)
                        is_login1 = True
                        break

        if common.is_display("TAG_NAME", "svg", driver):
            svgs = common.find_elements("TAG_NAME", "svg", driver, wait)
            for svg in svgs:
                if svg.get_attribute("aria-label") == '홈':
                    is_login2 = True
                    break

        # 로그인 안된 경우
        if not is_login1 or not is_login2:
            if not common.login(user_id, user_pw, tab_index, driver, wait):
                raise Exception('로그인 실패')
        else:
            common.log(f'로그인 성공여부 True', user_id, tab_index)
    except Exception as ex:
        common.remove_from_accounts(task_service, order_id, user_id, '로그인 실패', True)
        # print(traceback.format_exc())
        return f'0,1,로그인 실패'

    try:
        if mode == 'LIVE':
            remains = common.get_remains(order_id)
        else:
            remains = 1
        common.log(f'남은 수량 : {remains}', user_id, tab_index)

        # 남은 개수가 0개면 완료처리
        if remains == 0:
            # common.remove_from_accounts(task_service, order_id, user_id, '남은 개수 없음')
            return f'0,1,남은 개수 없음'

        result, message = fetch_order()
        if result:
            if mode == 'LIVE':
                common.set_remains(order_id, 1)
            success += 1
        else:
            fail += 1

        if success > 0:
            common.write_working_log(task_service, user_id, success)
            common.write_working_save_log(task_service, order_id, user_id, order_url)
        common.sleep(3)
        return f'{success},{fail},{message}'
    except Exception as ex:
        # common.remove_from_accounts(task_service, order_id, user_id, '태스크 실패')
        print(traceback.format_exc())
        return f'0,1,태스크 실패'


# 주문 프로 세스
def fetch_order() -> tuple:
    try:
        driver.get(order_url)
        common.sleep(2)

        if common.agree_check(user_id, tab_index, driver, wait):
            common.sleep(1)
            is_agree, agree_message = common.agree_active(user_id, tab_index, driver, wait)

            if not is_agree:
                raise Exception(agree_message)

            common.sleep(1)

        result, message = process()
        return result, message
    except Exception as ex:
        raise Exception(ex)


# 주문 수행
def process() -> tuple:
    try:
        common.log('지정댓글 시작', user_id, tab_index)
        comment_element = common.find_element("CSS_SELECTOR", "span.xp7jhwk", driver, wait).find_element(By.XPATH, 'following-sibling::*')
        comment_svg = common.find_children_element("TAG_NAME", "svg", driver, comment_element)
        if comment_svg.get_attribute('aria-label') == 'Comment' or comment_svg.get_attribute('aria-label') == '댓글 달기':
            common.click(comment_element)
            common.sleep(1)

            click_comment = find_text_area()
            if click_comment:
                common.click(click_comment)

            text_comment = find_text_area()
            if text_comment:
                text_comment.send_keys(comment)
                common.sleep(1)
                send_btn = common.find_element("CSS_SELECTOR", ".xdj266r.x1emribx.xat24cr.x1i64zmx", driver, wait)
                common.click(send_btn)
                is_comment = True
                message = '성공'
            else:
                is_comment = False
                message = '에러발생'

            common.sleep(2)
            common.log('지정 댓글 종료', user_id, tab_index)
            return is_comment, message
    except Exception as ex:
        raise Exception(ex)


def find_text_area() -> object:
    find_comments = common.find_elements("TAG_NAME", "textarea", driver, wait)
    for find_comment in find_comments:
        if find_comment.get_attribute("aria-label") == 'Add a comment…' or find_comment.get_attribute(
                "aria-label") == '댓글 달기...':
            return find_comment

    return None


def main_fun(_tab_index: int, _user_id: str, _user_pw: str, _ip: str, _order_id: str, _quantity: int,
             _comment: str, _order_url: str, _mode: str, _session_id) -> str:
    global tab_index, user_id, user_pw, ip, order_id, quantity, comment, order_url, mode, session_id
    tab_index = _tab_index + 1
    user_id = _user_id
    user_pw = _user_pw
    ip = _ip
    order_id = _order_id
    quantity = _quantity
    comment = _comment
    order_url = _order_url
    mode = _mode
    session_id = _session_id

    # 시작 함수
    try:
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
        return result
    except Exception as ex:
        common.write_task_log(task_log_path, task_service, order_id, user_id, False, '에러발생', order_url)
        print(traceback.format_exc())
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
        driver.quit()

