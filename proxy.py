from seleniumwire import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('start-maximized')

# 첫 번째 탭에 사용할 프록시 설정
proxy_tab1 = {
    'http': 'http://127.0.0.1:8080'
}

# 두 번째 탭에 사용할 프록시 설정
proxy_tab2 = {
    'http': 'http://127.0.0.1:8080'
}

# Selenium Wire 옵션 설정
sw_options = {
    'proxy': proxy_tab1  # 기본적으로 첫 번째 탭에 프록시 설정
}

# 첫 번째 탭에 대한 WebDriver 생성
driver = webdriver.Chrome(
    options=chrome_options,
    seleniumwire_options=sw_options,
)

# 첫 번째 탭에서 웹페이지 열기
driver.get("https://naver.com")




# 두 번째 탭 생성 후 두 번째 탭에 대한 프록시 설정 변경
driver.execute_script("window.open()")
driver.switch_to.window(driver.window_handles[-1])  # 두 번째 탭으로 전환

sw_options['proxy'] = proxy_tab2  # 두 번째 탭에 대한 프록시 설정으로 변경
driver = webdriver.Chrome(
    options=chrome_options,
    seleniumwire_options=sw_options,
)

# 두 번째 탭에서 웹페이지 열기
driver.get("https://naver.com")
