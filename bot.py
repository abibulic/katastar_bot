import io
import os
import cv2
import sys
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

def find_lon_lat(mapa, img_shape, browser):
    x_corner = img_shape[1]/2
    y_corner = img_shape[0]/2

    mouse_position =  browser.find_elements_by_id('mousePositionId')[0]

    ac = ActionChains(browser)
    ac.move_to_element(mapa).move_by_offset(-x_corner, -y_corner).perform()
    position1 =  mouse_position.text.split(' ')[1:]
    ac.move_to_element(mapa).move_by_offset(x_corner-1, y_corner-1).perform()
    position2 =  mouse_position.text.split(' ')[1:]

    lon1 = float(position1[0][:-1])
    lat2 = float(position1[1])

    lon2 = float(position2[0][:-1])
    lat1 = float(position2[1])
    return lon1, lat1, lon2, lat2

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

    #prvi_list_podataka = WebDriverWait(browser, 10).until(EC.element_to_be_selected((By.CLASS_NAME,'m-widget28__tab-item')))#[3:8]
    prvi_list_podataka = browser.find_elements_by_class_name('m-widget28__tab-item')[3:8]
    for i, row in enumerate(prvi_list_podataka):
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

    #drugi_list_podataka = WebDriverWait(browser, 10).until(EC.element_to_be_selected(By.CLASS_NAME('table_text')))
    drugi_list_podataka = browser.find_elements_by_class_name('table_text')
    for row in drugi_list_podataka:  
        txt =  row.get_attribute("innerHTML")
        if len(txt):
            line += txt
            line += ','
        #print(txt)
    line = line[:-1]+';'

    #treci_list_podataka = WebDriverWait(browser, 10).until(EC.element_to_be_selected((By.CLASS_NAME,'m-widget13__text')))
    treci_list_podataka = browser.find_elements_by_class_name('m-widget13__text')
    wait_flag = False
    write_flag = False
    w_count = 0
    for i, row in enumerate(treci_list_podataka):
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
                lat2,
                times_to_move_x,
                times_to_move_y):

    step = 10
    diff = 10000
    counter = 0 #mora doc do cilja u manje od 20 koraka
    if count_moves_x%times_to_move_x == 0 and count_moves_x >= 0 and move_y:
        print('Move down')
        #ActionChains(browser).move_to_element(mapa).move_by_offset(0, y_move-1).click_and_hold().move_by_offset(0, -y_move).release().perform()
        while diff > 1:
            if counter >= 20:
                print('Can not move!!')
                break
            else:    
                temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
                diff = temp_lat22 - lat1
                if diff > 10:
                    step = int(diff/(2*pix_long))
                ActionChains(browser).move_to_element(mapa).move_by_offset(0, step-1).click_and_hold().move_by_offset(0, -step).release().perform()
                counter += 1
                #print(diff)
        move_y = False
        count_moves_y += 1
        if move_right:
            move_right = False
        else:
            move_right= True

    elif move_right:
        print('Move right')
        #ActionChains(browser).move_to_element(mapa).move_by_offset(x_move-1, 0).click_and_hold().move_by_offset(-x_move, 0).release().perform()
        while diff > 1:
            if counter >= 20:
                print('Can not move!!')
                break
            else:
                temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
                diff = long2 - temp_long11
                if diff > 10:
                    step = int(diff/(2*pix_long))
                ActionChains(browser).move_to_element(mapa).move_by_offset(step-1, 0).click_and_hold().move_by_offset(-step, 0).release().perform()
                counter += 1
                #print(diff)
        count_moves_x += 1
        move_y = True

    else:
        print('Move left')
        #ActionChains(browser).move_to_element(mapa).move_by_offset(-x_move, 0).click_and_hold().move_by_offset(x_move-1, 0).release().perform()
        while diff > 1:
            if counter >= 20:
                print('Can not move!!')
                break
            else:
                temp_long11, temp_lat11, temp_long22, temp_lat22 = find_log_lat(mapa, map_img.shape, browser)
                diff = temp_long22 - long1
                if diff > 10:
                    step = int(diff/(2*pix_long))
                ActionChains(browser).move_to_element(mapa).move_by_offset(-step, 0).click_and_hold().move_by_offset(step-1, 0).release().perform()
                counter += 1
                #print(diff)
        count_moves_x += 1
        move_y = True

    time.sleep(2)

    return count_moves_x, count_moves_y, move_right, move_y

