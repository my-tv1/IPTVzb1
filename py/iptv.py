#本程序只适用于酒店源的检测，请勿移植他用
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import re
import os
import threading
from queue import Queue
import queue
from datetime import datetime
import replace
import fileinput
from tqdm import tqdm
from pypinyin import lazy_pinyin
from opencc import OpenCC
import base64
import cv2
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from translate import Translator  # 导入Translator类，用于文本翻译
# 扫源测绘空间地址
# 搜素关键词："iptv/live/zh_cn.js" && country="CN" && region="Hunan" && city="changsha"
# 搜素关键词："ZHGXTV" && country="CN" && region="Hunan" && city="changsha"
#"isShowLoginJs"智能KUTV管理

#定义ZHGXTV采集地址
urls = [
    "https://fofa.info/result?qbase64=IlpIR1hUViIgJiYgcmVnaW9uPSJndWFuZ2Rvbmci",#广东
    "https://fofa.info/result?qbase64=IlpIR1hUViIgJiYgcmVnaW9uPSJHdWFuZ2RvbmciICYmIGNpdHk9InNoYW50b3Ui",#广东汕头
    "https://fofa.info/result?qbase64=IlpIR1hUViIgJiYgcmVnaW9uPSJHdWFuZ2RvbmciICYmIHBvcnQ9IjIyMjMi",#广东2223
    #"https://fofa.info/result?qbase64=IlpIR1hUViIgJiYgcmVnaW9uPSJIZW5hbiI%3D",#河南
    #"https://fofa.info/result?qbase64=IlpIR1hUViIgJiYgcmVnaW9uPSJoZWJlaSI%3D",#河北
    #"https://fofa.info/result?qbase64=IlpIR1hUViIgJiYgcmVnaW9uPSJzaWNodWFuIg%3D%3D",#四川  
]
#定义网址替换规则
def modify_urls(url):
    modified_urls = []
    ip_start_index = url.find("//") + 2
    ip_end_index = url.find(":", ip_start_index)
    base_url = url[:ip_start_index]  # http:// or https://
    ip_address = url[ip_start_index:ip_end_index]
    port = url[ip_end_index:]
    ip_end = "/ZHGXTV/Public/json/live_interface.txt"
    for i in range(1, 256):
        modified_ip = f"{ip_address[:-1]}{i}"
        modified_url = f"{base_url}{modified_ip}{port}{ip_end}"
        modified_urls.append(modified_url)
    return modified_urls
#定义超时时间以及是否返回正确的状态码
def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=3)          #//////////////////
        if response.status_code == 200:
            return url
    except requests.exceptions.RequestException:
        pass
    return None


results = []
for url in urls:
    # 创建一个Chrome WebDriver实例
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    # 使用WebDriver访问网页
    driver.get(url)  # 将网址替换为你要访问的网页地址
    time.sleep(10)
    # 获取网页内容
    page_content = driver.page_source
    # 关闭WebDriver
    driver.quit()

    # 查找所有符合指定格式的网址
    pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"  # 设置匹配的格式，如http://8.8.8.8:8888
    urls_all = re.findall(pattern, page_content)
    # urls = list(set(urls_all))  # 去重得到唯一的URL列表
    urls = set(urls_all)  # 去重得到唯一的URL列表
    x_urls = []
    for url in urls:  # 对urls进行处理，ip第四位修改为1，并去重
        url = url.strip()
        ip_start_index = url.find("//") + 2
        ip_end_index = url.find(":", ip_start_index)
        ip_dot_start = url.find(".") + 1
        ip_dot_second = url.find(".", ip_dot_start) + 1
        ip_dot_three = url.find(".", ip_dot_second) + 1
        base_url = url[:ip_start_index]  # http:// or https://
        ip_address = url[ip_start_index:ip_dot_three]
        port = url[ip_end_index:]
        ip_end = "1"
        modified_ip = f"{ip_address}{ip_end}"
        x_url = f"{base_url}{modified_ip}{port}"
        x_urls.append(x_url)
    urls = set(x_urls)  # 去重得到唯一的URL列表

    valid_urls = []
    #   多线程获取可用url
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for url in urls:
            url = url.strip()
            modified_urls = modify_urls(url)
            for modified_url in modified_urls:
                futures.append(executor.submit(is_url_accessible, modified_url))
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                valid_urls.append(result)
    for url in valid_urls:
        print(url)
    # 遍历网址列表，获取JSON文件并解析
    for url in valid_urls:
        try:
            # 发送GET请求获取JSON文件，设置超时时间为0.5秒
            json_url = f"{url}"
            response = requests.get(json_url, timeout=3)################################
            json_data = response.content.decode('utf-8')
            try:
                    # 按行分割数据
             lines = json_data.split('\n')
             for line in lines:
                 if 'udp' not in line and 'rtp' not in line:
                        line = line.strip()
                        if line:
                            name, channel_url = line.split(',')
                            urls = channel_url.split('/', 3)
                            url_data = json_url.split('/', 3)
                            if len(urls) >= 4:
                                urld = (f"{urls[0]}//{url_data[2]}/{urls[3]}")
                            else:
                                urld = (f"{urls[0]}//{url_data[2]}")
                            print(f"{name},{urld}")

                        if name and urld:
                            name = name.replace("高清电影", "影迷电影")                            
                            name = name.replace("中央", "CCTV")
                            name = name.replace("高清", "")
                            name = name.replace("HD", "")
                            name = name.replace("标清", "")
                            name = name.replace("超高", "")
                            name = name.replace("频道", "")
                            name = name.replace("靓妆", "女性时尚")
                            name = name.replace("本港台", "TVB星河")
                            name = name.replace("汉3", "汉")
                            name = name.replace("汉4", "汉")
                            name = name.replace("汉5", "汉")
                            name = name.replace("汉6", "汉")
                            name = name.replace("CHC动", "动")
                            name = name.replace("CHC家", "家")
                            name = name.replace("CHC影", "影")
                            name = name.replace("-", "")
                            name = name.replace(" ", "")
                            name = name.replace("PLUS", "+")
                            name = name.replace("＋", "+")
                            name = name.replace("(", "")
                            name = name.replace(")", "")
                            name = name.replace("L", "")
                            name = name.replace("新农村", "河南新农村")
                            name = name.replace("百姓调解", "河南百姓调解")
                            name = name.replace("法治", "河南法治")
                            name = name.replace("睛彩中原", "河南睛彩")
                            name = name.replace("军事", "河南军事")
                            name = name.replace("梨园", "河南梨园")
                            name = name.replace("相声小品", "河南相声小品")
                            name = name.replace("移动戏曲", "河南移动戏曲")
                            name = name.replace("都市生活", "河南都市生活")
                            name = name.replace("民生", "河南民生")
                            name = name.replace("CCTVNEWS", "CCTV13")
                            name = name.replace("cctv", "CCTV")
                            name = re.sub(r"CCTV(\d+)台", r"CCTV\1", name)
                            name = name.replace("CCTV1综合", "CCTV1")
                            name = name.replace("CCTV2财经", "CCTV2")
                            name = name.replace("CCTV3综艺", "CCTV3")
                            name = name.replace("CCTV4国际", "CCTV4")
                            name = name.replace("CCTV4中文国际", "CCTV4")
                            name = name.replace("CCTV4欧洲", "CCTV4")
                            name = name.replace("CCTV5体育", "CCTV5")
                            name = name.replace("CCTV5+体育", "CCTV5+")
                            name = name.replace("CCTV6电影", "CCTV6")
                            name = name.replace("CCTV7军事", "CCTV7")
                            name = name.replace("CCTV7军农", "CCTV7")
                            name = name.replace("CCTV7农业", "CCTV7")
                            name = name.replace("CCTV7国防军事", "CCTV7")
                            name = name.replace("CCTV8电视剧", "CCTV8")
                            name = name.replace("CCTV8纪录", "CCTV9")
                            name = name.replace("CCTV9记录", "CCTV9")
                            name = name.replace("CCTV9纪录", "CCTV9")
                            name = name.replace("CCTV10科教", "CCTV10")
                            name = name.replace("CCTV11戏曲", "CCTV11")
                            name = name.replace("CCTV12社会与法", "CCTV12")
                            name = name.replace("CCTV13新闻", "CCTV13")
                            name = name.replace("CCTV新闻", "CCTV13")
                            name = name.replace("CCTV14少儿", "CCTV14")
                            name = name.replace("央视14少儿", "CCTV14")
                            name = name.replace("CCTV少儿超", "CCTV14")
                            name = name.replace("CCTV15音乐", "CCTV15")
                            name = name.replace("CCTV音乐", "CCTV15")
                            name = name.replace("CCTV16奥林匹克", "CCTV16")
                            name = name.replace("SCTV5四川影视）", "SCTV5")
                            name = name.replace("CCTV17农业农村", "CCTV17")
                            name = name.replace("CCTV17军农", "CCTV17")
                            name = name.replace("CCTV17农业", "CCTV17")
                            name = name.replace("CCTV5+体育赛视", "CCTV5+")
                            name = name.replace("CCTV5+赛视", "CCTV5+")
                            name = name.replace("CCTV5+体育赛事", "CCTV5+")
                            name = name.replace("CCTV5+赛事", "CCTV5+")
                            name = name.replace("CCTV5+体育", "CCTV5+")
                            name = name.replace("CCTV5赛事", "CCTV5+")
                            name = name.replace("凤凰中文台", "凤凰中文")
                            name = name.replace("凤凰资讯台", "凤凰资讯")
                            name = name.replace("CCTV4K测试）", "CCTV4")
                            name = name.replace("CCTV164K", "CCTV16")
                            name = name.replace("上海东方卫视", "上海卫视")
                            name = name.replace("东方卫视", "上海卫视")
                            name = name.replace("内蒙卫视", "内蒙古卫视")
                            name = name.replace("福建东南卫视", "东南卫视")
                            name = name.replace("广东南方卫视", "南方卫视")
                            name = name.replace("湖南金鹰卡通", "金鹰卡通")
                            name = name.replace("炫动卡通", "哈哈炫动")
                            name = name.replace("卡酷卡通", "卡酷少儿")
                            name = name.replace("卡酷动画", "卡酷少儿")
                            name = name.replace("BRTVKAKU少儿", "卡酷少儿")
                            name = name.replace("优曼卡通", "优漫卡通")
                            name = name.replace("优曼卡通", "优漫卡通")
                            name = name.replace("嘉佳卡通", "佳嘉卡通")
                            name = name.replace("世界地理", "地理世界")
                            name = name.replace("CCTV世界地理", "地理世界")
                            name = name.replace("BTV北京卫视", "北京卫视")
                            name = name.replace("BTV冬奥纪实", "冬奥纪实")
                            name = name.replace("东奥纪实", "冬奥纪实")
                            name = name.replace("卫视台", "卫视")
                            name = name.replace("湖南电视台", "湖南卫视")
                            name = name.replace("少儿科教", "少儿")
                            name = name.replace("TV星河2）", "星河")
                            name = name.replace("影视剧", "影视")
                            name = name.replace("电视剧", "影视")
                            name = name.replace("奥运匹克", "")
                            results.append(f"{name},{urld}")
            except:
                continue
        except:
            continue
