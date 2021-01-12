import io
import os
import cv2
import time
import math
import random
import urllib
import base64
import numpy as np
import pandas as pd
from PIL import Image
from ast import literal_eval
from datetime import datetime

# from set_browser import set_selenium_local_session

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import WebDriverException

from arcgis.gis import GIS
from arcgis.geocoding import geocode, reverse_geocode
from arcgis.geometry import Point


# def set_browser(args):
#     browser = set_selenium_local_session(
#             args.proxy_address,
#             args.proxy_port,
#             args.proxy_username,
#             args.proxy_password,
#             args.headless_browser,
#             args.browser_profile_path,
#             args.disable_image_load,
#             args.page_delay,
#             args.geckodriver_path
#         )
    
#     return browser

def list_files(root_dir, ext='.txt'):
    file_list = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(ext):
                file_list.append(os.path.join(root, file).replace("\\","/"))
    return file_list


def merc(Coords):
    Coordinates = literal_eval(Coords)    
    lat = Coordinates[0]
    lon = Coordinates[1]
    
    r_major = 6378137.000
    x = r_major * math.radians(lon)
    scale = x/lon
    y = 180.0/math.pi * math.log(math.tan(math.pi/4.0 + lat * (math.pi/180.0)/2.0)) * scale    
    return (x, y)

def stringToRGB(base64_string):
    imgdata = base64.b64decode(str(base64_string))
    image = Image.open(io.BytesIO(imgdata))
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)

def set_browser(args):
    geoDisabled = webdriver.FirefoxOptions()
    geoDisabled.set_preference("geo.enabled", False)
    return webdriver.Firefox(executable_path=args.geckodriver_path, firefox_binary=args.firefox_binary, options=geoDisabled)

def find_border(img, lower_colour, upper_colour):
    lower = np.array((lower_colour), dtype="uint8")
    upper = np.array((upper_colour), dtype="uint8")
    mask = cv2.inRange(img, lower, upper)
    output = cv2.bitwise_and(img, img, mask=mask)
    output[output > 0] = 255
    return output

def calc_offset(size, x, y):
    y_center = size[0]/2
    x_center = size[1]/2
    x_offset = x - math.ceil(x_center)
    y_offset = y - math.ceil(y_center)
    return x_offset, y_offset

def wheel_element(element, deltaY = 120, offsetX = 0, offsetY = 0):
  error = element._parent.execute_script("""
    var element = arguments[0];
    var deltaY = arguments[1];
    var box = element.getBoundingClientRect();
    var clientX = box.left + (arguments[2] || box.width / 2);
    var clientY = box.top + (arguments[3] || box.height / 2);
    var target = element.ownerDocument.elementFromPoint(clientX, clientY);

    for (var e = target; e; e = e.parentElement) {
      if (e === element) {
        target.dispatchEvent(new MouseEvent('mouseover', {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY}));
        target.dispatchEvent(new MouseEvent('mousemove', {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY}));
        target.dispatchEvent(new WheelEvent('wheel',     {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY, deltaY: deltaY}));
        return;
      }
    }    
    return "Element is not interactable";
    """, element, deltaY, offsetX, offsetY)
  if error:
    raise WebDriverException(error)

def find_log_lat(mapa, img_shape, browser):
    x_corner = img_shape[1]/2
    y_corner = img_shape[0]/2

    mouse_position =  browser.find_elements_by_id('mousePositionId')[0]

    ac = ActionChains(browser)
    ac.move_to_element(mapa).move_by_offset(-x_corner, -y_corner).perform()
    position1 =  mouse_position.text.split(' ')[1:]
    ac.move_to_element(mapa).move_by_offset(x_corner-1, y_corner-1).perform()
    position2 =  mouse_position.text.split(' ')[1:]

    long1 = float(position1[0][:-1])
    lat2 = float(position1[1])

    long2 = float(position2[0][:-1])
    lat1 = float(position2[1])
    return long1, lat1, long2, lat2

def accept_cookies(browser):
    flag = True
    while flag:
        #cookies = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'cookie-layout')))
        cookies = browser.find_elements_by_class_name('cookie-layout')[0]
        if cookies.rect['height'] != 0:
            flag = False
    #ac = ActionChains(browser)
    ActionChains(browser).move_to_element(cookies).move_by_offset(860, 0).click().perform()

