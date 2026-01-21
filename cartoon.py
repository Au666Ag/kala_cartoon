import os
import requests
from lxml import etree
import time
import random




# 设置伪装头，模拟浏览器访问
def header(referer):
    headers = {
        "Referer": f"{referer}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "sec-ch-ua":'"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24',
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0",
    }
    return headers

# 创建会话对象
session = requests.Session()
session.headers.update()

# 定义一个获得网页HTML的函数
def html(url,referer):
    try:
        # 发送请求，获得响应文本
        response = session.get(url, headers=header(referer),timeout=10)
        response.encoding = "utf-8"
        # 处理429和其他错误
        if response.status_code == 429:
            print(f"⚠️  触发频率限制！等待15秒...")
            time.sleep(15)
            return None  # 返回None而不是False，便于判断

        if response.status_code == 403:
            print(f"❌  访问被拒绝(403)，可能IP被限制")
            return None

        if response.status_code != 200:
            print(f"⚠️  网址：{url} 请求失败，状态码：{response.status_code}")
            return None
        return etree.HTML(response.text)

    except Exception as e:
        print(f"❌  请求出错：{e}")
        return None

# 定义一个函数用于获得详情页网址后缀并合成详情页网址
def detail_url_function(html):
    detail_url_list = []
    # 获取详情页网址的后缀
    detail_url_suffix = html.xpath("/html/body/div[1]/div/div/div[2]/ul/li/div/a/@href")  # 使用contain方法属性多值匹配

    # 获取漫画名称
    cartoon_names = list(html.xpath("/html/body/div[1]/div/div/div[2]/ul/li/div/a/@title"))

    # 合成详情页网址
    for item in detail_url_suffix:
        detail_url = f"{list_url}{item}"
        detail_url_list.append(detail_url)
    return cartoon_names,detail_url_list    # 返回对象是一个列表，列表元素是返回的两返回值

# 定义一个函数获得详情页的HTML和漫画每个章节的网址
def detail_html_function(url,referer):
    chapter_url_list = []
    chapter_names = []
    # 获得详情页的HTML
    detail_html = html(url,referer)

    # 判断详情也有没有被反爬
    if detail_html is None or detail_html == '':
        print("被反爬或页面结构已经变化！！！")
    # 获得该漫画每个章节网址的后缀
    chapter_url_suffix = detail_html.xpath("//div[@id='playlist1']/ul/li/a/@href")
    # 获得漫画每个章节的名称
    chapter_names_list = detail_html.xpath("//div[@id='playlist1']/ul/li/a/text()")
    for i in chapter_names_list:
        chapter_name = i.replace("/", "")
        chapter_names.append(chapter_name)
    # 合成章节网址
    for item in chapter_url_suffix:
        chapter_url = f"{list_url}{item}"
        chapter_url_list.append(chapter_url)

    return chapter_names,chapter_url_list

# 使用selenium应对动态加载
def selenium_function(url):
    from selenium.webdriver.common.action_chains import ActionChains
    import time
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options

    # 使用selenium应对动态加载
    images_src_list = []
    # 模拟按下键盘的Page Down键
    def slide(browser):
        while True:
            # 记录滚动前的页面高度
            prev_height = browser.execute_script(
                "return document.body.scrollHeight || document.documentElement.scrollHeight")

            # 执行翻页操作
            ActionChains(browser).key_down(Keys.PAGE_DOWN).key_up(Keys.PAGE_DOWN).perform()
            time.sleep(0.2)

            # 获取当前页面高度
            current_height = browser.execute_script(
                "return document.body.scrollHeight || document.documentElement.scrollHeight")

            # 检查是否已到达页面底部
            scroll_position = browser.execute_script("""
                return window.innerHeight + window.pageYOffset >= 
                       Math.max(document.body.scrollHeight, document.documentElement.scrollHeight) - 10
            """)

            # 如果已到达页面底部或页面高度没有变化（没有新内容加载）
            if scroll_position or current_height == prev_height:
                break



    # 指定 chromedriver 的路径
    driver_path = r"D:\pycharm\conda\envs\xuexi\msedgedriver.exe"

    # 设置无头模式
    options = Options()
    options.add_argument("--headless")

    # 初始化 WebDriver
    service = Service(executable_path=driver_path)

    browser = webdriver.Edge(service=service)
    browser.get(url)


    # 获得referer,并没有进入到iframe中
    iframe = browser.find_element(By.XPATH, "//*[@id='playleft']/iframe")
    referer_url = iframe.get_attribute('src')
    print(referer_url)
    # 进入iframe中，获得图片的链接
    browser.switch_to.frame(iframe)

    # 调用下滑函数
    #slide(browser)
    #browser.implicitly_wait(10)
    images_src = browser.find_elements(By.XPATH,"//div[@class='comic-container']/img")

    for i in images_src:
        image_src = i.get_attribute('data-src')
        image_src_url = f"https://image.kalaimg.top{image_src}"
        images_src_list.append(image_src_url)

    # 回到主页面
    browser.switch_to.default_content()

    print(images_src_list)
    # 退出浏览器
    browser.quit()

    return referer_url,images_src_list

# 定义一个用于获得图片的函数
def image(url,referer):

    # 在下载图片前添加随机延迟
    time.sleep(random.uniform(2, 5))
    response = session.get(url,headers=header(referer),timeout=10)
    response.encoding = "utf-8"
    if response.status_code == 200:
        return response.content
    else:
        print(f"图片{url}请求未成功")
    return 0

# 对图片进行保存
def save_image(file_, content):
    with open(file_, 'wb') as file:
        file.write(content)
    print(f"图片已成功保存到 {file_}")



# 主程序
def main(url,referer):
    list_html = html(url,referer=list_url)
    cartoon_names, detail_url_list = detail_url_function(list_html)
    # 随机延迟：2-5秒（模拟真人浏览）
    delay = random.uniform(2, 5)
    time.sleep(delay)
    chapter_names, chapter_url_list = detail_html_function(detail_url_list[0],referer=list_url)
    print(chapter_names,chapter_url_list)
    for j in range(len(cartoon_names)):
        print(f"\n{'=' * 50}")
        print("\n")
        print(f"{cartoon_names[j]}已开始保存")
        print("\n")
        # 创建漫画主文件夹
        comic_folder = f"{cartoon_names[j]}"
        os.makedirs(comic_folder, exist_ok=True)

        for index, chap_url in enumerate(chapter_url_list):
            referer_url, images_url = selenium_function(chap_url)

            # 给每个章节创建文件夹
            chapter_folder = os.path.join(comic_folder, chapter_names[index])
            os.makedirs(chapter_folder, exist_ok=True)
            for i, image_url in enumerate(images_url):
                print(image_url)
                # 获得图片的二进制资源
                content = image(image_url,referer=referer_url)
                file_name = os.path.join(chapter_folder, f"{i:03d}.jpg")
                save_image(file_name, content)
            print("\n")
            print(f"{chapter_names[index]}已完成")
            print("\n")
            print(f"\n{'='*50}")
            print("\n")



if __name__ == '__main__':
    # 目标根网址
    list_url = "https://kalamanhua.com"
    url = "https://kalamanhua.com/type/Ec-----.html"
    main(url,referer=list_url)