def position_camera(browser,
                    mapa,
                    map_img,
                    lon,
                    lat
                    ):

    counter = 0 #mora doc do cilja u manje od 20 koraka

    lon1, lat1, lon2, lat2 = find_lon_lat(mapa, map_img.shape, browser)

    diff_lon = 10000
    diff_lat = 10000

    pix_lon = abs(lon1 - lon2)/map_img.shape[1]
    pix_lat = abs(lat1 - lat2)/map_img.shape[0]

    while abs(diff_lon) > 1 or abs(diff_lat) > 1:
        if counter >= 20:
            print('Takes to many steps to move to the righ position!!')
            break
        else:
            temp_lon11, temp_lat11, temp_lon22, temp_lat22 = find_lon_lat(mapa, map_img.shape, browser)

            # pos_long = temp_long11 + abs(temp_long11 - temp_long22)/2
            # pos_lat = temp_lat11 + abs(temp_lat11 - temp_lat22)/2

            diff_lon = lon - temp_lon11
            diff_lat = temp_lat22 - lat
            print(f'diff_lon: {diff_lon}, diff_lat: {diff_lat}')

            # diff_x = pos_long - long
            # diff_y = lat - pos_lat

            if abs(diff_lon) > 10:
                step_lon = int(diff_lon/(2*pix_lon))
                if step_lon > 0:
                    step_lon -= 1
                else:
                    step_lon += 1

            if abs(diff_lat) > 10:
                step_lat = int(diff_lat/(2*pix_lat))
                if step_lat > 0:
                    step_lat -= 1
                else:
                    step_lat += 1

            if abs(diff_lon) <= 1:
                step_lon = 1
            if abs(diff_lat) <= 1:
                step_lat = 1

            if abs(step_lon) > 1 or abs(step_lat) > 1:
                ActionChains(browser).move_to_element(mapa).move_by_offset(step_lon, step_lat).click_and_hold().move_to_element(mapa).release().perform()
                counter += 1

    time.sleep(2)

    return temp_lon11, temp_lat11, temp_lon22, temp_lat22


def long_lat_to_pix(lon, lat, browser, mapa, map_img):
    lon1, lat1, lon2, lat2 = find_lon_lat(mapa, map_img.shape, browser)

    pix_lon = abs(lon1 - lon2)/map_img.shape[1]
    pix_lat = abs(lat1 - lat2)/map_img.shape[0]

    pos_lon = lon1 + abs(lon1 - lon2)/2
    pos_lat = lat1 + abs(lat1 - lat2)/2

    diff_lon = lon - pos_lon
    diff_lat = pos_lat - lat

    step_lon = int(diff_lon/pix_lon)
    step_lat = int(diff_lat/pix_lat)    
    
    return step_lon, step_lat


