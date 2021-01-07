from set_browser import set_selenium_local_session

def set_browser():
    #settings
    proxy_address = None
    proxy_port = None
    proxy_username = None
    proxy_password = None
    headless_browser = False
    browser_profile_path = None
    disable_image_load = False
    page_delay = 10
    geckodriver_path = './assets/geckodriver.exe'

    browser = set_selenium_local_session(
            proxy_address,
            proxy_port,
            proxy_username,
            proxy_password,
            headless_browser,
            browser_profile_path,
            disable_image_load,
            page_delay,
            geckodriver_path
        )
    
    return browser