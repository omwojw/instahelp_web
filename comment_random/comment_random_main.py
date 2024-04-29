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
comment = None
order_url = None
wait_time = int(config['selenium']['wait_time'])
driver = None
act_chis = None
wait = None
task_service = "COMMENT_RANDOM"
task_log_path = "../log/task_history.txt"
mode = None


# 셀레 니움 실행
def setup() -> str:
    global driver
    driver = common.openSelenium(current_os, wait_time, ip)
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
    is_login = common.is_display("ID", "splash-screen", driver)

    # 로그인 안된 경우
    if is_login:
        if not common.login(user_id, user_pw, tab_index, driver, wait):
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '로그인 실패')
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
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '남은 개수 없음')
            common.remove_from_accounts(task_service, user_id, '남은 개수 없음')
            return f'0,1'

        result, message = fetch_order()
        if result:
            if mode == 'LIVE':
                common.setRemains(order_id, 1)
            success += 1
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'OK', '없음')
        else:
            fail += 1
            common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', message)
    except Exception as ex:
        fail += 1
        common.write_task_log(task_log_path, task_service, order_id, user_id, 'NO', '에러발생')
        common.remove_from_accounts(task_service, user_id, '태스크 실패')
        common.remove_from_error(traceback.format_exc(), order_id)
        print(traceback.format_exc())
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

        result, message = comment_random()
        return result, message
    except Exception as ex:
        raise Exception(ex)
        return False, ''


# 주문 수행
def comment_random() -> tuple:
    try:
        common.log('랜덤댓글 시작', tab_index)
        comment_element = common.find_element("CSS_SELECTOR", "span.xp7jhwk", driver, wait).find_element(By.XPATH, 'following-sibling::*')
        comment_svg = common.find_children_element("TAG_NAME", "svg", driver, comment_element)
        if comment_svg.get_attribute('aria-label') == 'Comment' or comment_svg.get_attribute('aria-label') == '댓글 달기':
            comment_element.click()
            common.sleep(1)

            click_comment = find_text_area()
            if click_comment:
                click_comment.click()

            text_comment = find_text_area()
            if text_comment:
                text_comment.send_keys(comment)
                common.sleep(1)
                send_btn = common.find_element("CSS_SELECTOR", ".xdj266r.x1emribx.xat24cr.x1i64zmx", driver, wait)
                send_btn.click()
                common.log('랜덤댓글 종료', tab_index)
                return True, ''

        common.log('랜덤댓글 종료', tab_index)
        return False, '에러'
    except Exception as ex:
        raise Exception(ex)
        return False, ''


def find_text_area() -> object:
    find_comments = common.find_elements("TAG_NAME", "textarea", driver, wait)
    for find_comment in find_comments:
        if find_comment.get_attribute("aria-label") == 'Add a comment…' or find_comment.get_attribute(
                "aria-label") == '댓글 달기...':
            return find_comment

    return None


def mainFun(_tab_index, _user_id, _user_pw, _ip, _order_id, _quantity, _comment, _order_url, _mode) -> str:
    global tab_index, user_id, user_pw, ip, order_id, quantity, comment, order_url, mode
    tab_index = _tab_index + 1
    user_id = _user_id
    user_pw = _user_pw
    ip = _ip
    order_id = _order_id
    quantity = _quantity
    comment = _comment
    order_url = _order_url
    mode = _mode

    # 시작 함수
    try:
        return setup()
    except Exception as ex:
        common.remove_from_error(traceback.format_exc(), order_id)
        print(traceback.format_exc())
        return f'0,0'

