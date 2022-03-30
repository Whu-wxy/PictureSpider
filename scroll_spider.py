from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

#from pyvirtualdisplay import Display
from queue import Queue
from Download_thread import ThreadWrite
import config
import re

# chrome_options = Options()
#chrome_options.add_argument('--headless')
options = webdriver.ChromeOptions()
options.add_argument("service_args=['–ignore-ssl-errors=true', '–ssl-protocol=TLSv1']") # Python2/3
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_argument('--ignore-certificate-errors')   # 忽略掉证书错误
options.add_argument('-ignore-ssl-errors')
# options.add_argument('headless')

#get直接返回，不再等待界面加载完成
desired_capabilities = DesiredCapabilities.CHROME
desired_capabilities["pageLoadStrategy"] = "none"

# 打开chrome浏览器
# C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe or D:\UserApps\Programs\Python\Scripts
driver = webdriver.Chrome(options=options)
driver.maximize_window()
# driver.set_page_load_timeout(30)  #页面加载超时时间
# driver.set_script_timeout(30)  #页面js加载超时时间

def scroll_page():
   # 返回滚动高度
   last_height = driver.execute_script("return document.body.scrollHeight")
   time.sleep(5)
   while True:
      # 滑动一次
      driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

      # 等待加载
      time.sleep(5)

      # 计算新的滚动高度并与上一个滚动高度进行比较
      new_height = driver.execute_script("return document.body.scrollHeight")
      # print(last_height)
      # print(new_height)
      if new_height == last_height:
         break
      last_height = new_height

   html = driver.page_source
   return html


#解析网页数据
def parse(html):
    soup = BeautifulSoup(html, 'lxml')

    # 找出所有图片url
    url_feature = '^[\s\S]*(' + config.img_url_keyword + ')[\s\S]*$'
    imgs = soup.find_all("img", {"src": re.compile(url_feature)}, recursive=True)
    img_links = []
    for link in imgs:
        link = link['src']
        if len(link) < 2 or not link.startswith('http'):
            continue
        link = link.replace("\n", "")
        link = link.replace("\r", "")
        img_links.append(link.strip())

    return img_links

if __name__ == '__main__':
    url = 'https://www.shipspotting.com/photos/gallery?shipName=&shipNameSearchMode=begins&imo=&mmsi=&eni=&pennant=&callSign=&category=&user=&country=China&port=&includeSubPorts=on&perPage=192&viewType=thumb&sortBy=newest'
    request_img_number = 2000
    img_queue = Queue()
    thread_list = []
    loadList = []
    for i in range(config.thread_num):
        loadList.append('线程' + str(i))
    for threadName in loadList:
        Ithraad = ThreadWrite(threadName, img_queue)
        Ithraad.start()
        thread_list.append(Ithraad)
    try:
        driver.get(url)
    except TimeoutException:  # 报错后就强制停止加载 # 这里是js控制
        driver.execute_script('window.stop()')
    locator = (By.CLASS_NAME, 'photo-card__link')
    # locator = (By.ID, 'root')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator))
    print('WebDriverWait finish')
    last_num = 0
    download_links = set()
    while True:
        html = scroll_page()
        img_links = parse(html) 
        img_links_set = set(img_links)
        new_links = download_links^img_links_set

        print('progress: ', '[',len(img_links), '/', request_img_number, ']')
        if last_num != len(img_links):
            for link in new_links:
                img_queue.put(('', config.save_path, link))
            download_links = download_links | new_links

        if len(img_links) > request_img_number:
            break

        last_num = len(img_links)

    driver.quit()

    for thread in thread_list:
        thread.THREAD_EXIT = True
        thread.join()