channels = []
for result in results:
    line = result.strip()
    if result:
        channel_name, channel_url = result.split(',')
        channels.append((channel_name, channel_url))
with open("iptv.txt", 'w', encoding='utf-8') as file:
    for result in results:
        file.write(result + "\n")
        print(result)
print("频道列表文件iptv.txt获取完成！")

for line in fileinput.input("iptv.txt", inplace=True):  #打开文件，并对其进行关键词原地替换
    line = line.replace("河南河南", "河南")
    line = line.replace("河南河南", "河南")  
    line = line.replace("河南法制", "河南法治")          
    line = line.replace("国防河南军事", "")             
    line = line.replace("CCTV12法制", "CCTV12")             
    line = line.replace("CCTV15+音乐", "CCTV15")             
    line = line.replace("CCTV17农村农业", "CCTV17")             
    line = line.replace("（福建卫视）", "")               
    line = line.replace("公共,http://171.8", "河南公共,http://171.8")   
    line = line.replace("新闻,http://171.8", "河南新闻,http://171.8")  
    line = line.replace("影视,http://171.8", "河南电视剧,http://171.8")             
    line = line.replace("河南影视,http://171.13", "河南电视剧,http://171.13")                       
    line = line.replace("广东大湾区卫视", "大湾区卫视")             
    line = line.replace("吉林延边卫视", "延边卫视")             
    line = line.replace("国防河南军事", "国防军事")             
    line = line.replace("都市生活", "都市")               
    line = line.replace("都市生活6", "都市")                   
    print(line, end="")  #设置end=""，避免输出多余的换行符

#定义智慧桌面采集地址
urls = [
    #"https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgcG9ydD0iMTExMSI%3D",  # 1111
    #"https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04iICYmIHJlZ2lvbj0i5rKz5YyXIg%3D%3D",  #河北
    "https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04iICYmIHJlZ2lvbj0i5bm%2F5LicIg%3D%3D",  #广东
    #"https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04iICYmIHJlZ2lvbj0ibGlhb25pbmci"    #辽宁
    #"https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04iICYmIHJlZ2lvbj0i5rKz5Y2XIg%3D%3D",  # 河南
    #"https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgcmVnaW9uPSJIdWJlaSIg",#湖北
    "https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgcG9ydD0iODE4MSIgJiYgY2l0eT0iR3VpZ2FuZyI%3D",  #贵港8181
    "https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY2l0eT0ieXVsaW4i",#玉林
    "https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgcmVnaW9uPSJmdWppYW4i",#福建
    "https://fofa.info/result?qbase64=ImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04iICYmIHJlZ2lvbj0i5bm%2F6KW%2FIg%3D%3D",    #广西 壮族iptv
]
def modify_urls(url):
    modified_urls = []
    ip_start_index = url.find("//") + 2
    ip_end_index = url.find(":", ip_start_index)
    base_url = url[:ip_start_index]  # http:// or https://
    ip_address = url[ip_start_index:ip_end_index]
    port = url[ip_end_index:]
    ip_end = "/iptv/live/1000.json?key=txiptv"
    for i in range(1, 256):
        modified_ip = f"{ip_address[:-1]}{i}"
        modified_url = f"{base_url}{modified_ip}{port}{ip_end}"
        modified_urls.append(modified_url)
    return modified_urls
def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=3)          #//////////////////
        if response.status_code == 200:
            return url
    except requests.exceptions.RequestException:
        pass
    return None
