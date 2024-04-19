import time

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

option = Options()
# option.add_argument("--proxy-server=socks5://127.0.0.1:9050")
option.add_argument("--proxy-server=http://49.254.239.34:6813")
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=option
)
driver.get('https://dnsleaktest.com/')
time.sleep(30)