def select_region(browser):
    # klikni na "Pronađi adrese"
    #ac = ActionChains(browser)
    central_image = browser.find_elements_by_class_name('tp-kbimg-wrap')
    ActionChains(browser).move_to_element(central_image[0]).move_by_offset(0, 620).click().perform()

    # nađi zagreb na mapi
    ac = ActionChains(browser)
    dropdown = browser.find_elements_by_class_name('ui-inputgroup')
    ac.move_to_element(dropdown[2]).move_by_offset(132, 0).click().perform()
    time.sleep(1)
    ac.move_to_element(dropdown[2]).move_by_offset(0, 148).click().perform()
    time.sleep(1)
    ac.move_to_element(dropdown[2]).move_by_offset(172, 0).click().perform()
    time.sleep(10)

def zoom_in(browser, mapa, x_offset, y_offset):
    # zoom in
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    time.sleep(5)
    # zoom out a little bit
    wheel_element(mapa, 120)
    wheel_element(mapa, 120)
    time.sleep(5)  

def colect_data(f, browser):
    line = str()

    prvi_list_pdataka = browser.find_elements_by_class_name('m-widget28__tab-item')[3:8]
    for i, row in enumerate(prvi_list_pdataka):
        txt = row.text
        if len(txt):
            txt = txt.split('\n')[1]
            if i == 4:
                txt = txt[:-11]
                line += txt
                line += ';'
            else:
                line += txt
                line += ';'
        #print(txt) 

    drugi_list_pdataka = browser.find_elements_by_class_name('table_text')
    for row in drugi_list_pdataka:  
        txt =  row.get_attribute("innerHTML")
        if len(txt):
            line += txt
            line += ','
        #print(txt)
    line = line[:-1]+';'

    treci_list_pdataka = browser.find_elements_by_class_name('m-widget13__text')
    wait_flag = False
    write_flag = False
    w_count = 0
    for i, row in enumerate(treci_list_pdataka):
        txt =  row.get_attribute("innerHTML") 
        if len(txt):
            if w_count == 0:
                try:
                    txt = int(txt)
                    w_count = 4
                    write_flag = True
                except:
                    w_count = 3
                    wait_flag = True
            if w_count != 0 and write_flag == True:
                line += str(txt)
                line += ','
                w_count -= 1

            elif w_count != 0 and wait_flag == True:
                w_count -= 1
            
        #print(txt)
    line = line[:-1]+'\n'
    f.write(line)

def move_camera(browser,
                count_moves_x, 
                count_moves_y, 
                move_right,
                move_y,
                pix_long,
                mapa,
                map_img,
                long1, 
                lat1, 
                long2, 
                lat2, ):

    step = 10
    diff = 10000

    if count_moves_x%10 == 0 and count_moves_x >= 0 and move_y:
        #ActionChains(browser).move_to_element(mapa).move_by_offset(0, y_move-1).click_and_hold().move_by_offset(0, -y_move).release().perform()
        while diff > 1:
            temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
            diff = temp_lat22 - lat1
            if diff > 10:
                step = int(diff/(2*pix_long))
            ActionChains(browser).move_to_element(mapa).move_by_offset(0, step-1).click_and_hold().move_by_offset(0, -step).release().perform()
            print(diff)
        move_y = False
        count_moves_y += 1
        if move_right:
            move_right = False
        else:
            move_right= True

    elif move_right:
        #ActionChains(browser).move_to_element(mapa).move_by_offset(x_move-1, 0).click_and_hold().move_by_offset(-x_move, 0).release().perform()
        while diff > 1:
            temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
            diff = long2 - temp_long11
            if diff > 10:
                step = int(diff/(2*pix_long))
            ActionChains(browser).move_to_element(mapa).move_by_offset(step-1, 0).click_and_hold().move_by_offset(-step, 0).release().perform()
            print(diff)
        count_moves_x += 1
        move_y = True

    else:
        #ActionChains(browser).move_to_element(mapa).move_by_offset(-x_move, 0).click_and_hold().move_by_offset(x_move-1, 0).release().perform()
        while diff > 1:
            temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
            diff = temp_long22 - long1
            if diff > 10:
                step = int(diff/(2*pix_long))
            ActionChains(browser).move_to_element(mapa).move_by_offset(-step, 0).click_and_hold().move_by_offset(step-1, 0).release().perform()
            print(diff)
        count_moves_x += 1
        move_y = True

    time.sleep(2)

    return count_moves_x, count_moves_y, move_right, move_y
    
