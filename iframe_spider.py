from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
#from pyvirtualdisplay import Display

chrome_options = Options()
#chrome_options.add_argument('--headless')
options = webdriver.ChromeOptions()
options.add_argument("service_args=['–ignore-ssl-errors=true', '–ssl-protocol=TLSv1']") # Python2/3
options.add_experimental_option('excludeSwitches', ['enable-automation'])

driver = webdriver.Chrome('C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe', chrome_options=chrome_options)


print('1')
def getDriverHttp(url):
    print('2')
    soup = ''
    try:
        element = WebDriverWait(driver, 1200).until(driver.get(url))
    except Exception as e:
        print(e)
    try:
        # driver.get(url)
        # driver.implicitly_wait(800)
        print('3')
        iframes = driver.find_elements_by_tag_name('iframe')
        iframe = iframes[0]
        time.sleep(3)
        print('4')
        driver.switch_to.frame(iframe)                          # 最重要的一步

        WebDriverWait(driver, 1200).until(EC.visibility_of(driver.find_element(by=By.TAG_NAME, value='img')))

        print('5')
        soup = BeautifulSoup(driver.page_source, "html.parser")
        print('6')
        with open('./iframe.html', 'w') as f:
            f.write(driver.page_source)
            print('html saved')
    except Exception as e:
        print(e)
    #driver.quit()
    return soup


def getVideoUrl(url):
    soup = getDriverHttp(url)
    miPlayer = soup.find('div',id='J_miPlayer')
    url = miPlayer.find('video').get('src')
    driver.quit()
    return url


if __name__ == '__main__':
    #path = getVideoUrl(u'http://aaxxy.com/vod-play-id-10788-src-1-num-2.html')

    getDriverHttp('https://curiosity.lib.harvard.edu/chinese-rubbings-collection/catalog/6-990095673240203941')

#document.querySelector("html")

