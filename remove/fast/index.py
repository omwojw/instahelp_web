import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ProcessPoolExecutor
from selenium.webdriver.chrome.service import Service as ChromeService
from datetime import timedelta


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")

    # ChromeDriver와 Chrome 브라우저 경로 설정
    chrome_service = ChromeService(executable_path="/usr/local/bin/chromedriver_linux")
    chrome_options.binary_location = "/usr/bin/google-chrome"

    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    return driver


def login(idx, user_id, user_pw, login_url):
    driver = setup_driver()
    driver.get(login_url)
    print(f"{idx+1} - {user_id} - {user_pw} - {driver.current_url}")
    driver.quit()


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes} 분 {seconds} 초"


def main():
    start_time = time.time()
    active_accounts = [
        "user1|password1",
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


if __name__ == '__main__':
    main()
