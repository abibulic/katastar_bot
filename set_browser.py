# general libs
import os
import zipfile
import shutil
from os.path import sep

# selenium
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as Firefox_Options
from selenium.webdriver import Remote
from webdriverdownloader import GeckoDriverDownloader
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


def get_geckodriver():
    # prefer using geckodriver from path
    gecko_path = shutil.which("geckodriver") or shutil.which("geckodriver.exe")
    if gecko_path:
        return gecko_path

    asset_path = "./assets/"
    gdd = GeckoDriverDownloader(asset_path, asset_path)
    # skips download if already downloaded
    #bin_path, sym_path = gdd.download_and_install()
    bin_path, sym_path = tuple(['C:\\Users\\abibulic\\InstaPy\\assets\\gecko\\v0.25.0\\geckodriver-v0.25.0-win64\\geckodriver.exe',
                                'C:\\Users\\abibulic\\InstaPy\\assets\\geckodriver.exe'])
    return sym_path

def create_firefox_extension():
    ext_path = os.path.abspath(os.path.dirname(__file__) + sep + "firefox_extension")
    # safe into assets folder
    zip_file = "D:\\WORK\\PROJECTS\\house_browser" + sep + "extension.xpi"

    files = ["manifest.json", "content.js", "arrive.js"]
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED, False) as zipf:
        for file in files:
            zipf.write(ext_path + sep + file, file)

    return zip_file


def set_selenium_local_session(
    proxy_address,
    proxy_port,
    proxy_username,
    proxy_password,
    headless_browser,
    browser_profile_path,
    disable_image_load,
    page_delay,
    geckodriver_path,
):
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) FxiOS/18.1 Mobile/16B92 Safari/605.1.15"
    )

    firefox_options = Firefox_Options()
    firefox_options.page_load_strategy = 'none'

    if headless_browser:
        firefox_options.add_argument("-headless")

    if browser_profile_path is not None:
        firefox_profile = webdriver.FirefoxProfile(browser_profile_path)
    else:
        firefox_profile = webdriver.FirefoxProfile()

    # set English language    
    firefox_profile.set_preference("intl.accept_languages", "en-US")
    firefox_profile.set_preference("general.useragent.override", user_agent)

    if disable_image_load:
        # permissions.default.image = 2: Disable images load,
        # this setting can improve pageload & save bandwidth
        firefox_profile.set_preference("permissions.default.image", 2)

    if proxy_address and proxy_port:
        firefox_profile.set_preference("network.proxy.type", 1)
        firefox_profile.set_preference("network.proxy.http", proxy_address)
        firefox_profile.set_preference("network.proxy.http_port", proxy_port)
        firefox_profile.set_preference("network.proxy.ssl", proxy_address)
        firefox_profile.set_preference("network.proxy.ssl_port", proxy_port)

    # mute audio
    firefox_profile.set_preference("media.volume_scale", "0.0")

    # prefer user path before downloaded one
    driver_path = geckodriver_path or get_geckodriver()
    binary = FirefoxBinary('C:/Users/aleks/AppData/Local/Mozilla Firefox/firefox.exe')
    browser = webdriver.Firefox(
        firefox_profile=firefox_profile,
        executable_path=driver_path,
        firefox_binary=binary,
        options=firefox_options,
    )

    # add extenions to hide selenium
    browser.install_addon(create_firefox_extension(), temporary=True)

    browser.implicitly_wait(page_delay)

    return browser