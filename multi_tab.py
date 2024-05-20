from selenium import webdriver

# Define proxies
proxy1 = {"httpProxy": "http://proxy1:8080", "httpsProxy": "http://proxy1:8080"}
proxy2 = {"httpProxy": "http://proxy2:8080", "httpsProxy": "http://proxy2:8080"}

# Create the driver
driver = webdriver.Chrome()

# Open new tabs
driver.get("https://naver.com")  # Open a starting page
driver.execute_script("window.open('https://google.com')")
driver.execute_script("window.open('https://google.com')")

# Get the window handles for each tab
tab1_handle = driver.window_handles[1]
tab2_handle = driver.window_handles[2]

# Set proxy for tab 1
driver.switch_to_window(tab1_handle)
driver.execute_script("""
    var proxy = {
        'proxyType': 'manual',
        'httpProxy': 'http://proxy1:8080',
        'ftpProxy': 'http://proxy1:8080',
        'sslProxy': 'http://proxy1:8080',
        'noProxy': ''
    };
    arguments[0].capabilities.setCapability('proxy', proxy);
""", driver.current_window_handle)

# Set proxy for tab 2
driver.switch_to_window(tab2_handle)
driver.execute_script("""
    var proxy = {
        'proxyType': 'manual',
        'httpProxy': 'http://proxy2:8080',
        'ftpProxy': 'http://proxy2:8080',
        'sslProxy': 'http://proxy2:8080',
        'noProxy': ''
    };
    arguments[0].capabilities.setCapability('proxy', proxy);
""", driver.current_window_handle)

# Navigate to different URLs in each tab
driver.switch_to_window(tab1_handle)
driver.get("https://ip-check.net/")

driver.switch_to_window(tab2_handle)
driver.get("https://ip-check.net/")