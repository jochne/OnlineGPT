# search_engines.py
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from utils import get_page_content
import charset_normalizer

def get_google_search_results(query, num_results=5, worker=None):
    """
    获取Google搜索结果，并爬取每个结果页面的内容。
    """
    query_encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={query_encoded}&num={num_results}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    logging.info(f"发送请求到Google URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 获取Content-Type并检查是否为HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logging.error(f"搜索结果页面非HTML内容: {url}，Content-Type: {content_type}")
            raise Exception("搜索结果页面非HTML内容")

        # 使用charset-normalizer检测编码
        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'

        # 使用检测到的编码解码内容
        text = response.content.decode(encoding, errors='replace')
        logging.info(f"检测到编码: {encoding}，Google搜索结果页面URL: {url}")
    except requests.RequestException as e:
        logging.error(f"请求Google失败：{e}")
        raise Exception(f"请求Google失败：{e}")
    except Exception as e:
        logging.error(f"解码Google搜索结果页面失败：{e}")
        raise Exception(f"解码Google搜索结果页面失败：{e}")

    soup = BeautifulSoup(text, 'html.parser')

    results = []

    # 根据Google当前的HTML结构进行解析
    for g in soup.find_all('div', class_='tF2Cxc'):
        # 提取标题
        title_tag = g.find('h3')
        title = title_tag.get_text(separator=' ', strip=True) if title_tag else "No title"

        # 提取URL
        link_tag = g.find('a')
        link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "No link"

        # 提取摘要内容
        snippet = ""
        possible_snippet_classes = ['VwiC3b', 'IsZvec', 'aCOpRe']
        for cls in possible_snippet_classes:
            snippet_tag = g.find('div', class_=cls)
            if snippet_tag:
                snippet = snippet_tag.get_text(separator=' ', strip=True)
                break
        if not snippet:
            snippet_tag = g.find('span', class_='aCOpRe')
            if snippet_tag:
                snippet = snippet_tag.get_text(separator=' ', strip=True)
        if not snippet:
            snippet = "No content"

        if snippet == "No content":
            logging.debug(f"未能提取到Google摘要内容，尝试其他方法。")

        results.append({
            'title': title,
            'link': link,
            'snippet': snippet,
            'content': "正在获取内容...",
            'engine': 'Google'  # 添加搜索引擎标识
        })

        if len(results) >= num_results:
            break
    logging.info(f"解析出 {len(results)} 个Google搜索结果。")

    # 使用线程池并行抓取每个链接的内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_result = {}
        for result in results:
            if worker and not worker.is_running:
                logging.info("抓取内容任务被中断。")
                break
            future = executor.submit(get_page_content, result['link'], worker)
            future_to_result[future] = result

        for future in as_completed(future_to_result):
            if worker and not worker.is_running:
                logging.info("抓取内容任务被中断。")
                break
            result = future_to_result[future]
            try:
                content = future.result()
                result['content'] = content
            except Exception as e:
                logging.error(f"抓取内容时出错 ({result['link']}): {e}")
                result['content'] = "无法获取内容"

    return results

def get_bing_search_results(query, num_results=5, worker=None):
    """
    获取Bing搜索结果，并爬取每个结果页面的内容。
    """
    query_encoded = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/search?q={query_encoded}&count={num_results}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    logging.info(f"发送请求到Bing URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 获取Content-Type并检查是否为HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logging.error(f"搜索结果页面非HTML内容: {url}，Content-Type: {content_type}")
            raise Exception("搜索结果页面非HTML内容")

        # 使用charset-normalizer检测编码
        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'

        # 使用检测到的编码解码内容
        text = response.content.decode(encoding, errors='replace')
        logging.info(f"检测到编码: {encoding}，Bing搜索结果页面URL: {url}")
    except requests.RequestException as e:
        logging.error(f"请求Bing失败：{e}")
        raise Exception(f"请求Bing失败：{e}")
    except Exception as e:
        logging.error(f"解码Bing搜索结果页面失败：{e}")
        raise Exception(f"解码Bing搜索结果页面失败：{e}")

    soup = BeautifulSoup(text, 'html.parser')

    results = []

    # 根据Bing当前的HTML结构进行解析
    for li in soup.find_all('li', class_='b_algo'):
        # 提取标题和链接
        h2 = li.find('h2')
        if h2 and h2.find('a'):
            a_tag = h2.find('a')
            title = a_tag.get_text(separator=' ', strip=True)
            link = a_tag['href']
        else:
            title = "No title"
            link = "No link"

        # 提取摘要
        snippet_tag = li.find('p')
        snippet = snippet_tag.get_text(separator=' ', strip=True) if snippet_tag else "No content"

        results.append({
            'title': title,
            'link': link,
            'snippet': snippet,
            'content': "正在获取内容...",
            'engine': 'Bing'  # 添加搜索引擎标识
        })

        if len(results) >= num_results:
            break
    logging.info(f"解析出 {len(results)} 个Bing搜索结果。")

    # 使用线程池并行抓取每个链接的内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_result = {}
        for result in results:
            if worker and not worker.is_running:
                logging.info("抓取内容任务被中断。")
                break
            future = executor.submit(get_page_content, result['link'], worker)
            future_to_result[future] = result

        for future in as_completed(future_to_result):
            if worker and not worker.is_running:
                logging.info("抓取内容任务被中断。")
                break
            result = future_to_result[future]
            try:
                content = future.result()
                result['content'] = content
            except Exception as e:
                logging.error(f"抓取内容时出错 ({result['link']}): {e}")
                result['content'] = "无法获取内容"

    return results

def get_baidu_search_results(query, num_results=5, worker=None):
    """
    获取百度搜索结果，并爬取每个结果页面的内容。
    """
    query_encoded = urllib.parse.quote_plus(query)
    url = f"https://www.baidu.com/s?wd={query_encoded}&rn={num_results}&ie=utf-8"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    logging.info(f"发送请求到百度 URL: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 获取Content-Type并检查是否为HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logging.error(f"搜索结果页面非HTML内容: {url}，Content-Type: {content_type}")
            raise Exception("搜索结果页面非HTML内容")

        # 使用charset-normalizer检测编码
        detected = charset_normalizer.from_bytes(response.content).best()
        encoding = detected.encoding if detected and detected.encoding else 'utf-8'

        # 使用检测到的编码解码内容
        text = response.content.decode(encoding, errors='replace')
        logging.info(f"检测到编码: {encoding}，百度搜索结果页面URL: {url}")
    except requests.RequestException as e:
        logging.error(f"请求百度失败：{e}")
        raise Exception(f"请求百度失败：{e}")
    except Exception as e:
        logging.error(f"解码百度搜索结果页面失败：{e}")
        raise Exception(f"解码百度搜索结果页面失败：{e}")

    soup = BeautifulSoup(text, 'html.parser')

    results = []

    # 根据百度当前的HTML结构进行解析
    for div in soup.find_all('div', class_='result'):
        h3 = div.find('h3')
        if h3 and h3.find('a'):
            a_tag = h3.find('a')
            title = a_tag.get_text(separator=' ', strip=True)
            link = a_tag['href']
        else:
            title = "No title"
            link = "No link"

        # 提取摘要
        snippet_tag = div.find('div', class_='c-abstract')
        if not snippet_tag:
            snippet_tag = div.find('div', class_='c-span18 c-span-last')
        snippet = snippet_tag.get_text(separator=' ', strip=True) if snippet_tag else "No content"

        results.append({
            'title': title,
            'link': link,
            'snippet': snippet,
            'content': "正在获取内容...",
            'engine': '百度'  # 添加搜索引擎标识
        })

        if len(results) >= num_results:
            break
    logging.info(f"解析出 {len(results)} 个百度搜索结果。")

    # 使用线程池并行抓取每个链接的内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_result = {}
        for result in results:
            if worker and not worker.is_running:
                logging.info("抓取内容任务被中断。")
                break
            future = executor.submit(get_page_content, result['link'], worker)
            future_to_result[future] = result

        for future in as_completed(future_to_result):
            if worker and not worker.is_running:
                logging.info("抓取内容任务被中断。")
                break
            result = future_to_result[future]
            try:
                content = future.result()
                result['content'] = content
            except Exception as e:
                logging.error(f"抓取内容时出错 ({result['link']}): {e}")
                result['content'] = "无法获取内容"

    return results