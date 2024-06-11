import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ProcessPoolExecutor
from selenium.webdriver.chrome.service import Service as ChromeService
from datetime import timedelta
import os
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
def setup_driver():
    chrome_options = Options()

    # 헤드리스 모드
    chrome_options.add_argument("--headless")

    # 크롬 확장프로그램 비활성화
    # 확장 프로그램이 성능을 저하시키거나 불필요한 리소스를 사용할 수 있으므로 이를 비활성화하여 성능을 최적화합니다.
    chrome_options.add_argument("--disable-extensions")

    # GPU 하드웨어 가속을 비활성화
    # GPU 가속이 필요 없는 경우 이를 비활성화하여 리소스를 절약합니다. 특히 헤드리스 모드에서는 유용합니다.
    chrome_options.add_argument("--disable-gpu")

    # 샌드박스 모드를 비활성화
    # 샌드박스 모드를 비활성화하면 성능이 향상될 수 있지만, 보안상의 이유로 사용에 주의가 필요합니다.
    chrome_options.add_argument("--no-sandbox")

    # 공유메모리를 사용하지 않도록 설정
    # 공유 메모리 크기가 작은 환경에서는 이를 비활성화하여 크롬이 디스크를 대신 사용하도록 합니다. Docker 같은 환경에서 유용합니다.
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 브라우저측 네비게이션 비활성화
    # 이 옵션은 특정 상황에서 성능을 최적화할 수 있습니다.
    chrome_options.add_argument("--disable-browser-side-navigation")

    # 자동화된 브라우저 환경을 위해 설정합니다.
    # 크롬이 자동화된 환경에서 실행되고 있음을 나타내어 특정 최적화 및 기능을 활성화합니다.
    chrome_options.add_argument("enable-automation")

    # "Chrome is being controlled by automated test software" 메시지 바를 비활성화합니다.
    # 사용자 경험을 방해하지 않도록 메시지 바를 숨깁니다.
    chrome_options.add_argument("--disable-infobars")

    # AutomationControlled 기능을 비활성화합니다.
    # 사이트가 브라우저 자동화를 감지하지 못하게 합니다.
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # 원격 디버깅 포트를 설정합니다.
    # 디버깅 및 성능 최적화를 위해 사용될 수 있습니다. 여러 인스턴스 실행 시 겹치지 않는 포트를 설정해야 합니다.
    # chrome_options.add_argument("--remote-debugging-port=9222")

    # 사이트 격리 기능을 비활성화합니다.
    # 성능 향상을 위해 사이트 간 격리를 비활성화합니다. 보안 기능을 일부 희생할 수 있습니다.
    chrome_options.add_argument("--disable-site-isolation-trials")

    # 네트워크 서비스 기능을 비활성화합니다.
    # 네트워크 서비스 관련 기능이 성능을 저하시키는 경우 이를 비활성화하여 성능을 최적화할 수 있습니다.
    chrome_options.add_argument("--disable-features=NetworkService")

    # Viz Display Compositor 기능을 비활성화합니다.
    # 렌더링 관련 성능 문제를 해결하기 위해 사용합니다. 특정 환경에서 성능 향상이 있을 수 있습니다.
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")


    # chrome_options.add_argument(f"user-data-dir=./chromeprofile_{os.getpid()}")
    chrome_options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    service = ChromeService(executable_path="C:/workspace/instahelp_web/resources/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(index, username, password, login_url):
    driver = setup_driver()
    driver.get(login_url)

    # try:
    #     # Replace the below lines with your login logic
    #     username_field = driver.find_element(By.NAME, "username")
    #     password_field = driver.find_element(By.NAME, "password")
    #     login_button = driver.find_element(By.NAME, "login")
    #
    #     username_field.send_keys(username)
    #     password_field.send_keys(password)
    #     login_button.click()
    #
    #     # Wait for login to complete
    #     time.sleep(5)  # Adjust the sleep time as needed
    #
    #     print(f"Account {index} logged in successfully")
    # except Exception as e:
    #     print(f"Account {index} failed to login: {str(e)}")
    # finally:
    #     driver.quit()
    driver.quit()


def measure_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert bytes to MB


def sample_memory_usage_per_instance():
    driver = setup_driver()
    time.sleep(2)  # Allow some time for the browser to fully load
    memory_usage = measure_memory_usage()
    driver.quit()
    return memory_usage


def get_optimal_max_workers():
    cpu_count = os.cpu_count()
    print(f"개발서버 CPU 코어 개수: {cpu_count}")

    total_memory = psutil.virtual_memory().total
    total_memory_gb = total_memory / (1024 ** 3)
    print(f"개발서버 메모리: {total_memory_gb:.2f} GB")

    memory_usage_per_instance = sample_memory_usage_per_instance()
    print(f"인스턴스당 메모리 사용량: {memory_usage_per_instance:.2f} MB")

    # Calculate max workers based on memory usage per instance
    max_memory_based_workers = total_memory // (memory_usage_per_instance * 1024 * 1024)

    # Calculate max workers based on both CPU and memory constraints
    optimal_max_workers = min(cpu_count * 2, max_memory_based_workers)

    # Ensure at least 1 worker and at most 300 workers
    return max(1, min(300, optimal_max_workers))


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes} 분 {seconds} 초"


def main():
    start_time = time.time()
    active_accounts = [
        "user2|password2",
        "user2|password2",
        "user2|password2",
    ]

    login_url = "https://www.instagram.com/"  # Replace with your login URL

    initial_memory_usage = measure_memory_usage()
    print(f"초기 메모리 사용량: {initial_memory_usage:.2f} MB")

    max_workers = get_optimal_max_workers()
    print(f"최대 작업 인스턴스: {max_workers}")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(
            login,
            index,
            account.split('|')[0],
            account.split('|')[1],
            login_url
        ) for index, account in enumerate(active_accounts)]

        for future in futures:
            future.result()  # Get the result of the future (if needed)


    # Measure final memory usage
    final_memory_usage = measure_memory_usage()
    print(f"마지막 메모리 사용량: {final_memory_usage:.2f} MB")

    # Calculate the average memory usage per instance
    average_memory_usage_per_instance = (final_memory_usage - initial_memory_usage) / len(active_accounts)
    print(f"인스턴스당 평균 메모리 사용량: {average_memory_usage_per_instance:.2f} MB")

    end_time = time.time()
    elapsed_time = timedelta(seconds=end_time - start_time)
    formatted_time = format_timedelta(elapsed_time)
    print(f"걸린시간: {formatted_time} 계정개수 {len(active_accounts)}")



if __name__ == '__main__':
    main()
