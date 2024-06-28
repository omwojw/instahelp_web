import tensorflow as tf
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ProcessPoolExecutor
from selenium.webdriver.chrome.service import Service as ChromeService
from datetime import timedelta
import configparser
import os
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../', 'setting', 'config.ini'), encoding='utf-8')

def setup_driver():
    driver_path = config['selenium']['driver_path_window']
    chrome_path = config['selenium']['chrome_path_window']

    chrome_options = Options()
    # chrome_options.add_argument("--headless")

    chrome_options.add_argument("--disable-gpu")  # 테스트 시에는 필요할 수 있음
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    chrome_options.add_argument("--enable-gpu-rasterization")  # GPU 래스터화 활성화
    chrome_options.add_argument("--ignore-gpu-blocklist")  # GPU 블록리스트 무시



    # ChromeDriver와 Chrome 브라우저 경로 설정
    # chrome_service = ChromeService(executable_path="/usr/local/bin/chromedriver_linux")
    # chrome_options.binary_location = "/usr/bin/google-chrome"

    chrome_service = ChromeService(executable_path=driver_path)
    chrome_options.binary_location = chrome_path

    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    return driver


def login(idx, user_id, user_pw, login_url):
    driver = setup_driver()
    time.sleep(3)
    print(f"{idx + 1} - {user_id} - {user_pw} - {driver.current_url}")
    driver.get(login_url)
    time.sleep(99999)
    driver.quit()


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes} 분 {seconds} 초"


def main():
    start_time = time.time()
    active_accounts = [
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
        "user1|password1",
    ]

    # login_url = "chrome://gpu"  # Replace with your login URL
    login_url = "https://instagram.com"  # Replace with your login URL

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(
            login,
            index,
            account.split('|')[0],
            account.split('|')[1],
            login_url
        ) for index, account in enumerate(active_accounts)]

        for future in futures:
            future.result()  # Get the result of the future (if needed)

    end_time = time.time()
    elapsed_time = timedelta(seconds=end_time - start_time)
    formatted_time = format_timedelta(elapsed_time)
    print(f"걸린시간: {formatted_time} 계정개수 {len(active_accounts)}")




if __name__ == '__main__':
    main()
