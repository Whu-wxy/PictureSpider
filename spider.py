import aiohttp
import asyncio
import time
from bs4 import BeautifulSoup
from urllib.request import urljoin
import re
import multiprocessing as mp
import os
from urllib.parse import urljoin
import random
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

import config

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

seen = set()
unseen = set([config.base_url])

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
}

# proxies = {'http':'http://117.88.5.202',
#            'https':'https://117.88.177.33',
#             'https':'https://119.254.94.93',
#             'https':'https://117.88.5.27',
#             'https':'https://125.73.220.18',
#             'https':'https://117.88.176.110',
#            }

#解析网页数据
def parse(html, url):
    soup = BeautifulSoup(html, 'lxml')
    urls = soup.find_all('a', {"href": re.compile('^.+/.+?$')})

    title = soup.find('title')
    if title:
        title = title.get_text().strip()
    else:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
        else:
            title = os.path.basename(url)

    page_urls = set([urljoin(config.base_url, url['href']) for url in urls])
    imgs = soup.find_all("img", {"src": re.compile('.+/.+?')})
    img_links = []
    for link in imgs:
        img_links.append(link['src'])

    return title, page_urls, img_links, url

#下载网页
async def crawl(url, session):
    print('正在爬取: ', url)
    try:
        r = await session.get(url, headers=headers)   #, proxy = 'http://117.88.5.202'
        html = await r.text("utf-8","ignore")
        await asyncio.sleep(random.uniform(2, 5))       # slightly delay for downloading
        return (html, url)
    except Exception as e:
        print(repr(e))
        return ('', url)


async def main(loop):
    global unseen
    pool = mp.Pool(2)               # slightly affected
    async with aiohttp.ClientSession() as session:
        count = 1
        while len(unseen) != 0:
            print('Crawled url count: ', len(seen))
            print('UnCrawled url count: ', len(unseen))
            if config.max_page_count != None:
                if count > config.max_page_count:
                    break
            unseen = list(unseen)
            tasks = [loop.create_task(crawl(url, session)) for url in unseen[:5]]
            finished, unfinished = await asyncio.wait(tasks)
            htmls = [f.result() for f in finished]

            parse_jobs = [pool.apply_async(parse, args=(html, url,)) for (html, url) in htmls]
            results = [j.get() for j in parse_jobs]

            seen.update(unseen[:5])
            unseen = unseen[5:]
            unseen = set(unseen)
            for title, page_urls, img_links, url in results:
                print('正在从"%s"下载图片...' % url)
                title = re.sub('[\/:*?"<>|]', '-', title)    #创建文件夹时去除非法字符
                if not os.path.exists('./imgs/'+title):
                    os.makedirs('./imgs/'+title)    #创建文件夹

                unseen.update(page_urls - seen)
                count += 1

                download_imgs(img_links, './imgs/' + title, url)

#下载图片
def download_imgs(img_links, saveDir, url):
    for IMAGE_URL in img_links:
        IMAGE_URL = urljoin(url, IMAGE_URL)
        filename = os.path.basename(IMAGE_URL)
        try:
            r = requests.get(IMAGE_URL, stream=True, headers=headers, verify=False)  # stream loading   , proxies = proxies
        except requests.exceptions.RequestException as e:
            print(e)
            continue

        try:
            with open(os.path.join(saveDir, filename), 'wb') as f:
                for chunk in r.iter_content(chunk_size=32):
                    f.write(chunk)
        except Exception as e:
            print(repr(e))
            continue

        time.sleep(0.1)


if __name__ == "__main__":
    if config.max_page_count != None and config.max_page_count <= 0:
        print('最大爬取页数必须大于0!')
    else:
        if config.max_page_count == None:
            print('将爬取所有网页图片！手动停止或爬取完所有网页！')
        t1 = time.time()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))
        loop.close()
        print("Total time: ", time.time() - t1)

    print('结束！')