def do_the_job(args, date, link):
    f = open(f'{args.data_path}{date}.txt', 'w+')
    line = 'Katastarska općina;Broj katastarske čestice;Adresa katastarske čestice;Površina katastarske čestice/m2;Posjedovni list;Način uporabe i zgrade + Površina/m2;Posjedovni list + Udio + Ime i prezime/Naziv + Adresa\n'
    
    count_moves_x = 0
    count_moves_y = 0
    move_right = True
    move_y = True

    if args.save_img:
        img_dir = f'{args.img_path}{date}'
        try:
            os.mkdir(img_dir)
        except OSError:
            print(f'Creation of the directory {img_dir} failed')

        img_dir = f'{args.img_path}{date}/img/'
        try:  
            os.mkdir(img_dir)
        except OSError:
            print(f'Creation of the directory {img_dir} failed')
    
    browser = set_browser(args)
    browser.set_page_load_timeout(1)
    browser.maximize_window()
    browser.implicitly_wait(30)

    try:
        browser.get(link)
        # html = browser.find_element_by_tag_name('html')
        # html.send_keys(Keys.END)
    except OSError:
        print(f'Failed to open link: {link}!')

    # prihvati kolačiće
    try:
        accept_cookies(browser)
    except OSError:
        print(f'Failed to accept cookies!')

    # nađi zagreb na mapi
    try:
        select_region(browser)
    except OSError:
        print(f'Failed to select region!')

    # pozicioniranje na mapi
    try:
        mapa = browser.find_elements_by_class_name('ol-layer')[0]
    except OSError:
        print(f'Can not find map on the website!')

    map_img = stringToRGB(mapa.screenshot_as_base64)
    
    #TODO test
    #map_img = cv2.imread('mapa.png')
    #long_orig1, lat_orig1, long_orig2, lat_orig2 = find_log_lat(mapa, map_img.shape, browser)
    #bbox_orig = abs(long_orig1-long_orig2)*abs(lat_orig1-lat_orig2)

    # filtriranje crvene boje granice zagreba
    # lower = [80, 90, 180]
    # upper = [85, 96, 190]
    # mask_img = find_border(map_img, lower, upper)
    # mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)

    # odaberi roi rucno
    mask_img = cv2.imread('roi_mask.png')
    mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)

    i, j = np.where(mask_img == 255)

    x_offset, y_offset = calc_offset(mask_img.shape, j[0], i[0])

    # zoom in
    zoom_in(browser, mapa, x_offset, y_offset)

    #TODO test
    # long1 = 468752.19
    # lat2 = 5092446.7

    # long2 = 471029.74
    # lat1 = 5091376.62

    # pokreni drugi browser
    browser2 = set_browser(args)
    browser2.set_page_load_timeout(1)
    browser2.maximize_window()
    browser2.implicitly_wait(30)

    # konfiguracijske varijable za pomicanje po mapi
    x_move = int(mask_img.shape[1]/2)
    y_move = int(mask_img.shape[0]/2)
    pix_long = 2277.5500000000466/1808
 
    while count_moves_x*count_moves_y < 100:

        wheel_element(mapa, 120)
        time.sleep(5)

        # nađi longitude/latitude sa slike
        long1, lat1, long2, lat2 = find_log_lat(mapa, map_img.shape, browser)
        #bbox = abs(long1 - long2)*abs(lat1 - lat2)

        #scale = math.sqrt(bbox_orig/bbox)

        link2 = f'https://oss.uredjenazemlja.hr/OssWebServices/wms?token=7effb6395af73ee111123d3d1317471357a1f012d4df977d3ab05ebdc184a46e&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=image%2Fpng8&TRANSPARENT=true&LAYERS=oss%3ABZP_CESTICE%2Coss%3ABZP_CESTICE%2Coss%3ABZP_ZGRADE&STYLES=jis_cestice_kathr%2Cjis_cestice_nazivi_kathr%2C&tiled=false&ratio=2&serverType=geoserver&CRS=EPSG%3A3765&WIDTH=2713&HEIGHT=1280&BBOX={long1}%2C{lat1}%2C{long2}%2C{lat2}'
        try:
            browser2.get(link2)
        except OSError:
            print(f'Failed to open link: {link}!')
            pass
            #break

        time.sleep(5)
        try:
            layout_img_element = browser2.find_element_by_tag_name("img")
        except OSError:
            print(f'Can not find image in the second browser!')
            pass

        #TODO test
        #layout_img = cv2.imread('layout_img.png')

        # slika bez granica
        lower = [220, 220, 220]
        upper = [235, 235, 235]
        layout_img = stringToRGB(layout_img_element.screenshot_as_base64)
        layout_img = find_border(layout_img, lower, upper)

        layout_img = cv2.cvtColor(layout_img, cv2.COLOR_BGR2GRAY)
        layout_img = cv2.resize(layout_img, (0,0),  fx=1.24, fy=1.24)
        layout_img = layout_img[138:-134, 287:-286]
        #layout_img = cv2.resize(layout_img, (map_img.shape[1],map_img.shape[0])) 
        

        #TODO test
        #kernel_map_img = cv2.imread('kernel_map_img.png')

        wheel_element(mapa, -120)
        time.sleep(5)
        
        long1, lat1, long2, lat2 = find_log_lat(mapa, map_img.shape, browser)

        # zoomirana slika granice zagreba
        #kernel_map_img = stringToRGB(mapa.screenshot_as_base64)
        #cv2.imwrite("test2.png", kernel_map_img)

        # lower = [80, 90, 180]
        # upper = [85, 96, 190]
        # kernel_mask_border = find_border(kernel_map_img, lower, upper)
        # kernel_mask_border = cv2.cvtColor(kernel_mask_border, cv2.COLOR_BGR2GRAY)
        # # fill image if there is border
        # if np.any(kernel_mask_border):
        #     h, w = kernel_mask_border.shape[:2]
        #     mask = np.zeros((h+2, w+2), np.uint8)
        #     cv2.floodFill(kernel_mask_border, mask, (0,0), 255)
        #     kernel_mask_border = cv2.bitwise_not(kernel_mask_border)
        #     kernel_mask_border[kernel_mask_border == 255] = 1

        # lower = [20, 130, 90]
        # upper = [30, 140, 100]
        # kernel_mask2 = find_border(kernel_map_img, lower, upper)
        # kernel_mask2 = cv2.cvtColor(kernel_mask2, cv2.COLOR_BGR2GRAY)
        
        # uzmi trenutnu mapu
        # lower_kernel = [66, 100, 134]
        # upper_kernel = [72, 146, 210]
        # kernel_mask3 = find_border(kernel_map_img, lower_kernel, upper_kernel)
        # kernel_mask3 = cv2.cvtColor(kernel_mask3, cv2.COLOR_BGR2GRAY)

        #kernel_mask = kernel_mask_border*layout_img
        kernel_mask = layout_img
        kernel_mask[kernel_mask < 255] = 0
        
        #loop while there is still some white pixel
        h, w = kernel_mask.shape[:2]
        mask = np.zeros((h+2, w+2), np.uint8)
        while np.any(kernel_mask):
            i, j = np.where(kernel_mask == 255)
            x_offset, y_offset = calc_offset(mask_img.shape, j[0], i[0])
            ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset+2, y_offset+2).click().perform()
            time.sleep(1)
            cv2.floodFill(kernel_mask, mask, (j[0],i[0]), 0)
            cv2.imshow("kernel_mask", kernel_mask)
            cv2.waitKey(2)

            # colect data
            try:
                colect_data(f, browser)
            except OSError:
                print(f'Failed to collect data!')

            #close data dialog
            try:
                #close_element = browser.find_element_by_class_name('m-portlet__nav-link')
                close_element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'm-portlet__nav-link')))
            except OSError:
                print(f'Can not find close button on the website!')
            ActionChains(browser).move_to_element(close_element).move_by_offset(118, 5).click().perform()
        # move camera
        try:
            count_moves_x, count_moves_y, move_right, move_y = move_camera(browser,
                                                                        count_moves_x, 
                                                                        count_moves_y, 
                                                                        move_right,
                                                                        move_y, 
                                                                        pix_long,
                                                                        mapa,
                                                                        map_img,
                                                                        long1, 
                                                                        lat1, 
                                                                        long2, 
                                                                        lat2)
        except OSError:
            print(f'Camera move was unsuccessful!')

        #TODO izbrisat ako funkcija funkcionira
        # if count_moves_x%10 == 0 and count_moves_x >= 0 and move_y:
        #     #ActionChains(browser).move_to_element(mapa).move_by_offset(0, y_move-1).click_and_hold().move_by_offset(0, -y_move).release().perform()
        #     while diff > 1:
        #         temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
        #         diff = temp_lat22 - lat1
        #         if diff > 10:
        #             step = int(diff/(2*pix_long))
        #         ActionChains(browser).move_to_element(mapa).move_by_offset(0, step-1).click_and_hold().move_by_offset(0, -step).release().perform()
        #         print(diff)

        #     diff = 10000
        #     move_y = False
        #     count_moves_y += 1
        #     if move_right:
        #         move_right = False
        #     else:
        #         move_right= True
        # elif move_right:
        #     #ActionChains(browser).move_to_element(mapa).move_by_offset(x_move-1, 0).click_and_hold().move_by_offset(-x_move, 0).release().perform()
        #     while diff > 1:
        #         temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
        #         diff = long2 - temp_long11
        #         if diff > 10:
        #             step = int(diff/(2*pix_long))
        #         ActionChains(browser).move_to_element(mapa).move_by_offset(step-1, 0).click_and_hold().move_by_offset(-step, 0).release().perform()
        #         print(diff)
        
        #     diff = 10000
        #     count_moves_x += 1
        #     move_y = True
        # else:
        #     #ActionChains(browser).move_to_element(mapa).move_by_offset(-x_move, 0).click_and_hold().move_by_offset(x_move-1, 0).release().perform()
        #     while diff > 1:
        #         temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
        #         diff = temp_long22 - long1
        #         if diff > 10:
        #             step = int(diff/(2*pix_long))
        #         ActionChains(browser).move_to_element(mapa).move_by_offset(-step, 0).click_and_hold().move_by_offset(step-1, 0).release().perform()
        #         print(diff)
        #     diff = 10000
        #     count_moves_x += 1
        #     move_y = True
        # time.sleep(2)

    f.close()     
    browser.quit()
    browser2.quit()


    # cv2.imwrite("kernel_map_img.png", kernel_map_img)
    # cv2.imwrite("kernel_mask.png", kernel_mask)
    # cv2.imwrite("layout_img.png", layout_img)

    # cv2.imshow("kernel_map_img", kernel_map_img)
    # cv2.imshow("kernel_mask_border", kernel_mask_border)
    # cv2.imshow("kernel_mask", kernel_mask)
    # cv2.imshow("layout_img", layout_img)
    # cv2.waitKey(0)

