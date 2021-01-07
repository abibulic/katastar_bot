import argparse

def get_args():

    parser = argparse.ArgumentParser(description='Collect data')

    # Site parameters
    parser.add_argument('--site', type=str, default='katastar',
                        help='Select a site from which to collect the data')
    parser.add_argument('--save_img', type=bool, default=True,
                        help='Collect images')

    # Browser settings
    parser.add_argument('--proxy_address', type=str, default=None,
                        help='Proxy address')
    parser.add_argument('--proxy_port', type=str, default=None,
                        help='Proxy port')
    parser.add_argument('--proxy_username', type=str, default=None,
                        help='Proxy username')
    parser.add_argument('--proxy_password', type=str, default=None,
                        help='Proxy password')
    parser.add_argument('--headless_browser', type=bool, default=False,
                        help='Run browser in headless mode')
    parser.add_argument('--browser_profile_path', type=str, default=None,
                        help='Browser profile path')
    parser.add_argument('--disable_image_load', type=bool, default=False,
                        help='Disable image load. If True, images will not load')
    parser.add_argument('--page_delay', type=int, default=10,
                        help='How long to wait response from page')
    parser.add_argument('--geckodriver_path', type=str, default='./assets/geckodriver.exe',
                        help='Path to gecko driver')    
    parser.add_argument('--firefox_binary', type=str, default='C:/Users/aleks/AppData/Local/Mozilla Firefox/firefox.exe',
                        help='Path to firefox binary')   

    # Action setting
    parser.add_argument('--get_links', type=bool, default=False,
                        help='Collect all links first')
    parser.add_argument('--get_data', type=bool, default=True,
                        help='Collect data from links')   
    parser.add_argument('--get_only_new_data', type=bool, default=True,
                        help='Collect only new data from links')   

    # Data settings  
    parser.add_argument('--link_path', type=str, default='./data/links/',
                        help='Path to link collection')
    parser.add_argument('--data_path', type=str, default='./data/dataframes/',
                        help='Path to data collection')   
    parser.add_argument('--img_path', type=str, default='./data/images/',
                        help='Path to image collection')                                        


    return parser.parse_args(args=[])