results = []
for url in urls:
    # 创建一个Chrome WebDriver实例
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    # 使用WebDriver访问网页
    driver.get(url)  # 将网址替换为你要访问的网页地址
    time.sleep(10)
    # 获取网页内容
    page_content = driver.page_source
    # 关闭WebDriver
    driver.quit()
    # 查找所有符合指定格式的网址
    pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"  # 设置匹配的格式，如http://8.8.8.8:8888
    urls_all = re.findall(pattern, page_content)
    # urls = list(set(urls_all))  # 去重得到唯一的URL列表
    urls = set(urls_all)  # 去重得到唯一的URL列表
    x_urls = []
    for url in urls:  # 对urls进行处理，ip第四位修改为1，并去重
        url = url.strip()
        ip_start_index = url.find("//") + 2
        ip_end_index = url.find(":", ip_start_index)
        ip_dot_start = url.find(".") + 1
        ip_dot_second = url.find(".", ip_dot_start) + 1
        ip_dot_three = url.find(".", ip_dot_second) + 1
        base_url = url[:ip_start_index]  # http:// or https://
        ip_address = url[ip_start_index:ip_dot_three]
        port = url[ip_end_index:]
        ip_end = "1"
        modified_ip = f"{ip_address}{ip_end}"
        x_url = f"{base_url}{modified_ip}{port}"
        x_urls.append(x_url)
    urls = set(x_urls)  # 去重得到唯一的URL列表
    valid_urls = []
    #   多线程获取可用url
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for url in urls:
            url = url.strip()
            modified_urls = modify_urls(url)
            for modified_url in modified_urls:
                futures.append(executor.submit(is_url_accessible, modified_url))
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                valid_urls.append(result)
    for url in valid_urls:
        print(url)
    # 遍历网址列表，获取JSON文件并解析
    for url in valid_urls:
        try:
            # 发送GET请求获取JSON文件，设置超时时间为0.5秒
            ip_start_index = url.find("//") + 2
            ip_dot_start = url.find(".") + 1
            ip_index_second = url.find("/", ip_dot_start)
            base_url = url[:ip_start_index]  # http:// or https://
            ip_address = url[ip_start_index:ip_index_second]
            url_x = f"{base_url}{ip_address}"
            json_url = f"{url}"
            response = requests.get(json_url, timeout=3)                        #///////////////
            json_data = response.json()
            try:
                # 解析JSON文件，获取name和url字段
                for item in json_data['data']:
                    if isinstance(item, dict):
                        name = item.get('name')
                        urlx = item.get('url')
                        if 'udp' not in urlx and 'rtp' not in urlx:
                            pass
                        if 'http' in urlx:
                            urld = f"{urlx}"
                        else:
                            urld = f"{url_x}{urlx}"
                        if name and urld:
                            name = name.replace("高清电影", "影迷电影")                            
                            name = name.replace("中央", "CCTV")
                            name = name.replace("高清", "")
                            name = name.replace("HD", "")
                            name = name.replace("标清", "")
                            name = name.replace("超高", "")
                            name = name.replace("频道", "")
                            name = name.replace("汉1", "汉")
                            name = name.replace("汉2", "汉")
                            name = name.replace("汉3", "汉")
                            name = name.replace("汉4", "汉")
                            name = name.replace("汉5", "汉")
                            name = name.replace("汉6", "汉")
                            name = name.replace("CHC动", "动")
                            name = name.replace("CHC家", "家")
                            name = name.replace("CHC影", "影")
                            name = name.replace("-", "")
                            name = name.replace(" ", "")
                            name = name.replace("PLUS", "+")
                            name = name.replace("＋", "+")
                            name = name.replace("(", "")
                            name = name.replace(")", "")
                            name = name.replace("CHC", "")
                            name = name.replace("L", "")
                            name = name.replace("002", "AA酒店MV")
                            name = name.replace("测试002", "凤凰卫视")
                            name = name.replace("测试003", "凤凰卫视")
                            name = name.replace("测试004", "私人影院")
                            name = name.replace("测试005", "私人影院")
                            name = name.replace("测试006", "东森洋片")
                            name = name.replace("测试007", "东森电影")
                            name = name.replace("测试008", "AXN电影")
                            name = name.replace("测试009", "好莱坞电影")
                            name = name.replace("测试010", "龙祥电影")
                            name = name.replace("莲花台", "凤凰香港")
                            name = name.replace("测试014", "凤凰资讯")
                            name = name.replace("测试015", "未知影视")
                            name = name.replace("TV星河", "空")
                            name = name.replace("305", "酒店影视1")
                            name = name.replace("306", "酒店影视2")
                            name = name.replace("307", "酒店影视3")
                            name = name.replace("CMIPTV", "")
                            name = name.replace("cctv", "CCTV")
                            name = re.sub(r"CCTV(\d+)台", r"CCTV\1", name)
                            name = name.replace("CCTV1综合", "CCTV1")
                            name = name.replace("CCTV2财经", "CCTV2")
                            name = name.replace("CCTV3综艺", "CCTV3")
                            name = name.replace("CCTV4国际", "CCTV4")
                            name = name.replace("CCTV4中文国际", "CCTV4")
                            name = name.replace("CCTV4欧洲", "CCTV4")
                            name = name.replace("CCTV5体育", "CCTV5")
                            name = name.replace("CCTV5+体育", "CCTV5+")
                            name = name.replace("CCTV6电影", "CCTV6")
                            name = name.replace("CCTV7军事", "CCTV7")
                            name = name.replace("CCTV7军农", "CCTV7")
                            name = name.replace("CCTV7农业", "CCTV7")
                            name = name.replace("CCTV7国防军事", "CCTV7")
                            name = name.replace("CCTV8电视剧", "CCTV8")
                            name = name.replace("CCTV8纪录", "CCTV9")
                            name = name.replace("CCTV9记录", "CCTV9")
                            name = name.replace("CCTV9纪录", "CCTV9")
                            name = name.replace("CCTV10科教", "CCTV10")
                            name = name.replace("CCTV11戏曲", "CCTV11")
                            name = name.replace("CCTV12社会与法", "CCTV12")
                            name = name.replace("CCTV13新闻", "CCTV13")
                            name = name.replace("CCTV新闻", "CCTV13")
                            name = name.replace("CCTV14少儿", "CCTV14")
                            name = name.replace("央视14少儿", "CCTV14")
                            name = name.replace("CCTV少儿超", "CCTV14")
                            name = name.replace("CCTV15音乐", "CCTV15")
                            name = name.replace("CCTV音乐", "CCTV15")
                            name = name.replace("CCTV16奥林匹克", "CCTV16")
                            name = name.replace("CCTV17农业农村", "CCTV17")
                            name = name.replace("CCTV17军农", "CCTV17")
                            name = name.replace("CCTV17农业", "CCTV17")
                            name = name.replace("CCTV5+体育赛视", "CCTV5+")
                            name = name.replace("CCTV5+赛视", "CCTV5+")
                            name = name.replace("CCTV5+体育赛事", "CCTV5+")
                            name = name.replace("CCTV5+赛事", "CCTV5+")
                            name = name.replace("CCTV5+体育", "CCTV5+")
                            name = name.replace("CCTV5赛事", "CCTV5+")
                            name = name.replace("凤凰中文台", "凤凰中文")
                            name = name.replace("凤凰资讯台", "凤凰资讯")
                            name = name.replace("CCTV4K测试）", "CCTV4")
                            name = name.replace("CCTV164K", "CCTV16")
                            name = name.replace("上海东方卫视", "上海卫视")
                            name = name.replace("东方卫视", "上海卫视")
                            name = name.replace("内蒙卫视", "内蒙古卫视")
                            name = name.replace("福建东南卫视", "东南卫视")
                            name = name.replace("广东南方卫视", "南方卫视")
                            name = name.replace("湖南金鹰卡通", "金鹰卡通")
                            name = name.replace("炫动卡通", "哈哈炫动")
                            name = name.replace("卡酷卡通", "卡酷少儿")
                            name = name.replace("卡酷动画", "卡酷少儿")
                            name = name.replace("BRTVKAKU少儿", "卡酷少儿")
                            name = name.replace("优曼卡通", "优漫卡通")
                            name = name.replace("优曼卡通", "优漫卡通")
                            name = name.replace("嘉佳卡通", "佳嘉卡通")
                            name = name.replace("世界地理", "地理世界")
                            name = name.replace("CCTV世界地理", "地理世界")
                            name = name.replace("BTV北京卫视", "北京卫视")
                            name = name.replace("BTV冬奥纪实", "冬奥纪实")
                            name = name.replace("东奥纪实", "冬奥纪实")
                            name = name.replace("卫视台", "卫视")
                            name = name.replace("湖南电视台", "湖南卫视")
                            name = name.replace("少儿科教", "少儿")
                            name = name.replace("TV星河2）", "星河")
                            name = name.replace("影视剧", "影视")
                            name = name.replace("电视剧", "影视")
                            name = name.replace("奥运匹克", "")
                            name = name.replace("TVBTVB", "TVB")
                            name = name.replace("星空卫视", "动物杂技")
                            results.append(f"{name},{urld}")
            except:
                continue
        except:
            continue
channels = []
for result in results:
    line = result.strip()
    if result:
        channel_name, channel_url = result.split(',')
        channels.append((channel_name, channel_url))
with open("iptv.txt", 'a', encoding='utf-8') as file:           #打开文本以追加的形式写入行到ZHGX文件
    for result in results:
        file.write(result + "\n")
        print(result)
print("频道列表文件iptv.txt追加写入成功！")


#这里排序IP段去重放在了原文件头
#这里排序IP段去重放在了原文件头
#这里排序IP段去重放在了原文件头
#这里排序IP段去重放在了原文件头
#这里排序IP段去重放在了原文件头
#这里排序IP段去重放在了原文件头
#这里排序IP段去重放在了原文件头



