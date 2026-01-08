# !/bin/env python3
# -*- coding: utf-8 -*
# """
# cron: 5 9 * * * hangzhou_spider.py
# new Env('杭州租房');
# """
from douban_scraper import DoubanScraper
import time

summary_list = []

# 用户黑名单（可根据需要添加）
user_black_list = []

processed_links = set()


def filter_content(item: dict) -> bool:
    """
    过滤内容

    Args:
        item: 帖子信息字典
    Returns:
        bool: True 表示通过过滤，False 表示被过滤掉
    """
    # 检查作者名中是否包含关键词
    if "租" in item['author'] or "豆友" in item['author'] or "公寓" in item['author']:
        return False
    # 检查链接是否已经处理过
    if item['link'] in processed_links:
        return False
    # 检查用户是否在黑名单中
    if item['author'] in user_black_list:
        return False

    # 排除项关键词检查
    blackList = [
        "女生", "房源", "公积金", "居住证", "钥匙", "别墅",
        "求租", "预算", "有没有", "求整租",
        # 高价过滤（超过3000的）
        "9000", "8900", "8800", "8700", "8600", "8500", "8400", "8300", "8200", "8100",
        "8000", "7900", "7800", "7700", "7600", "7500", "7400", "7300", "7200", "7100",
        "7000", "6900", "6800", "6700", "6600", "6500", "6400", "6300", "6200", "6100",
        "6000", "5900", "5800", "5700", "5600", "5500", "5400", "5300", "5200", "5100",
        "5000", "4900", "4800", "4700", "4600", "4500", "4400", "4300", "4200", "4100",
        "4000", "3900", "3800", "3700", "3600", "3500", "3400", "3300", "3200", "3100",
        "3000",
    ]

    for keyword in blackList:
        if keyword in item['title']:
            return False

    # 最优先站点 - 五常站和荆长路
    top_priority_stations = ["五常", "荆长路"]
    is_top_priority = any(station in item['title'] for station in top_priority_stations)

    # 偏好区域白名单 - 5号线和19号线沿线区域
    # 如果标题包含这些站点，则保留
    preferred_stations = [
        # 5号线站点
        "5号线", "五号线",
        "金星", "绿汀路", "葛巷", "创景路", "良睦路", "杭师大仓前", "永福路", "五常",
        "蒋村", "浙大紫金港", "三坝", "萍水街", "和睦", "大运河", "拱宸桥东", "善贤",
        "西文街", "东新园", "杭氧", "打铁关", "宝善桥", "建国北路", "万安桥", "城站",
        "江城路", "候潮门", "南星桥", "长河", "聚才路", "江晖路", "滨康路", "博奥路",
        "金鸡路", "人民广场", "育才北路", "通惠中路", "火车南站", "双桥", "姑娘桥",
        # 19号线站点（机场快线）
        "19号线", "十九号线", "机场快线",
        "苕溪", "火车西站", "海创园", "荆长路", "西溪湿地北", "五联", "文三路",
        "沈塘桥", "西湖文化广场", "驿城路", "火车东站", "御道", "平澜路", "耕文路",
        "知行路", "萧山国际机场", "永盛路",
    ]

    # 检查是否包含偏好站点（如果包含，优先保留）
    has_preferred = any(station in item['title'] for station in preferred_stations)

    # 排除其他地铁线（非5号线和19号线）
    other_lines = [
        "1号线", "一号线", "2号线", "二号线", "3号线", "三号线", "4号线", "四号线",
        "6号线", "六号线", "7号线", "七号线", "8号线", "八号线", "9号线", "九号线",
        "10号线", "十号线", "16号线", "十六号线",
    ]

    # 如果明确提到其他线路且没有提到偏好线路，则过滤
    for line in other_lines:
        if line in item['title'] and not has_preferred:
            return False

    # 排除偏远区域
    remote_areas = [
        "临安", "富阳", "桐庐", "淳安", "建德",
    ]
    for area in remote_areas:
        if area in item['title']:
            return False

    return True


def print_discussions(discussions: list):
    """打印讨论列表"""

    for item in discussions:
        if filter_content(item):
            print(item['title'] + '\t\t' + item['time'] + '\t\t' + item['author'] + '\t\t' + item['link'])
            processed_links.add(item['link'])
            summary_list.append(item)


def get_top_summary(start: int = 0, max_items: int = 20, max_pages: int = 6):
    """
    获取租房信息摘要

    Args:
        start: 起始位置
        max_items: 最大获取条目数
        max_pages: 最大页数限制
    """
    scraper = DoubanScraper()
    # 杭州租房小组列表
    hangzhou_groups = [
        'hangzhouzu',  # 杭州租房
        '571home',     # 杭州租房小组
    ]

    try:
        for group_id in hangzhou_groups:
            print(f"\n=== 正在爬取小组: {group_id} ===")
            current_page = start
            while len(summary_list) < max_items and current_page < max_pages * 25:
                page_num = current_page // 25
                # 获取当前页数据
                discussions = scraper.get_group_discussions(group_id, page_num)
                if not discussions:
                    print("未获取到数据，可能是页面结构变化或反爬限制")
                    break
                print_discussions(discussions)
                # 更新页码
                current_page += 25
                # 添加延时，避免请求过快
                time.sleep(7)

            if len(summary_list) >= max_items:
                break

    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
    finally:
        scraper.close()


if __name__ == '__main__':
    processed_links = set()
    summary_list = []
    get_top_summary()