def clean_data(data, data_categories):
    data = data.drop_duplicates()
    #data = data.reset_index()

    for c in data_categories:
        if c != 'price_per_m2':
            if c == 'num_rooms':
                data.loc[data[c] == 'Garsonijera', c] = 0
                data.loc[data[c] == '5+', c] = 5
            else:
                data.loc[data[c] == 'None', c] = 0

    convert_dict = {'price': float, 
                    'indoor_area': float, 
                    'num_rooms': int, 
                    'netto_area': float,
                    'build_data': int, 
                    'last_renovation': int, 
                } 
    data = data.astype(convert_dict) 

    data.loc[data.energy_class == 'A+', 'energy_class'] = 8
    data.loc[data.energy_class == 'A', 'energy_class'] = 7
    data.loc[data.energy_class == 'B', 'energy_class'] = 6
    data.loc[data.energy_class == 'C', 'energy_class'] = 5
    data.loc[data.energy_class == 'D', 'energy_class'] = 4
    data.loc[data.energy_class == 'E', 'energy_class'] = 3
    data.loc[data.energy_class == 'F', 'energy_class'] = 2
    data.loc[data.energy_class == 'G', 'energy_class'] = 1

    return data

def save_pandas(args, date):
    data_categories = ['price', 
            'indoor_area', 
            'price_per_m2',
            'num_rooms',
            'netto_area',
            'build_data',
            'last_renovation',
            'energy_class',
            ]

    data = pd.read_csv(f'{args.data_path}{date}.txt',
                   names=['img_id',
                        'link',
                        'price',
                        'indoor_area',
                        'num_rooms', 
                        'location1',
                        'street',
                        'ap_type',
                        'num_floors',
                        'floor',
                        'building_floors',
                        'netto_area',
                        'build_data',
                        'last_renovation',
                        'furnished',
                        'parking_lots',
                        'balcony',
                        'energy_class',
                        'location2', 
                        'tel',
                        'agency',
                        'post_time',
                        'exparation_date',
                        'time_shown',
                        'latitude',
                        'longitude',
                        'x',
                        'y'],sep=';', encoding='ansi')

    data['price_per_m2'] = round(data.price/data.indoor_area, 2)

    data = clean_data(data, data_categories)

    data.to_csv(f'{args.data_path}{date}.csv', index=False)

def run(args, date, last_date, link):
    do_the_job(args, date, link)
    save_pandas(args, date)
        