def do_the_job(args, date, link):
    f = open(f'{args.data_path}{date}.txt', 'w+')
    #line = 'Katastarska općina;Broj katastarske čestice;Adresa katastarske čestice;Površina katastarske čestice/m2;Posjedovni list;Način uporabe i zgrade + Površina/m2;Posjedovni list + Udio + Ime i prezime/Naziv + Adresa\n'
    
    f_pos = open(f'{args.data_path}last_position.txt', 'w+')
    f_pos.close()

    # pravokutnik od interesa
    start_lon = 448577.94
    start_lat = 5075598.09
    end_lon = 467923.70
    end_lat = 5067859.79

    # standard diffs
    standard_diff_lon = 2277.5499999999884
    standard_diff_lat = 1070.089999999851

    # koriste se za nastavak ako je bot blokirao
    continue_lon = start_lon#start_lon + 3*standard_diff_lon
    continue_lat = start_lat#start_lat - standard_diff_lat

    #točke pravokutnika koje mora proć da bi uzeo sve podatke
    A = [start_lon, start_lat]
    B = [end_lon, start_lat]
    C = [start_lon, end_lat]
    D = [end_lon, end_lat]

    A_flag = False
    B_flag = False
    C_flag = False
    D_flag = False

    move_right = True
    move_down = False

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
    except:
        print(f'Failed to open link: {link}!')
        sys.exit(1)

    # prihvati kolačiće
    try:
        accept_cookies(browser)
    except:
        print(f'Failed to accept cookies!')
        sys.exit(1)

    # nađi zagreb na mapi
    try:
        select_region(browser)
    except:
        print(f'Failed to select region!')
        sys.exit(1)

    # nađi mapu
    try:
        mapa = browser.find_elements_by_class_name('ol-layer')[0]
    except:
        print(f'Can not find map on the website!')
        sys.exit(1)

    # uzmi sliku mape
    map_img = stringToRGB(mapa.screenshot_as_base64)

    width_img = map_img.shape[1]
    height_img = map_img.shape[0]
    
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
    # mask_img = cv2.imread('roi_mask.png')
    # mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)

    # nađi startnu poziciju (A točku)
    x_offset, y_offset = long_lat_to_pix(continue_lon, continue_lat, browser, mapa, map_img)
    
    # x_pos = 638
    # y_pos = 343
    # times_to_move_x = 9
    # times_to_move_y = 6
    # x_offset, y_offset = calc_offset(mask_img.shape, x_pos, y_pos)
    #i, j = np.where(mask_img == 255)
    #x_offset, y_offset = calc_offset(mask_img.shape, j[0], i[0])

    # zoom in
    zoom_in(browser, mapa, x_offset, y_offset)

    # move to starting position
    try:
        new_lon1, new_lat1, new_lon2, new_lat2 = position_camera(browser, mapa, map_img, continue_lon, continue_lat)
        if abs(new_lon1-A[0]) < 1 and abs(new_lat2-A[1]) < 1:
            A_flag = True
    except:
        print(f'Positioning camera to A was not successful!')
        sys.exit(1)

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

    while not A_flag or not B_flag or not C_flag or not D_flag:

        wheel_element(mapa, 120)
        time.sleep(5)

        lon1, lat1, lon2, lat2 = find_lon_lat(mapa, map_img.shape, browser)
        diff_lon1 = abs(lon1 - lon2)
        diff_lat1 = abs(lat1 - lat2)

        link2 = f'https://oss.uredjenazemlja.hr/OssWebServices/wms?token=7effb6395af73ee111123d3d1317471357a1f012d4df977d3ab05ebdc184a46e&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=image%2Fpng8&TRANSPARENT=true&LAYERS=oss%3ABZP_CESTICE%2Coss%3ABZP_CESTICE%2Coss%3ABZP_ZGRADE&STYLES=jis_cestice_kathr%2Cjis_cestice_nazivi_kathr%2C&tiled=false&ratio=2&serverType=geoserver&CRS=EPSG%3A3765&WIDTH=2713&HEIGHT=1280&BBOX={lon1}%2C{lat1}%2C{lon2}%2C{lat2}'
        try:
            browser2.get(link2)
        except:
            print(f'Failed to open link: {link}!')
            pass
            #break

        time.sleep(5)
        try:
            layout_img_element = browser2.find_element_by_tag_name("img")
        except:
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

        #TODO test
        #kernel_map_img = cv2.imread('kernel_map_img.png')

        wheel_element(mapa, -120)
        time.sleep(5)
        
        #test = stringToRGB(mapa.screenshot_as_base64)
        #cv2.imwrite('testingggg1.png', test)

        lon11, lat11, lon22, lat22 = find_lon_lat(mapa, map_img.shape, browser)
        diff_lon2 = abs(lon11 - lon22)
        diff_lat2 = abs(lat11 - lat22)

        #resize layout img
        layout_img = cv2.resize(layout_img, (0,0),  fx=1.24, fy=1.24)
        layout_img = layout_img[138:-134, 287:-286]
        #cv2.imwrite('testingggg2.png', layout_img)

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
        x_offset_offset = 0
        y_offset_offset = 0
        while np.any(kernel_mask):
            s2 = -1
            i, j = np.where(kernel_mask == 255)
            x_offset, y_offset = calc_offset(kernel_mask.shape, j[0], i[0])
            ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset+x_offset_offset, y_offset+y_offset_offset).click().perform()
            time.sleep(1)

            sidebar_elements =  browser.find_elements_by_class_name('m-widget28__pic')
            for s1, sidebar in enumerate(sidebar_elements):
                if sidebar.rect['width'] > 0 and sidebar.rect['height'] > 0:
                    sidebar_element = sidebar
                    s2 = s1

            if s2 != 1 and s2 >= 0:
                ActionChains(browser).move_to_element(sidebar_element).move_by_offset(163, -115).click().perform()
                s2 = -1
                x_offset_offset += 1
                pass

            elif s2 == 1:
                x_offset_offset = 0
                try:
                    colect_data(f, browser)
                except:
                    print(f'Failed to collect data!')
                    try:
                        colect_data(f, browser)
                    except:
                        print(f'Failed to collect data!')

                cv2.floodFill(kernel_mask, mask, (j[0],i[0]), 0)
                cv2.imshow("kernel_mask", kernel_mask)
                cv2.waitKey(2)

                ActionChains(browser).move_to_element(sidebar_element).move_by_offset(163, -115).click().perform()
                s2 = -1

            # cv2.floodFill(kernel_mask, mask, (j[0],i[0]), 0)
            # cv2.imshow("kernel_mask", kernel_mask)
            # cv2.waitKey(2)
            
            # # colect data
            # try:
            #     colect_data(f, browser)
            # except:
            #     print(f'Failed to collect data!')

            # #close data dialog
            # try:
            #     #close_element = browser.find_element_by_class_name('m-portlet__nav-link')
            #     close_element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'm-portlet__nav-link')))
            # except:
            #     print(f'Can not find close button on the website!')
            
            # wait_count = 0
            # while close_element.rect['width'] == 0 and wait_count < 20:
            #     #ActionChains(browser).move_to_element(close_element).move_by_offset(118, 5).click().perform()
            #     time.sleep(1)
            #     wait_count += 1

            # if close_element.rect['width'] > 0:
            #     ActionChains(browser).move_to_element(close_element).move_by_offset(118, 5).click().perform()
            # else:
            #     time.sleep(10)

        # move camera
        try:
            if move_down:
                print('Moving down...')
                move_down = False
                move_right = not(move_right)

                new_lon1, new_lat1, new_lon2, new_lat2 = position_camera(browser, mapa, map_img, lon11, lat11)

                if abs(new_lon1-B[0]) < 1 and abs(new_lat1-B[1]) < 1:
                    B_flag = True
                if abs(new_lon1-C[0]) < 1 and abs(new_lat1-C[1]) < 1:
                    C_flag = True
                if abs(new_lon1-D[0]) < 1 and abs(new_lat1-D[1]) < 1:
                    D_flag = True

            elif move_right:
                print('Moving right...')
                new_lon1, new_lat1, new_lon2, new_lat2 = position_camera(browser, mapa, map_img, lon22, lat22)

                if abs(new_lon1-B[0]) < 1 and abs(new_lat1-B[1]) < 1:
                    B_flag = True
                if abs(new_lon1-C[0]) < 1 and abs(new_lat1-C[1]) < 1:
                    C_flag = True
                if abs(new_lon1-D[0]) < 1 and abs(new_lat1-D[1]) < 1:
                    D_flag = True
                
                if new_lon1 - B[0] > 0:
                    move_down = True

            else:
                print('Moving left...')
                new_lon1, new_lat1, new_lon2, new_lat2 = position_camera(browser, mapa, map_img, lon11-diff_lon2, lat22)

                if abs(new_lon1-B[0]) < 1 and abs(new_lat1-B[1]) < 1:
                    B_flag = True
                if abs(new_lon1-C[0]) < 1 and abs(new_lat1-C[1]) < 1:
                    C_flag = True
                if abs(new_lon1-D[0]) < 1 and abs(new_lat1-D[1]) < 1:
                    D_flag = True
                
                if A[0] - new_lon1 > 0:
                    move_down = True

            f_pos = open(f'{args.data_path}last_position.txt', 'a')
            f_pos.write(f'{new_lon1},{new_lat2}\n')
            f_pos.close()
                

        except:
            print(f'Camera move was unsuccessful!')

    f.close()     
    f_pos.close()
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
