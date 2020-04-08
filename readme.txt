1.安装需要的包：
pip install -r requirements.txt


2.在config.py中修改参数


3.运行
#单线程下载图片，速度较慢
python spider.py

#多线程下载图片，速度快 (Download_thread.py只在这里使用)
python spider_thread.py

#爬取iframe中的内容，博物馆里这部分由于加载过慢，总是报timeout，现采用最后一个，网页完全加载完之后，手动存html
python iframe_spider.py

#把一个网址的html文件下载下来
python down_html.py

#先将html或iframe内的html手动存到iframe_content.html文件，然后运行，将会开始下载图片
python crawl_from_offline_html.py