from selenium import webdriver


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
driver.switch_to.window(tab1_handle)
driver.execute_script("""
    var proxy = {
        'proxyType': 'manual',
        'httpProxy': 'http://121.126.88.103:56870',
        'ftpProxy': 'http://121.126.88.103:5687',
        'sslProxy': 'http://121.126.88.103:5687',
        'noProxy': ''
    };
    arguments[0].capabilities.setCapability('proxy', proxy);
""", driver.current_window_handle)

# Set proxy for tab 2
driver.switch_to.window(tab2_handle)
driver.execute_script("""
    var proxy = {
        'proxyType': 'manual',
        'httpProxy': 'http://124.198.0.25:5944',
        'ftpProxy': 'http://124.198.0.25:5944',
        'sslProxy': 'http://124.198.0.25:5944',
        'noProxy': ''
    };
    arguments[0].capabilities.setCapability('proxy', proxy);
""", driver.current_window_handle)

# Navigate to different URLs in each tab
driver.switch_to.window(tab1_handle)
driver.get("https://ip-check.net/")

driver.switch_to.window(tab2_handle)
driver.get("https://ip-check.net/")