import requests
from bs4 import BeautifulSoup
import time
from lxml import etree
import re
import random
import os

# 设置随机停顿
def random_number():
    number = random.randint(1, 10)
    return number

# 设置伪装头，模拟浏览器访问
def header(referer):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "Referer": f"{referer}"
    }
    return headers

# 定义一个获得网页HTML的函数
def html_detail(url,referer):
    time.sleep(random_number())
    try:
        # 发送请求，获得响应文本
        response = requests.get(url, headers=header(referer), timeout=10)
        response.encoding = "utf-8"
        return etree.HTML(response.text)

    except Exception as e:
        print(f"❌  请求出错：{e}")
        return None


# 定义一个函数获得详情页的HTML和漫画每个章节的网址
def detail_html_function(url,referer):
    chapters_url = []
    chapter_names = []
    # 获得详情页的HTML
    detail_html = html_detail(url,referer)

    # 判断详情也有没有被反爬
    if detail_html is None or detail_html == '':
        print("被反爬或页面结构已经变化！！！")
    # 漫画名称
    cartoon_ = detail_html.xpath("/html/body/div[1]/div/div/div/div/div[1]/div[2]/h1/text()")
    cartoon_name = cartoon_[0]
    # 获得该漫画每个章节网址的后缀
    chapter_url_suffix = detail_html.xpath("//div[@id='playlist1']/ul/li/a/@href")
    # 获得漫画每个章节的名称
    chapter_names_list = detail_html.xpath("//div[@id='playlist1']/ul/li/a/text()")
    for i in chapter_names_list:
        chapter_name = re.sub(r"[/（）、]", "",i)
        chapter_names.append(chapter_name)
    # 合成章节网址
    for item in chapter_url_suffix:
        chapter_url = f"https://kalamanhua.com/{item}"
        chapters_url.append(chapter_url)

    return cartoon_name,chapter_names,chapters_url



def chapter_html(iframe_url,referer):
    time.sleep(random_number())
    html = requests.get(
        iframe_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": referer
        }
    ).text
    return html

# 下载图片
def download(url,iframe_url,file_name):
    time.sleep(random_number())
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": iframe_url
        },
        timeout=10
    )
    with open(file_name, "wb") as f:
        f.write(r.content)
        print(f"{file_name}已保存")


def main():
    url = input("输入漫画详情页网址:")
    root_url = re.match('(https://.*?/).*?',url).group(1)
    cartoon_name,chapter_names,chapters_url = detail_html_function(url,referer=root_url)
    # 创建漫画主文件夹
    comic_folder = f"{cartoon_name}"
    os.makedirs(comic_folder, exist_ok=True)
    for i,chapter_url in enumerate(chapters_url):
        print(f"\n{'=' * 50}")
        print(f"第{i}章开始保存")

        # 给每个章节创建文件夹
        chapter_folder = os.path.join(comic_folder, chapter_names[i])
        os.makedirs(chapter_folder, exist_ok=True)
        chapter_url_html = html_detail(chapter_url,referer=root_url)
        chapter_url_html = etree.tostring(chapter_url_html, encoding='unicode')

        # 提取请求网址
        iframe_url = re.search('var player_aaaa.*?,"url":"(.*?)",',chapter_url_html, re.S).group(1)
        iframe_url = f"https://image.kalaimg.top/play/min/{iframe_url}"
        html = chapter_html(iframe_url,referer=root_url)
        soup = BeautifulSoup(html,"lxml")
        imgs = []
        for img in soup.select("img.comic-img"):
            src = img.get("data-src")
            if not src:
                continue
            if src.startswith("/"):
                src = "https://image.kalaimg.top" + src
            imgs.append(src)
        print("图片数量:", len(imgs))
        for index,img in enumerate(imgs):
            file_name = os.path.join(chapter_folder, f"{index:03d}.jpg")
            download(img,iframe_url,file_name)
        print(f"第{i}章已保存")
if __name__ == "__main__":
    main()