###################################################去除列表中的组播地址以及CCTV和卫视
def filter_lines(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    filtered_lines = []
    for line in lines:
        #if 'hls' in line or 'tsfile' in line:
        if ',' in line:
          if 'udp' not in line and 'rtp' not in line:   # and 'CCTV' not in line and '卫视' not in line
            filtered_lines.append(line)
    with open(output_file, 'w', encoding='utf-8') as output_file:
        output_file.writelines(filtered_lines)
filter_lines("iptv.txt", "iptv.txt")



################################################按网址去重，此段代码多余，为了方便变更暂时保留
def remove_duplicates(input_file, output_file):
    # 用于存储已经遇到的URL和包含genre的行
    seen_urls = set()
    seen_lines_with_genre = set()
    # 用于存储最终输出的行
    output_lines = []
    # 打开输入文件并读取所有行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print("去重前的行数：", len(lines))
        # 遍历每一行
        for line in lines:
            # 使用正则表达式查找URL和包含genre的行,默认最后一行
            urls = re.findall(r'[https]?[http]?[P2p]?[mitv]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
            genre_line = re.search(r'\bgenre\b', line, re.IGNORECASE) is not None
            # 如果找到URL并且该URL尚未被记录
            if urls and urls[0] not in seen_urls:
                seen_urls.add(urls[0])
                output_lines.append(line)
            # 如果找到包含genre的行，无论是否已被记录，都写入新文件
            if genre_line:
                output_lines.append(line)
    # 将结果写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    print("去重后的行数：", len(output_lines))
remove_duplicates('iptv.txt', 'iptv.txt')

###################################################打开文件，并对其进行行内关键词原地替换再次规范频道名，若无异类频道名，此段代码可删   
for line in fileinput.input("iptv.txt", inplace=True):                    #
    line = line.replace("CHC电影", "影迷电影")             
    line = line.replace("湖北公共新闻", "湖北公共")             
    line = line.replace("CHC电影", "影迷电影")             
    line = line.replace("CHC电影", "影迷电影")             
    line = line.replace("河南影视", "河南电视剧")                            
    line = line.replace("公共新闻", "公共")                                
    line = line.replace("广东河南", "广东")                                         
    line = line.replace("公共,http://58.51", "湖北公共新闻,http://58.51")                                           
    line = line.replace("", "")                                           
    line = line.replace("", "")                                           
    line = line.replace("", "")                              
    line = line.replace("影视文化", "影视")                            
    line = line.replace("武汉影视", "武汉电视剧")                            
    line = line.replace("公共新闻,http://58.", "湖北公共新闻,http://58.")                            
    line = line.replace("湖北公共,", "湖北公共新闻,")                                              
    line = line.replace("湖北湖北", "湖北")                                              
    line = line.replace("深圳影视", "深圳电视剧")             
    print(line, end="")  #设置end=""，避免输出多余的换行符


#################################################### 对整理好的频道列表测试HTTP连接
def test_connectivity(url, max_attempts=1): #定义测试HTTP连接的次数
    # 尝试连接指定次数    
   for _ in range(max_attempts):  
    try:
        response = requests.head(url, timeout=10)  # 发送HEAD请求，仅支持V4,修改此行数字可定义链接超时
        #response = requests.get(url, timeout=10)  # 发送get请求，支持V6,修改此行数字可定义链接超时
        return response.status_code == 200  # 返回True如果状态码为200
    except requests.RequestException:  # 捕获requests引发的异常
        pass  # 发生异常时忽略
   #return False  # 如果所有尝试都失败，返回False
   pass   
# 使用队列来收集结果的函数
def process_line(line, result_queue):
    parts = line.strip().split(",")  # 去除行首尾空白并按逗号分割
    if len(parts) == 2 and parts[1]:  # 确保有URL，并且URL不为空
        channel_name, channel_url = parts  # 分别赋值频道名称和URL
        if test_connectivity(channel_url):  # 测试URL是否有效
            result_queue.put((channel_name, channel_url, "有效"))  # 将结果放入队列
        else:
            result_queue.put((channel_name, channel_url, "无效"))  # 将结果放入队列
    else:
        # 格式不正确的行不放入队列
        pass
# 主函数
def main(source_file_path, output_file_path):
    with open(source_file_path, "r", encoding="utf-8") as source_file:  # 打开源文件
        lines = source_file.readlines()  # 读取所有行s     
    result_queue = queue.Queue()  # 创建队列
    threads = []  # 初始化线程列表
    for line in tqdm(lines, desc="检测进行中"):  # 显示进度条
        thread = threading.Thread(target=process_line, args=(line, result_queue))  # 创建线程
        thread.start()  # 启动线程
        threads.append(thread)  # 将线程加入线程列表
    for thread in threads:  # 等待所有线程完成
        thread.join()
    # 初始化计数器
    valid_count = 0
    invalid_count = 0
    with open(output_file_path, "w", encoding="utf-8") as output_file:  # 打开输出文件
        for _ in range(result_queue.qsize()):  # 使用队列的大小来循环
            item = result_queue.get()  # 获取队列中的项目
            # 只有在队列中存在有效的项目时才写入文件
            if item[0] and item[1]:  # 确保channel_name和channel_url都不为None
                output_file.write(f"{item[0]},{item[1]},{item[2]}\n")  # 写入文件
                if item[2] == "有效":  # 统计有效源数量
                    valid_count += 1
                else:  # 统计无效源数量
                    invalid_count += 1
    print(f"任务完成, 有效源数量: {valid_count}, 无效源数量: {invalid_count}")  # 打印结果
if __name__ == "__main__":
    try:
        source_file_path = "iptv.txt"  # 输入源文件路径
        output_file_path = "检测结果.txt"  # 设置输出文件路径
        main(source_file_path, output_file_path)  # 调用main函数
    except Exception as e:
        print(f"程序发生错误: {e}")  # 打印错误信息
        
#########################################################################提取检测结果中的有效行
def filter_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:  # 打开文件
        lines = file.readlines()  # 读取所有行
    filtered_lines = []  # 初始化过滤后的行列表
    for line in lines:  # 遍历所有行
        if 'genre' in line or '有效' in line:  # 如果行中包含'genre'或'有效'
            filtered_lines.append(line)  # 将行添加到过滤后的行列表
    return filtered_lines  # 返回过滤后的行列表
def write_filtered_lines(output_file_path, filtered_lines):
    with open(output_file_path, 'w', encoding='utf-8') as output_file:  # 打开输出文件
        output_file.writelines(filtered_lines)  # 写入过滤后的行
if __name__ == "__main__":
    input_file_path = "检测结果.txt"  # 设置输入文件路径
    output_file_path = "检测结果.txt"  # 设置输出文件路径
    filtered_lines = filter_lines(input_file_path)  # 调用filter_lines函数
    write_filtered_lines(output_file_path, filtered_lines)  # 调用write_filtered_lines函数


###################################################################################定义替换规则的字典,对整行内的内容进行替换
replacements = {
    ",有效": "",  # 将",有效"替换为空字符串
    "#genre#,无效": "#genre#",  # 将"#genre#,无效"替换为"#genre#"
}
# 打开原始文件读取内容，并写入新文件
with open('检测结果.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()
# 创建新文件并写入替换后的内容
with open('检测结果.txt', 'w', encoding='utf-8') as new_file:
    for line in lines:
        for old, new in replacements.items():  # 遍历替换规则字典
            line = line.replace(old, new)  # 替换行中的内容
        new_file.write(line)  # 写入新文件
print("新文件已保存。")  # 打印完成信息

####################### 提示用户输入文件名（拖入文件操作）打开用户指定的文件对不规范频道名再次替换
file_path = '检测结果.txt'
# 检查文件是否存在
if not os.path.isfile(file_path):
    print("文件不存在，请重新输入.")
    exit(1)
with open(file_path, 'r', encoding="utf-8") as file:
    # 读取所有行并存储到列表中
    lines = file.readlines()
#定义替换规则的字典对频道名替换
replacements = {
    	"-": "",
    	"星河": "TVB星河",
    	"福建东南卫视": "东南卫视",
    	"CCTV风云音乐": "风云音乐",
    	"本港台（珠江）": "TVB星河",
    	"\n都市": "\n河南都市",
    	"": "",
    	"": "",
    	"SD": "",
    	"「": "",
    	"AA": "",
    	"XF": "",
    	"": "",
    	"": "",
    	"湖南金鹰纪实": "金鹰纪实",
    	"频道": "",
    	"CCTV-": "CCTV",
    	"CCTV_": "CCTV",
    	" ": "",
    	"CCTV高尔夫网球": "高尔夫网球",
    	"CCTV发现之旅": "发现之旅",
    	"CCTV中学生": "中学生",
    	"CCTV兵器科技": "兵器科技",
    	"CCTV地理世界": "地理世界",
    	"CCTV风云足球": "风云足球",
    	"CCTV央视台球": "央视台球",
    	"CCTV台球": "台球",
    	"CCTV高尔夫网球": "高尔夫网球",
    	"CCTV中视购物": "中视购物",
    	"CCTV发现之旅": "发现之旅",
    	"CCTV中学生": "中学生",
    	"CCTV高尔夫网球": "高尔夫网球",
    	"CCTV风云剧场": "风云剧场",
    	"CCTV第一剧场": "第一剧场",
    	"CCTV怀旧剧场": "怀旧剧场",
    	"CCTV风云剧场": "风云剧场",
    	"CCTV第一剧场": "第一剧场",
    	"CCTV怀旧剧场": "怀旧剧场",
    	"IPTV": "",
    	"PLUS": "+",
    	"＋": "+",
    	"(": "",
    	")": "",
    	"CAV": "",
    	"美洲": "",
    	"北美": "",
    	"12M": "",
    	"高清测试CCTV-1": "",
    	"高清测试CCTV-2": "",
    	"高清测试CCTV-7": "",
    	"高清测试CCTV-10": "",
    	"LD": "",
    	"HEVC20M": "",
    	"S,": ",",
    	"测试": "",
    	"CCTW": "CCTV",
    	"试看": "",
    	"测试": "",
    	"NewTv": "",
    	"NEWTV": "",
    	"NewTV": "",
    	"iHOT": "",
    	"CHC": "",
    	"测试cctv": "CCTV",
    	"凤凰中文台": "凤凰中文",
    	"凤凰资讯台": "凤凰资讯",
    	"(CCTV4K测试）": "CCTV4K",
    	"上海东方卫视": "上海卫视",
    	"东方卫视": "上海卫视",
    	"内蒙卫视": "内蒙古卫视",
    	"福建东南卫视": "东南卫视",
    	"广东南方卫视": "南方卫视",
    	"湖南金鹰卡通": "金鹰卡通",
    	"炫动卡通": "哈哈炫动",
    	"卡酷卡通": "卡酷少儿",
    	"卡酷动画": "卡酷少儿",
    	"BRTVKAKU少儿": "卡酷少儿",
    	"优曼卡通": "优漫卡通",
    	"优曼卡通": "优漫卡通",
    	"嘉佳卡通": "佳嘉卡通",
    	"世界地理": "地理世界",
    	"CCTV世界地理": "地理世界",
    	"BTV北京卫视": "北京卫视",
    	"BTV冬奥纪实": "冬奥纪实",
    	"东奥纪实": "冬奥纪实",
    	"卫视台": "卫视",
    	"湖南电视台": "湖南卫视",
    	"少儿科教": "少儿",
    	"影视剧": "影视",
    	"电视剧": "影视",
    	"CCTV1CCTV1": "CCTV1",
    	"CCTV2CCTV2": "CCTV2",
    	"CCTV7CCTV7": "CCTV7",
    	"CCTV10CCTV10": "CCTV10"
}
with open('酒店源.txt', 'w', encoding='utf-8') as new_file:
    for line in lines:
        # 去除行尾的换行符
        line = line.rstrip('\n')
        # 分割行，获取逗号前的字符串
        parts = line.split(',', 1)
        if len(parts) > 0:
            # 替换逗号前的字符串
            before_comma = parts[0]
            for old, new in replacements.items():
                before_comma = before_comma.replace(old, new)
            # 将替换后的逗号前部分和逗号后部分重新组合成一行，并写入新文件
            new_line = f'{before_comma},{parts[1]}\n' if len(parts) > 1 else f'{before_comma}\n'
            new_file.write(new_line)
#
#####################################定义替换规则的字典,对整行内的多余标识内容进行替换
replacements = {
    	"（）": "",
        "湖北,": "湖北卫视,",
        "广东,": "广东卫视,",
        "安徽,": "安徽卫视,",
        "北京,": "北京卫视,",
        "重庆,": "重庆卫视,",
        "东南,": "东南卫视,",
        "湖南,": "湖南卫视,",
        "吉林,": "吉林卫视,",
        "江苏,": "江苏卫视,",
        "山东,": "山东卫视,",
        "上海,": "上海卫视,",
        "深圳,": "深圳卫视,",
        "四川,": "四川卫视,",
        "天津,": "天津卫视,",
        "厦门1,": "厦门卫视,",
        "厦门2,": "厦门卫视,",
        "浙江,": "浙江卫视,",
        "T,": ",",
        "dx,": ",",
        "g,": ",",
        "P,": "+,",
        "lt,": ",",
        "": "",
        "": "",
        "": ""
}
# 打开原始文件读取内容，并写入新文件
with open('酒店源.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()
# 创建新文件并写入替换后的内容
with open('酒店源.txt', 'w', encoding='utf-8') as new_file:
    for line in lines:
        for old, new in replacements.items():
            line = line.replace(old, new)
        new_file.write(line)
print("替换完成，新文件已保存。")
#
###############################################################################文本排序
# 打开原始文件读取内容，并写入新文件
with open('酒店源.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()
# 定义一个函数，用于提取每行的第一个数字
def extract_first_number(line):
    match = re.search(r'\d+', line)
    return int(match.group()) if match else float('inf')
# 对列表中的行进行排序
# 按照第一个数字的大小排列，如果不存在数字则按中文拼音排序
sorted_lines = sorted(lines, key=lambda x: (not 'CCTV' in x, extract_first_number(x) if 'CCTV' in x else lazy_pinyin(x.strip())))
# 将排序后的行写入新的utf-8编码的文本文件，文件名基于原文件名
output_file_path = "sorted_" + os.path.basename(file_path)
# 写入新文件
with open('酒店源.txt', "w", encoding="utf-8") as file:
    for line in sorted_lines:
        file.write(line)
print(f"文件已排序并保存为: {output_file_path}")
#
##########################################################################################简体转繁体
# 创建一个OpenCC对象，指定转换的规则为繁体字转简体字
converter = OpenCC('t2s.json')#繁转简
#converter = OpenCC('s2t.json')#简转繁
# 打开txt文件
with open('酒店源.txt', 'r', encoding='utf-8') as file:
    traditional_text = file.read()
# 进行繁体字转简体字的转换
simplified_text = converter.convert(traditional_text)
# 将转换后的简体字写入txt文件
with open('酒店源.txt', 'w', encoding='utf-8') as file:
    file.write(simplified_text)
#
########################################################################定义关键词分割规则,分类提取
def check_and_write_file(input_file, output_file, keywords):
    # 使用 split(', ') 而不是 split(',') 来分割关键词
    keywords_list = keywords.split(', ')
    first_keyword = keywords_list[0]  # 获取第一个关键词作为头部信息
    pattern = '|'.join(re.escape(keyword) for keyword in keywords_list)
    extracted_lines = False
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write(f'{first_keyword},#genre#\n')  # 使用第一个关键词作为头部信息
        for line in lines:
            if 'genre' not in line and 'epg' not in line:
                if re.search(pattern, line):
                    out_file.write(line)
                    extracted_lines = True
    # 如果没有提取到任何关键词，则不保留输出文件
    if not extracted_lines:
        os.remove(output_file)  # 删除空的输出文件
        print(f"未提取到关键词，{output_file} 已被删除。")
    else:
        print(f"文件已提取关键词并保存为: {output_file}")
# 按类别提取关键词并写入文件
check_and_write_file('酒店源.txt',  'a0.txt',  keywords="央视频道, 8K, 4K, 4k")
check_and_write_file('酒店源.txt',  'a.txt',  keywords="央视频道, CCTV, 8K, 4K, 爱上4K, 纯享, 风云剧场, 怀旧剧场, 影迷, 高清电影, 动作电影, 每日影院, 全球大片, 第一剧场, 家庭影院, 影迷电影, 星光, 华语, 美国大片, 峨眉")
check_and_write_file('酒店源.txt',  'a1.txt',  keywords="央视频道, 风云音乐, 女性时尚, 地理世界, 音乐现场")

check_and_write_file('酒店源.txt',  'b.txt',  keywords="卫视频道, 卫视, 凤凰， 星空")

check_and_write_file('酒店源.txt',  'c.txt',  keywords="影视频道, 爱情喜剧, 爱喜喜剧, 风云剧场, 怀旧剧场, 影迷, 高清电影, 动作电影, 每日影院, 全球大片, 第一剧场, 家庭影院, 影迷电影, 星光, 华语, 美国大片, 峨眉, \
电影, 惊嫊悬疑, 东北热剧, 无名, 都市剧场, iHOT, 剧场, 欢笑剧场, 重温经典, 明星大片, 中国功夫, 军旅, 东北热剧, 中国功夫, 军旅剧场, 古装剧场, \
家庭剧场, 惊悚悬疑, 欢乐剧场, 潮妈辣婆, 爱情喜剧, 精品大剧, 超级影视, 超级电影, 黑莓动画, 黑莓电影, 海外剧场, 精彩影视, 无名影视, 潮婆辣妈, 超级剧, 热播精选")
check_and_write_file('酒店源.txt',  'c1.txt',  keywords="影视频道, 求索动物, 求索, 求索科学, 求索记录, 爱谍战, 爱动漫, 爱科幻, 爱青春, 爱自然, 爱科学, 爱浪漫, 爱历史, 爱旅行, 爱奇谈, 爱怀旧, 爱赛车, 爱都市, 爱体育, 爱经典, \
爱玩具, 爱喜剧, 爱悬疑, 爱幼教, 爱院线")
check_and_write_file('酒店源.txt',  'c2.txt',  keywords="影视频道, 军事评论, 农业致富, 哒啵赛事, 怡伴健康, 武博世界, 超级综艺, 哒啵, HOT, 炫舞未来, 精品体育, 精品萌宠, 精品记录, 超级体育, 金牌, 武术世界, 精品纪录")

check_and_write_file('酒店源.txt',  'd.txt',  keywords="少儿频道, 少儿, 卡通, 动漫, 宝贝, 哈哈")

check_and_write_file('酒店源.txt',  'e.txt',  keywords="港澳频道, TVB, 珠江台, 澳门, 龙华, 广场舞, 动物杂技, 民视, 中视, 华视, AXN, MOMO, 采昌, 耀才, 靖天, 镜新闻, 靖洋, 莲花, 年代, 爱尔达, 好莱坞, 华丽, 非凡, 公视, \
寰宇, 无线, EVEN, MoMo, 爆谷, 面包, momo, 唐人, 中华小, 三立, CNA, FOX, RTHK, Movie, 八大, 中天, 中视, 东森, 凤凰, 天映, 美亚, 环球, 翡翠, 亚洲, 大爱, 大愛, 明珠, 半岛, AMC, 龙祥, 台视, 1905, 纬来, 神话, 经典都市, 视界, \
番薯, 私人, 酒店, TVB, 凤凰, 半岛, 星光视界, 大愛, 新加坡, 星河, 明珠, 环球, 翡翠台")

check_and_write_file('酒店源.txt',  'f.txt',  keywords="省市频道, 湖北, 武汉, 河北, 广东, 河南, 陕西, 四川, 湖南, 广西, 石家庄, 南宁, 汕头, 揭阳, 普宁, 福建, 辽宁")

check_and_write_file('酒店源.txt',  'o1.txt',  keywords="其他频道, 新闻, 综合, 文艺, 电视, 公共, 科教, 教育, 民生, 轮播, 套, 法制, 文化, 经济, 生活")
check_and_write_file('酒店源.txt',  'o.txt',  keywords="其他频道, , ")
#
#对生成的文件进行合并
file_contents = []
file_paths = ["e.txt", "a0.txt", "a.txt", "a1.txt", "b.txt", "c.txt", "c1.txt", "c2.txt", "d.txt", "f.txt", "o1.txt", "o.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            content = file.read()
            file_contents.append(content)
    else:                # 如果文件不存在，则提示异常并打印提示信息
        print(f"文件 {file_path} 不存在，跳过")
# 写入合并后的文件
with open("去重.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))
#

##################################################################### 打开文档并读取所有行 ，对提取后重复的频道去重
with open('去重.txt', 'r', encoding="utf-8") as file:
 lines = file.readlines()
# 使用列表来存储唯一的行的顺序 
 unique_lines = [] 
 seen_lines = set() 
# 遍历每一行，如果是新的就加入unique_lines 
for line in lines:
 if line not in seen_lines:
  unique_lines.append(line)
  seen_lines.add(line)
# 将唯一的行写入新的文档 
with open('酒店源.txt', 'w', encoding="utf-8") as file:
 file.writelines(unique_lines)
#任务结束，删除不必要的过程文件
files_to_remove = ['去重.txt', "2.txt", "iptv.txt", "e.txt", "a0.txt", "a.txt", "a1.txt", "b.txt", "c.txt", "c1.txt", "c2.txt", "d.txt", "f.txt", "o1.txt", "o.txt", "检测结果.txt"]
for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
    else:              # 如果文件不存在，则提示异常并打印提示信息
        print(f"文件 {file} 不存在，跳过删除。")
print("任务运行完毕，酒店源频道列表可查看文件夹内txt文件！")






































# 获取rtp目录下的文件名
files = os.listdir('rtp')
files_name = []
# 去除后缀名并保存至provinces_isps
for file in files:
    name, extension = os.path.splitext(file)
    files_name.append(name)
#忽略不符合要求的文件名
provinces_isps = [name for name in files_name if name.count('_') == 1]
# 打印结果
print(f"本次查询：{provinces_isps}的组播节目") 
keywords = []
for province_isp in provinces_isps:
    # 读取文件并删除空白行
    try:
        with open(f'rtp/{province_isp}.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines if line.strip()]
        # 获取第一行中以包含 "rtp://" 的值作为 mcast
        if lines:
            first_line = lines[1]
            if "rtp://" in first_line:
                mcast = first_line.split("rtp://")[1].split(" ")[0]
                keywords.append(province_isp + "_" + mcast)
    except FileNotFoundError:
    # 如果文件不存在，则捕获 FileNotFoundError 异常并打印提示信息
        print(f"文件 '{province_isp}.txt' 不存在. 跳过此文件.")
for keyword in keywords:
    province, isp, mcast = keyword.split("_")
    # 将省份转成英文小写
    translator = Translator(from_lang='chinese', to_lang='english')
    province_en = translator.translate(province)
    province_en = province_en.lower()
    # 根据不同的 isp 设置不同的 org 值
    org = "Chinanet"
    others = ''
    if isp == "电信" and province_en == "sichuang":
        org = "Chinanet"
        isp_en = "ctcc"
        asn = "4134"
        others = '&& city="Chengdu" '
    elif isp == "电信" and province_en != "sichuang":
        org = "Chinanet"
        isp_en = "ctcc"
        asn = "4134"
    elif isp == "联通" and province_en != "beijing":
        isp_en = "cucc"
        org = "CHINA UNICOM China169 Backbone"
        asn = "4837"
    elif isp == "联通" and province_en == "beijing":
        asn = "4808"
        isp_en = "cucc"
    else:
        asn = ""
        org = ""
    current_time = datetime.now()
    timeout_cnt = 0
    result_urls = set()
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\"'# && org=\"{org}\"
                # 将字符串编码为字节流
            bytes_string = search_txt.encode('utf-8')
                # 使用 base64 进行编码
            search_txt = base64.b64encode(bytes_string).decode('utf-8')
            search_url += search_txt
            print(f"{current_time} 查询运营商 : {province}{isp} ，查询网址 : {search_url}")
            response = requests.get(search_url, timeout=30)
            # 处理响应
            response.raise_for_status()
            # 检查请求是否成功
            html_content = response.text
            # 使用BeautifulSoup解析网页内容
            html_soup = BeautifulSoup(html_content, "html.parser")
            # print(f"{current_time} html_content:{html_content}")
            # 查找所有符合指定格式的网址
            # 设置匹配的格式，如http://8.8.8.8:8888
            pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
            urls_all = re.findall(pattern, html_content)
            # 去重得到唯一的URL列表
            result_urls = set(urls_all)
            print(f"{current_time} result_urls:{result_urls}")
            valid_ips = []
            # 遍历所有视频链接
            for url in result_urls:
                video_url = url + "/rtp/" + mcast
                # 用OpenCV读取视频
                cap = cv2.VideoCapture(video_url)
                # 检查视频是否成功打开
                if not cap.isOpened():
                    print(f"{current_time} {video_url} 无效")
                else:
                    # 读取视频的宽度和高度
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    print(f"{current_time} {video_url} 的分辨率为 {width}x{height}")
                    # 检查分辨率是否大于0
                    if width > 0 and height > 0:
                        valid_ips.append(url)
                    # 关闭视频流
                    cap.release()
                    
            if valid_ips:
                #生成节目列表 省份运营商.txt
                rtp_filename = f'rtp/{province}_{isp}.txt'
                with open(rtp_filename, 'r', encoding='utf-8') as file:
                    data = file.read()
                txt_filename = f'playlist/{province}{isp}.txt'
                with open(txt_filename, 'w') as new_file:
                    for url in valid_ips:
                        new_data = data.replace("rtp://", f"{url}/rtp/")
                        new_file.write(new_data)
                print(f'已生成播放列表，保存至{txt_filename}')
            else:
                print("未找到合适的 IP 地址。")
        except (requests.Timeout, requests.RequestException) as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}]搜索请求发生超时，异常次数：{timeout_cnt}")
            if timeout_cnt <= 2:
                    # 继续下一次循环迭代
                continue
            else:
                print(f"{current_time} 搜索IPTV频道源[]，超时次数过多：{timeout_cnt} 次，停止处理")
print('playlist制作完成！ 文件输出在当前文件夹！')
# 合并自定义频道文件#
file_contents = []
file_paths = ["playlist/四川电信.txt", "playlist/河南电信.txt", "playlist/河北电信.txt"]  # 替换为实际的文件路径列表
for file_path in file_paths:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            content = file.read()
            file_contents.append(content)
    else:                # 如果文件不存在，则提示异常并打印提示信息
        print(f"文件 {file_path} 不存在，跳过")
# 写入合并后的文件
with open("组播源.txt", "w", encoding="utf-8") as output:
    output.write('\n'.join(file_contents))
for line in fileinput.input("组播源.txt", inplace=True):  #打开文件，并对其进行关键词原地替换 
    line = line.replace("CHC电影", "CHC影迷电影") 
    line = line.replace("高清电影", "影迷电影") 
    print(line, end="")  #设置end=""，避免输出多余的换行符   
#从整理好的文本中按类别进行特定关键词提取#
keywords = ['CHC', '峨眉', '华语', '星光院线', '剧场', '家庭', '影迷', '动作', '星空', '凤凰']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
#pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制
with open('组播源.txt', 'r', encoding='utf-8') as file, open('c2.txt', 'w', encoding='utf-8') as c2:    #定义临时文件名
    c2.write('\n组播剧场,#genre#\n')                                                                  #写入临时文件名$GD
    for line in file:
      if '$GD' not in line and '调解' not in line:
        if re.search(pattern, line):  # 如果行中有任意关键字
         c2.write(line)  # 将该行写入输出文件                                                          #定义临时文件
#从整理好的文本中按类别进行特定关键词提取#
keywords = ['爱动漫', '爱怀旧', '爱经典', '爱科幻', '爱幼教', '爱青春', '爱院线', '爱悬疑']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
#pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制
with open('组播源.txt', 'r', encoding='utf-8') as file, open('c1.txt', 'w', encoding='utf-8') as c1:    #定义临时文件名
    c1.write('\niHOT系列,#genre#\n')                                                                  #写入临时文件名$GD
    for line in file:
      if '$GD' not in line and '4K' not in line:
        if re.search(pattern, line):  # 如果行中有任意关键字
         c1.write(line)  # 将该行写入输出文件                                                          #定义临时文件
 
#从整理好的文本中按类别进行特定关键词提取#
keywords = ['4K', '8K']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
#pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制
with open('组播源.txt', 'r', encoding='utf-8') as file, open('DD.txt', 'w', encoding='utf-8') as DD:
    DD.write('\n4K 频道,#genre#\n')
    for line in file:
        if re.search(pattern, line):  # 如果行中有任意关键字
          DD.write(line)  # 将该行写入输出文件
keywords = ['湖南', '广东', '广州', '河南', '河北']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
#pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制
with open('组播源.txt', 'r', encoding='utf-8') as file, open('df1.txt', 'w', encoding='utf-8') as df1:
    #df1.write('\n省市频道,#genre#\n')
    for line in file:
      if 'CCTV' not in line and '卫视' not in line and '影' not in line and '剧' not in line and '4K' not in line:        
        if re.search(pattern, line):  # 如果行中有任意关键字
          df1.write(line)  # 将该行写入输出文件
#从整理好的文本中按类别进行特定关键词提取#
keywords = ['河北', '石家庄', '丰宁', '临漳', '井陉', '井陉矿区', '保定', '元氏', '兴隆', '内丘', '南宫', '吴桥', '唐县', '唐山', '安平', '定州', '大厂', '张家口', '徐水', '成安', \
            '承德', '故城', '康保', '廊坊', '晋州', '景县', '武安', '枣强', '柏乡', '涉县', '涞水', '涞源', '涿州', '深州', '深泽', '清河', '秦皇岛', '衡水', '遵化', '邢台', '邯郸', \
            '邱县', '隆化', '雄县', '阜平', '高碑店', '高邑', '魏县', '黄骅', '饶阳', '赵县', '睛彩河北', '滦南', '玉田', '崇礼', '平泉', '容城', '文安', '三河', '清河']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
#pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制
with open('组播源.txt', 'r', encoding='utf-8') as file, open('f.txt', 'w', encoding='utf-8') as f:    #定义临时文件名
    f.write('\n河北频道,#genre#\n')                                                                  #写入临时文件名
    for line in file:
      if 'CCTV' not in line and '卫视' not in line and 'CHC' not in line and '4K' not in line and 'genre' not in line:
        if re.search(pattern, line):  # 如果行中有任意关键字
         f.write(line)  # 将该行写入输出文件
#从整理好的文本中按类别进行特定关键词提取#
keywords = ['河南', '焦作', '开封', '卢氏', '洛阳', '孟津', '安阳', '宝丰', '邓州', '渑池', '南阳', '内黄', '平顶山', '淇县', '郏县', '封丘', '获嘉', '巩义', '杞县', '汝阳', '三门峡', '卫辉', '淅川', \
            '新密', '新乡', '信阳', '新郑', '延津', '叶县', '义马', '永城', '禹州', '原阳', '镇平', '郑州', '周口']  # 需要提取的关键字列表
pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字
#pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制
with open('组播源.txt', 'r', encoding='utf-8') as file, open('f1.txt', 'w', encoding='utf-8') as f1:    #定义临时文件名
    f1.write('\n河南频道,#genre#\n')                                                                  #写入临时文件名
    for line in file:
      if 'CCTV' not in line and '卫视' not in line and 'CHC' not in line and '4K' not in line and 'genre' not in line:
        if re.search(pattern, line):  # 如果行中有任意关键字
         f1.write(line)  # 将该行写入输出文件
#从文本中截取省市段生成新文件#
# 定义关键词
start_keyword = '省市频道,#genre#'
end_keyword = '其他频道,#genre#'
# 输入输出文件路径
input_file_path = '酒店源.txt'  # 替换为你的输入文件路径
output_file_path = 'df.txt'  # 替换为你想要保存输出的文件路径
# 用于存储结果的列表
result_lines = []
# 打开输入文件并读取内容
with open(input_file_path, 'r', encoding='utf-8') as file:
    capture = False  # 用于控制是否开始捕获行
    for line in file:
        # 检查是否到达开始关键词
        if start_keyword in line:
            capture = True
            result_lines.append(line)  # 添加开始关键词所在的行
        # 如果已经开始捕获，并且到达结束关键词，则停止捕获
        elif end_keyword in line and capture:
            break
        # 如果处于捕获状态，则添加当前行
        if capture:
            result_lines.append(line)
# 将结果写入输出文件
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.writelines(result_lines)
print('提取完成，结果已保存到:', output_file_path)
#
#
#  获取远程港澳台直播源文件
url = "https://raw.githubusercontent.com/frxz751113/AAAAA/main/TW.txt"          #源采集地址
r = requests.get(url)
open('港澳.txt','wb').write(r.content)         #打开源文件并临时写入



#
#从整理好的文本中按类别进行特定关键词提取#
with open('酒店源.txt', 'r', encoding='utf-8') as f:  #打开文件，并对其进行关键词提取                                               #
 #keywords = ['http', 'rtmp', 'genre']  # 需要提取的关键字列表                                                       #
 keywords = ['重温', '酒店', '私人', '天映', '莲花', 'AXN', '好莱坞', 'TVB', '星', '广场舞', '龙祥', '凤凰', '东森']  # 需要提取的关键字列表                                                       #
 pattern = '|'.join(keywords)  # 创建正则表达式模式，匹配任意一个关键字                                      #
 #pattern = r"^(.*?),(?!#genre#)(.*?)$" #以分类直接复制                                                     #
 with open('酒店源.txt', 'r', encoding='utf-8') as file, open('b.txt', 'w', encoding='utf-8') as b:           #
    b.write('港澳频道,#genre#\n')                                                                        #
    for line in file:                                                                                      #
        if re.search(pattern, line):  # 如果行中有任意关键字                                                #
          b.write(line)  # 将该行写入输出文件                                                               #
                                                                                                           #



#从整理好的文本中进行特定关键词替换以规范频道名#
for line in fileinput.input("b.txt", inplace=True):  #打开文件，并对其进行关键词原地替换                     #
    #line = line.replace("央视频道,#genre#", "")                                                                         #
    line = line.replace("四川康巴卫视", "康巴卫视")                                                                         #
    line = line.replace("黑龙江卫视+", "黑龙江卫视")                                                                         #
    line = line.replace("[1920*1080]", "")                                                                         #
    line = line.replace("湖北电视台", "湖北综合")                                                                         #
    line = line.replace("教育台", "教育")                                                                         #
    #line = line.replace("星河", "TVB星河")                                                        #
    print(line, end="")  #设置end=""，避免输出多余的换行符   
    
#
#从文本中截取少儿段生成新文件#
# 定义关键词
start_keyword = '少儿频道,#genre#'
end_keyword = '省市频道,#genre#'
# 输入输出文件路径
input_file_path = '酒店源.txt'  # 替换为你的输入文件路径
output_file_path = 'sr2.txt'  # 替换为你想要保存输出的文件路径
# 用于存储结果的列表
result_lines = []
# 打开输入文件并读取内容
with open(input_file_path, 'r', encoding='utf-8') as file:
    capture = False  # 用于控制是否开始捕获行
    for line in file:
        # 检查是否到达开始关键词
        if start_keyword in line:
            capture = True
        # 如果已经开始捕获，并且到达结束关键词，则停止捕获
        elif end_keyword in line and capture:
            break
        # 如果处于捕获状态，则添加当前行
        if capture:
            result_lines.append(line)
# 将结果写入输出文件
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.writelines(result_lines)
print('提取完成，结果已保存到:', output_file_path)
#
#从文本中截取省市段生成两个新文件#
#  获取远程港澳台直播源文件，打开文件并输出临时文件并替换关键词
url = "https://raw.githubusercontent.com/frxz751113/AAAAA/main/IPTV/汇总.txt"          #源采集地址
r = requests.get(url)
open('TW.txt','wb').write(r.content)         #打开源文件并临时写入
for line in fileinput.input("TW.txt", inplace=True):   #打开临时文件原地替换关键字
    line = line.replace("﻿Taiwan,#genre#", "")                         #编辑替换字
    line = line.replace("﻿amc", "AMC")                         #编辑替换字
    line = line.replace("﻿中文台", "中文")                         #编辑替换字
    print(line, end="")                                     #加入此行去掉多余的转行符
# 定义关键词
start_keyword = '省市频道,#genre#'
end_keyword = '港澳频道,#genre#'
# 输入输出文件路径
input_file_path = 'TW.txt'  # 替换为你的输入文件路径
output_file_path = 'a.txt'  # 替换为你想要保存输出的文件路径
deleted_lines_file_path = 'df0.txt'  # 替换为你想要保存删除行的文件路径
# 标记是否处于要删除的行范围内
delete_range = False
# 存储要删除的行，包括开始关键词行
deleted_lines = []
# 读取原始文件并过滤掉指定范围内的行
with open(input_file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()
# 过滤掉不需要的行
filtered_lines = []
for line in lines:
    if start_keyword in line:
        delete_range = True
        deleted_lines.append(line)  # 将开始关键词行添加到删除行列表
        continue
    if delete_range:
        if end_keyword in line:
            delete_range = False
            filtered_lines.append(line)  # 将结束关键词行添加到输出文件列表
        else:
            deleted_lines.append(line)  # 添加到删除行列表
    else:
        filtered_lines.append(line)
# 将过滤后的内容写入新文件
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.writelines(filtered_lines)
# 将删除的行写入到新的文件中
with open(deleted_lines_file_path, 'w', encoding='utf-8') as file:
    file.writelines(deleted_lines)
print('过滤完成，结果已保存到:', output_file_path)
print('删除的行已保存到:', deleted_lines_file_path)


#
#从文本中截取少儿段并生成两个新文件#
# 定义关键词
start_keyword = '少儿频道,#genre#'
end_keyword = '港澳频道,#genre#'
# 输入输出文件路径
input_file_path = 'a.txt'  # 替换为你的输入文件路径
output_file_path = 'a0.txt'  # 替换为你想要保存输出的文件路径
deleted_lines_file_path = 'sr1.txt'  # 替换为你想要保存删除行的文件路径
# 标记是否处于要删除的行范围内
delete_range = False
# 存储要删除的行，包括开始关键词行
deleted_lines = []
# 读取原始文件并过滤掉指定范围内的行
with open(input_file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()
# 过滤掉不需要的行
filtered_lines = []
for line in lines:
    if start_keyword in line:
        delete_range = True
        deleted_lines.append(line)  # 将开始关键词行添加到删除行列表
        continue
    if delete_range:
        if end_keyword in line:
            delete_range = False
            filtered_lines.append(line)  # 将结束关键词行添加到输出文件列表
        else:
            deleted_lines.append(line)  # 添加到删除行列表
    else:
        filtered_lines.append(line)
# 将过滤后的内容写入新文件
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.writelines(filtered_lines)
# 将删除的行写入到新的文件中
with open(deleted_lines_file_path, 'w', encoding='utf-8') as file:
    file.writelines(deleted_lines)
print('过滤完成，结果已保存到:', output_file_path)
print('删除的行已保存到:', deleted_lines_file_path)
#
#
        
#合并所有频道文件#
# 读取要合并的频道文件，并生成临时文件#合并所有频道文件#
file_contents = []
file_paths = ["a0.txt", "港澳.txt", "b.txt", "df0.txt", "f.txt", "f1.txt"]  # 替换为实际的文件路径列表#
for file_path in file_paths:                                                             #
    with open(file_path, 'r', encoding="utf-8") as file:                                 #
        content = file.read()
        file_contents.append(content)
# 生成合并后的文件
with open("综合源.txt", "w", encoding="utf-8") as output:
    output.write(''.join(file_contents))   #加入\n则多一空行
#去重#
#去重#
with open('综合源.txt', 'r', encoding="utf-8") as file:
 lines = file.readlines()
# 使用列表来存储唯一的行的顺序 
 unique_lines = [] 
 seen_lines = set() 
# 遍历每一行，如果是新的就加入unique_lines 
for line in lines:
 if line not in seen_lines:
  unique_lines.append(line)
  seen_lines.add(line)
# 将唯一的行写入新的文档 
with open('综合源.txt', 'w', encoding="utf-8") as file:
 file.writelines(unique_lines)
#再次规范频道名#
#从整理好的文本中进行特定关键词替换以规范频道名#
for line in fileinput.input("综合源.txt", inplace=True):   #打开临时文件原地替换关键字
    line = line.replace("CCTV1,", "CCTV1-综合,")  
    line = line.replace("CCTV2,", "CCTV2-财经,")  
    line = line.replace("CCTV3,", "CCTV3-综艺,")  
    line = line.replace("CCTV4,", "CCTV4-国际,")  
    line = line.replace("CCTV5,", "CCTV5-体育,")  
    line = line.replace("CCTV5+,", "CCTV5-体育plus,")  
    line = line.replace("CCTV6,", "CCTV6-电影,")  
    line = line.replace("CCTV7,", "CCTV7-军事,")  
    line = line.replace("CCTV8,", "CCTV8-电视剧,")  
    line = line.replace("CCTV9,", "CCTV9-纪录,")  
    line = line.replace("CCTV10,", "CCTV10-科教,")  
    line = line.replace("CCTV11,", "CCTV11-戏曲,")  
    line = line.replace("CCTV11+,", "CCTV11-戏曲,")  
    line = line.replace("CCTV12,", "CCTV12-社会与法,")  
    line = line.replace("CCTV13,", "CCTV13-新闻,")  
    line = line.replace("CCTV14,", "CCTV14-少儿,")  
    line = line.replace("CCTV15,", "CCTV15-音乐,")  
    line = line.replace("CCTV16,", "CCTV16-奥林匹克,")  
    line = line.replace("CCTV17,", "CCTV17-农业农村,") 
    line = line.replace("CCTV风", "风")  
    line = line.replace("CCTV兵", "兵")  
    line = line.replace("CCTV世", "世")  
    line = line.replace("CCTV女", "女")  
    line = line.replace("008广", "广")
    line = line.replace(" ", "")
    line = line.replace("家庭电影", "家庭影院")    
    line = line.replace("CHC", "")  
    line = line.replace("科技生活", "科技")  
    line = line.replace("财经生活", "财经")  
    line = line.replace("新闻综合", "新闻")  
    line = line.replace("公共新闻", "公共")  
    line = line.replace("经济生活", "经济")  
    line = line.replace("频道1", "频道") 
    line = line.replace("省市频道", "湖北频道")    
    line = line.replace("[720p]", "") 
    line = line.replace("[1080p]", "")     
    print(line, end="")   
#简体转繁体#
#简体转繁体
# 创建一个OpenCC对象，指定转换的规则为繁体字转简体字
converter = OpenCC('t2s.json')#繁转简
#converter = OpenCC('s2t.json')#简转繁
# 打开txt文件
with open('综合源.txt', 'r', encoding='utf-8') as file:
    traditional_text = file.read()
# 进行繁体字转简体字的转换
simplified_text = converter.convert(traditional_text)
# 将转换后的简体字写入txt文件
with open('综合源.txt', 'w', encoding='utf-8') as file:
    file.write(simplified_text)
#TXT转M3U#
def txt_to_m3u(input_file, output_file):
    # 读取txt文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # 打开m3u文件并写入内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U x-tvg-url="https://live.fanmingming.com/e.xml" catchup="append" catchup-source="?playseek=${(b)yyyyMMddHHmmss}-${(e)yyyyMMddHHmmss}"\n')
        # 初始化genre变量
        genre = ''
        # 遍历txt文件内容
        for line in lines:
            line = line.strip()
            if "," in line:  # 防止文件里面缺失“,”号报错
                # if line:
                # 检查是否是genre行
                channel_name, channel_url = line.split(',', 1)
                if channel_url == '#genre#':
                    genre = channel_name
                    print(genre)
                else:
                    # 将频道信息写入m3u文件
                    f.write(f'#EXTINF:-1 tvg-logo="https://live.fanmingming.com/tv/{channel_name}.png" group-title="{genre}",{channel_name}\n')
                    f.write(f'{channel_url}\n')
# 将txt文件转换为m3u文件
txt_to_m3u('综合源.txt', '综合源.m3u')
#任务结束，删除不必要的过程文件#
files_to_remove = ['组播源.txt', "TW.txt", "a.txt", "a0.txt", "b.txt", "b1.txt", "港澳.txt", "df0.txt", "df.txt", "df1.txt", "sr1.txt", "sr2.txt", \
                   "c2.txt", "c1.txt", "DD.txt", "f.txt", "f1.txt", "酒店源#.txt"]
for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
    else:              # 如果文件不存在，则提示异常并打印提示信息
        print(f"文件 {file} 不存在，跳过删除。")
print("任务运行完毕，分类频道列表可查看文件夹内综合源.txt文件！")
