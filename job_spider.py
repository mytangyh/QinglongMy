#!/bin/env python3
# -*- coding: utf-8 -*-
"""
cron: 1 * * * * job_spider.py
new Env('远程工作');
"""

import asyncio
import json
import sqlite3
import requests
from dotenv import load_dotenv

import sendNotify
from sendNotify import is_product_env, dingding_bot_with_key
from ai_utils import AIHelper

key_name = "job"
load_dotenv()

# 数据库初始化
conn = sqlite3.connect(f'{key_name}.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS titles (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        state TEXT NOT NULL
    )
''')
conn.commit()


def get_db_data():
    cursor.execute('SELECT * FROM titles')
    return cursor.fetchall()


def insert_db(job_list):
    tuples_list = [(x['title'], x['state']) for x in job_list]
    cursor.executemany('INSERT OR REPLACE INTO titles (name, state) VALUES (?, ?)', tuples_list)
    conn.commit()


def close_db():
    if cursor:
        cursor.close()
    if conn:
        conn.close()


def filter_item(job_item, db_titles):
    title = f"[{job_item['postTitle'].lower().strip()}]({job_item['url']})"
    state = f"{job_item['descContent']}\n{job_item['source']} {job_item['salary']} {job_item['jobType']}\n"

    if any(title == row[1] for row in db_titles):
        print("重复已忽略:", title)
        return None

    keywords = "android 安卓 客户端 app python java".split()
    if any(word in title for word in keywords):
        return {'title': title, 'state': state}
    return None


def get_hot_search():
    url = 'https://easynomad.cn/api/posts/list?limit=15&page=1&jobCategory=%E5%BC%80%E5%8F%91&contractType='
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    elements = resp.json().get('data', [])
    db_titles = get_db_data()

    valid_items = []
    for job_item in elements:
        result = filter_item(job_item, db_titles)
        if result:
            print("有效职位:", result['title'])
            valid_items.append(result)
    return valid_items


def build_prompt(job_items):
    prompt_prefix = (
        "你是一个远程职位分析助手，请完成以下任务：\n"
        "1. 将英文内容翻译为中文。\n"
        "2. 评估每个职位的技术要求，从 1 到 10 打分，数字越高表示越难。\n"
        "3. 每个职位请按照以下 JSON 格式返回：\n\n"
        "```\n"
        "[\n"
        "  {\n"
        "    \"title\": \"职位标题\",\n"
        "    \"href\": \"原始链接\",\n"
        "    \"score\": 7,\n"
        "    \"text\": \"职位内容分析和中文翻译\",\n"
        "    \"src_list\": [\"图片URL1\", \"图片URL2\"]\n"
        "  },\n"
        "  ...\n"
        "]\n"
        "```\n\n"
        "请严格按照上述 JSON 格式返回，不要包含任何额外解释、标注或 markdown 语法。\n"
        "以下是待分析的职位内容：\n"
    )

    jobs_text = ""
    for i, item in enumerate(job_items, start=1):
        jobs_text += (
            f"\n---\n"
            f"职位 {i}\n"
            f"标题：{item['title']}\n"
            f"内容：{item['state']}\n"
        )

    return prompt_prefix + jobs_text


def parse_ai_response(json_response):
    try:
        json_data = json.loads(json_response)
        markdown_text = ""
        for item in json_data:
            title = item.get("title", "未知标题")
            href = item.get("href", "#")
            score = item.get("score", "")
            text = item.get("text", "")
            images = item.get("src_list", [])

            markdown_text += f"\n##### [{title} {score}]({href})\n{text}\n"
            for img in images:
                markdown_text += f"![]({img})\n"
        return markdown_text, json_data[0].get("title", "Job Summary")
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        print("解析 AI 响应失败:", e)
        return "⚠️ 无法解析 AI 返回内容。", "AI分析失败"


def notify_markdown(summary_list):
    if not summary_list:
        print("暂无 job！！")
        return

    helper = AIHelper()
    prompt = build_prompt(summary_list)
    json_response = asyncio.run(helper.analyze_content("", prompt))
    markdown_text, summary = parse_ai_response(json_response)

    if is_product_env():
        insert_db(summary_list)

    sendNotify.dingding_bot("job", markdown_text)

    with open(f"log_{key_name}.md", 'w', encoding='utf-8') as f:
        f.write(markdown_text)


if __name__ == '__main__':
    try:
        jobs = get_hot_search()
        notify_markdown(jobs)
    finally:
        close_db()
