import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ProcessPoolExecutor
from selenium.webdriver.chrome.service import Service as ChromeService
from datetime import timedelta


def setup_driver():
    chrome_options = Options()

    # 헤드리스 모드
    chrome_options.add_argument("--headless")

    # chrome_options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    service = ChromeService(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def login(idx, user_id, user_pw, login_url):
    # driver = setup_driver()
    # driver.get(login_url)
    print(f"{idx+1} - {user_id} - {user_pw}")
    # driver.quit()


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes} 분 {seconds} 초"


def main():
    start_time = time.time()
    active_accounts = [
        "user1|password1",
        "user2|password2",
        "user3|password3",
    ]

    login_url = "https://www.instagram.com/"  # Replace with your login URL

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

    time.sleep(100000)


if __name__ == '__main__':
    main()
