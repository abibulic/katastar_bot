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
    return webdriver.Firefox(executable_path=args.geckodriver_path, firefox_binary=args.firefox_binary)

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

def do_the_job(args, date, link):
    f = open(f'{args.data_path}{date}.txt', 'w+')

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
    flag = True
    while flag:
        #cookies = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'cookie-layout')))
        cookies = browser.find_elements_by_class_name('cookie-layout')[0]
        if cookies.rect['height'] != 0:
            flag = False
    #ac = ActionChains(browser)
    ActionChains(browser).move_to_element(cookies).move_by_offset(860, 0).click().perform()

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
    time.sleep(20)

    # pozicioniranje na mapi
    mapa = browser.find_elements_by_class_name('ol-layer')[0]
    map_img = stringToRGB(mapa.screenshot_as_base64)
    
    #TODO temp
    #map_img = cv2.imread('mapa.jpg')

    lower = [80, 90, 180]
    upper = [85, 96, 190]
    mask_img = find_border(map_img, lower, upper)
    mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)

    i, j = np.where(mask_img == 255)

    x_offset, y_offset = calc_offset(mask_img.shape, j[0], i[0])

    # zoom in
    #ac = ActionChains(browser)
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()
    ActionChains(browser).move_to_element(mapa).move_by_offset(x_offset, y_offset).double_click().perform()


    # cv2.imwrite("mapa.png", map_img)
    # cv2.imshow("map_img", map_img)
    # cv2.imshow("mask_img", mask_img)
    # cv2.waitKey(0)

   



    # traži cijenu
    price = browser.find_elements_by_class_name("ClassifiedDetailSummary-priceForeign")
    price = price[0].text
    price = int(price.replace('~','').replace('.','').replace('€','').replace(' ',''))

    # traži površinu kuće i broj soba
    temp = browser.find_elements_by_class_name("ClassifiedDetailHighlightedAttributes-text")
    indoor_area = int(temp[0].text.split(',')[0])
    try:
        num_rooms = temp[1].text.split('-')[0]
    except:
        num_rooms = temp[1].text[0]

    # traži ostale izlistane karakteristike
    temp = browser.find_elements_by_class_name("ClassifiedDetailBasicDetails-textWrapContainer")
    for i, t in enumerate(temp):
        text = t.text
        if text == 'Lokacija':
            location1 = temp[i+1].text
        elif text == 'Ulica':
            street = temp[i+1].text
        elif text == 'Tip stana':
            ap_type = temp[i+1].text
        elif text == 'Broj etaža':
            num_floors = temp[i+1].text
        elif text == 'Broj soba' and num_rooms == 'None':
            num_rooms = temp[i+1].text
        elif text == 'Kat':
            floor = temp[i+1].text
        elif text == 'Ukupni broj katova':
            building_floors = temp[i+1].text
        elif text == 'Stambena površina' and indoor_area == 'None':
            indoor_area = temp[i+1].text[:-2]
        elif text == 'Netto površina':
            netto_area = temp[i+1].text[:-2].replace(',','.')
        elif text == 'Godina izgradnje':
            build_data = temp[i+1].text.replace('.','')
        elif text == 'Godina zadnje renovacije':
            last_renovation = temp[i+1].text.replace('.','')
        elif text == 'Namještenost i stanje':
            furnished = temp[i+1].text
        elif text == 'Broj parkirnih mjesta':
            parking_lots = temp[i+1].text
        elif text == 'Balkon/Lođa/Terasa':
            balcony = temp[i+1].text
        elif text == 'Energetski razred':
            energy_class = temp[i+1].text
    
    # traži drugu adresu i broj (često bude adresa agencije za oglašavanje)
    temp = browser.find_elements_by_class_name("ClassifiedDetailOwnerDetails-contactEntry")
    for i, t in enumerate(temp):
        text = t.text
        if 'Adresa' in text:
            location2 = text[9:]
        elif '09' in text or '+385' in text:
            tel = text
        elif 'Web adresa' in text:
            agency = text.split('\n')[-1]

    # traži vrijeme posta i datum isteka
    temp = browser.find_elements_by_class_name("ClassifiedDetailSystemDetails-listData")
    post_time = temp[0].text
    exparation_date = temp[1].text
    time_shown = temp[2].text.split(' ')[0]

    
    # uzmi sliku karte
    # mapa = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "mapboxgl-canvas")))
    # img = stringToRGB(mapa.screenshot_as_base64)
    # cv2.imshow("a",img)
    # cv2.waitKey(0)

    # uzmi slike nekretnine
    if args.save_img:
        #imgs = browser.find_elements_by_class_name("ClassifiedDetailGallery-figure")
        imgs = browser.find_elements_by_xpath("//figure[@class='ClassifiedDetailGallery-figure']/img")
        for i, img in enumerate(imgs):
            src = img.get_attribute('src')
            if src == None:
                src = img.get_attribute('data-src')

            img_name = f"{img_dir}/{ll:06d}{i:03d}.jpg"
            urllib.request.urlretrieve(src, img_name)

    # latitude, longitude
    if street != 'None':
        geocode_result = geocode(address=location1+','+street, as_featureset=True)
        latitude1 = geocode_result.features[0].geometry['y']
        longitude1 = geocode_result.features[0].geometry['x']

    else:
        geocode_result = geocode(address=location1, as_featureset=True)
        latitude1 = geocode_result.features[0].geometry['y']
        longitude1 = geocode_result.features[0].geometry['x']
        latitude1 += random.random()*0.0007
        longitude1 += random.random()*0.0007

    x, y = merc(str(latitude1)+','+str(longitude1))

    # geocode_result = geocode(address='Grad Zagreb'+location2, as_featureset=True)
    # latitude2 = geocode_result.features[0].geometry['y']
    # longitude2 = geocode_result.features[0].geometry['x']

    # dif_latitude = abs(latitude1-latitude2)
    # dif_longitude = abs(longitude1-longitude2)

    # if dif_latitude > 0.005 or dif_longitude > 0.005:
    #     latitude = latitude1
    #     longitude = longitude1
    # else:
    #     latitude = latitude2
    #     longitude = longitude2


    time.sleep(1)


    line_string = f'{ll:06d};'+\
                    link[:-1]+';'\
                    +str(price)+';'\
                    +str(indoor_area)+';'\
                    +num_rooms+';'\
                    +location1+';'\
                    +street+';'\
                    +ap_type+';'\
                    +num_floors+';'\
                    +floor+';'\
                    +building_floors+';'\
                    +netto_area+';'\
                    +build_data+';'\
                    +last_renovation+';'\
                    +furnished+';'\
                    +parking_lots+';'\
                    +balcony+';'\
                    +energy_class+';'\
                    +location2+';'\
                    +tel+';'\
                    +agency+';'\
                    +post_time+';'\
                    +exparation_date+';'\
                    +time_shown+';'\
                    +str(latitude1)+';'\
                    +str(longitude1)+';'\
                    +str(x)+';'\
                    +str(y)

    f1.write("%s\n" % line_string)
        
    f1.close()
    f2.close()  
    browser.quit()

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
        







