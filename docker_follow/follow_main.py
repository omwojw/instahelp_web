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

wait_time = int(config['selenium']['wait_time'])
driver: Optional[WebDriver] = None
act_chis = None
wait: Optional[WebDriverWait] = None
task_service = config['item']['follow']
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

    # 로그객체 생성
    common.set_logger(order_id, user_id, tab_index)

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

        try:
            import os
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 경고 및 오류만 표시
            os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # oneDNN 최적화 비활성화

            import tensorflow as tf

            # GPU 사용 가능 여부 확인
            common.log("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))
        except Exception as e:
            common.log(traceback.format_exc(), user_id, tab_index)

        # # 로그인 버튼 클릭
        # find_btns = common.find_elements("CSS_SELECTOR", "button.x5yr21d", driver, wait)
        # login_btn = None
        # for find_btn in find_btns:
        #     if find_btn.text == 'Log in' or find_btn.text == '로그인':
        #         login_btn = find_btn
        # if login_btn:
        #     common.click(login_btn)


        is_login1 = False
        is_login2 = False

        # 자동 로그인 성공
        if home_url == driver.current_url:
            is_login1 = True

            # 검증이 성공했다고 해도 동의하기가 나올수도 있음
            if common.agree_check(user_id, tab_index, driver, wait):
                common.sleep(1)
                is_agree, agree_message = common.agree_active(user_id, tab_index, driver, wait)

                if not is_agree:
                    is_login1 = False
                common.sleep(1)

        # 자동 로그인 실패
        else:
            # 계정 정지
            if 'accounts/suspended' in driver.current_url:
                raise Exception('계정정지')

            # 메타 정보동의
            elif '/consent/' in driver.current_url:
                divs = common.find_elements("TAG_NAME", "div", driver, wait)
                for div in divs:
                    if div.text == '시작하기':
                        common.click(div)
                        common.sleep(1)

                        spans = common.find_elements("TAG_NAME", "span", driver, wait)
                        for span in spans:
                            if span.text == '무료 사용':
                                common.click(span)
                                common.sleep(1)

                                span_agrees = common.find_elements("TAG_NAME", "span", driver, wait)
                                for span_agree in span_agrees:
                                    if span_agree.text == '동의':
                                        common.click(span_agree)
                                        common.sleep(1)
                                        is_login1 = True
                                        break

                if not is_login1:
                    raise Exception('광고설정')

            # 인증 후 살리기
            elif 'challenge/action' in driver.current_url:
                raise Exception('인증필요')
                # TODO 이메일 이증

            # 계정 봇 의심 경고 경우
            elif 'challenge' in driver.current_url:
                divs = common.find_elements("TAG_NAME", "div", driver, wait)
                for div in divs:
                    if div.get_attribute("aria-label") == '닫기' or div.get_attribute('aria-label') == 'Dismiss':
                        common.click(div)
                        common.sleep(3)
                        is_login1 = True
                        break

                if not is_login1:
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

            if not is_login2:
                raise Exception('2차 로그인 검증 에러')

        is_login = is_login1 and is_login2

        # 로그인 안된 경우
        if not is_login:
            login, message = common.login(user_id, user_pw, tab_index, driver, wait)
            if not login:
                raise Exception(message)
        else:
            common.log(f'자동 로그인 성공여부 {is_login1} - {is_login2}', user_id, tab_index)
    except Exception as ex:
        common.remove_from_accounts(task_service, order_id, user_id, str(ex), True)
        return f'0,1,{str(ex)}'

    try:
        if mode == 'LIVE':
            remains = common.get_remains(order_id)
        else:
            remains = 1
        common.log(f'남은 수량 : {remains}', user_id, tab_index)

        # 남은 개수가 0개면 완료처리
        if remains == 0:
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
        common.log(traceback.format_exc(), user_id, tab_index)
        return f'0,1,태스크 실패'


# 주문 프로 세스
def fetch_order() -> tuple:
    try:
        common.move_page(driver, order_url)
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
        common.log('팔로우 시작', user_id, tab_index)
        btn_elements = common.find_elements("CSS_SELECTOR", "button._acan", driver, wait)
        follow_status = 0
        follow_btn = None
        for btn_element in btn_elements:
            if btn_element.text == 'Follow' or btn_element.text == '팔로우':
                follow_status = 1
                follow_btn = btn_element
            elif btn_element.text == 'Following' or btn_element.text == '팔로잉':
                follow_status = 2
        common.sleep(1)
        if follow_status == 1:
            common.click(follow_btn)
            common.sleep(5)

            is_follow = False
            message = '팔로우 버튼을 눌렀지만 에러'
            after_elements = common.find_elements("CSS_SELECTOR", "button._acan", driver, wait)
            for after_element in after_elements:
                if after_element.text == 'Following' or after_element.text == '팔로잉':
                    is_follow = True
                    message = '성공'
                elif after_element.text == '동의함':
                    message = '동의함 처리됨'

        elif follow_status == 2:
            is_follow = False
            message = '이미 팔로우 되어 있음'
        else:
            is_follow = False
            message = '에러발생'

        common.sleep(2)
        common.log(f'팔로우 종료 - {message}', user_id, tab_index)
        return is_follow, message
    except Exception as ex:
        raise Exception(ex)


def main_fun(_tab_index: int, _user_id: str, _user_pw: str, _ip: str, _order_id: str, _quantity: int,
             _order_url: str, _mode: str, _session_id: str) -> str:
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