import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List


class DoubanScraper:
    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        })

    def get_group_discussions(self, group_id: str, page: int = 0) -> List[Dict]:
        """获取豆瓣小组讨论列表"""
        try:
            url = f'https://www.douban.com/group/{group_id}/discussion?start={page * 25}'

            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                print(f"页面响应异常: status={response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            discussions = []

            # 尝试新版布局
            topic_items = soup.select('.article .topic-item')
            if topic_items:
                for item in topic_items:
                    title_link = item.select_one('.title a')
                    user_info = item.select_one('.user-info a')
                    time_elem = item.select_one('.time')

                    if title_link:
                        discussions.append({
                            'title': (title_link.get('title') or title_link.get_text()).strip().replace(' ', '').replace('\n', ''),
                            'link': title_link.get('href'),
                            'author': user_info.get_text().strip() if user_info else '',
                            'time': time_elem.get_text().strip() if time_elem else ''
                        })
                return discussions

            # 尝试旧版布局
            rows = soup.select('table.olt tr')
            if rows:
                for row in rows[1:]:  # 跳过表头
                    title_cell = row.select_one('td.title a')
                    author_cell = row.select_one('td:nth-child(2) a')
                    time_cell = row.select_one('td:nth-child(4)')

                    if title_cell:
                        discussions.append({
                            'title': (title_cell.get('title') or title_cell.get_text()).strip().replace(' ', '').replace('\n', ''),
                            'link': title_cell.get('href'),
                            'author': author_cell.get_text().strip() if author_cell else '',
                            'time': time_cell.get_text().strip() if time_cell else ''
                        })
                return discussions

            print("未找到讨论列表，可能页面结构已变化")
            return []

        except Exception as e:
            print(f"爬取失败: {str(e)}")
            return []

    def close(self):
        """关闭会话"""
        self.session.close()


if __name__ == '__main__':
    scraper = DoubanScraper()
    try:
        results = scraper.get_group_discussions('hangzhouzu')
        print(f"获取到 {len(results)} 条讨论")
        with open('discussions.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    finally:
        scraper.close()
