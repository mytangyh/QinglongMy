#!/bin/env python3
# -*- coding: utf-8 -*
import os
import json
import asyncio
from pathlib import Path

from openai import OpenAI

# 添加对 .env 文件的支持
try:
    from dotenv import load_dotenv

    # 优先尝试加载 .env 文件
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("提示: 可以安装 python-dotenv 来使用 .env 文件功能")
    pass
class AIHelper:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        if not self.api_key:
            raise ValueError("API_KEY 环境变量未设置")

        self.base_url = os.getenv('API_URL')
        if not self.base_url:
            raise ValueError("API_URL 环境变量未设置")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    async def chat_completion(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个有帮助的AI助手"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用API时出错: {e}")
            raise

    def clean_response(self, response: str) -> str:
        try:
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError as e:
                    print(f"JSON validation failed: {e}")

            print("Failed to find valid JSON content")
            return response

        except Exception as e:
            print(f"Error in clean_response: {e}")
            return response

    async def analyze_content(self, content: dict, prompt: str) -> str:
        results = []
        try:
            score_response = await self.chat_completion(prompt)
            cleaned_response = self.clean_response(score_response)
            try:
                json.loads(cleaned_response)
                results.append(cleaned_response)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON after cleaning: {e}")
                return json.dumps(content)

        except Exception as e:
            print(f"调用API时出错: {str(e)}")
            print("等待 1 分钟后重试...")
            await asyncio.sleep(60)
            try:
                score_response = await self.chat_completion(prompt)
                cleaned_response = self.clean_response(score_response)
                results.append(cleaned_response)
            except Exception as e:
                print(f"重试时出错: {str(e)}")
                return json.dumps(content)

        return results[0]

# ---------------------- 测试方法 ----------------------
if __name__ == "__main__":
    async def main():
        ai = AIHelper()

        print("=== 调用 chat_completion 测试 ===")
        try:
            response = await ai.chat_completion("你好，请介绍一下你自己。")
            print("chat_completion 返回内容：")
            print(response)
        except Exception as e:
            print("chat_completion 出错：", e)

        print("\n=== 调用 analyze_content 测试 ===")
        try:
            fake_data = {"input": "测试内容"}
            prompt = "请用 JSON 数组格式返回对输入的评分，例如：[{'score': 95, 'comment': '很好'}]"
            result = await ai.analyze_content(fake_data, prompt)
            print("analyze_content 返回内容：")
            print(result)
        except Exception as e:
            print("analyze_content 出错：", e)

    asyncio.run(main())
