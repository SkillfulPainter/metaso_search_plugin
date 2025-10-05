"""Metaso Search API implementation for MCP server

This module provides web search and academic search functionality using Metaso Search API.
It includes both the API implementation and tool descriptions.
"""

from typing import List, Tuple, Type, Any
import warnings
import sys
from pathlib import Path
import time
from .metaso.client import MetasoClient
import json
import re
from bs4 import BeautifulSoup
from src.common.logger import get_logger
from src.plugin_system import (
    BasePlugin,
    BaseTool,
    register_plugin,
    ComponentInfo,
    ConfigField,
    ToolParamType,
)

logger = get_logger("search_metaso")

# 速率限制配置
RATE_LIMIT = {
    "per_second": 1,
    "per_minute": 60
}

request_count = {
    "second": 0,
    "minute": 0,
    "last_reset": time.time(),
    "last_minute_reset": time.time()
}

# 配置 Windows asyncio 事件循环
if sys.platform == 'win32':
    # 忽略 ResourceWarning
    warnings.filterwarnings("ignore", category=ResourceWarning)

class MetasoSearchTool(BaseTool):
    """从秘塔上搜索相关内容工具"""
    name = "metaso_search"
    description = ("当用户需要你进行搜索获取需要在网上搜索的信息，如即时性信息时，使用此工具进行网页搜索。"
                   "用于从公开互联网上获取信息。当用户的查询涉及新闻动态、天气、股价等即时性内容，或需要了解人物、事件、通用概念等公开领域的知识时，使用此工具。"
                )
    parameters = [
        ("query", ToolParamType.STRING, "搜索关键词，结合用户或你自己的要求从聊天记录中总结，需包含所有核心需求，越详细越好", True, None),
    ]

    available_for_llm = True


    def remove_brackets(self, text):
        # 移除圆括号及其内容
        while True:
            new_text = re.sub(r'\([^()]*\)', '', text)
            if new_text == text:
                break
            text = new_text
        # 移除中括号及其内容
        while True:
            new_text = re.sub(r'\[[^\[\]]*\]', '', text)
            if new_text == text:
                break
            text = new_text
        return text


    async def _clean_html(self, raw_html: str) -> str:
        """彻底清理 HTML 标签和实体"""
        soup = BeautifulSoup(raw_html, "html.parser")
        # 移除所有脚本和样式
        for script in soup(["script", "style", "noscript", "meta", "link"]):
            script.decompose()
        # 获取纯文本并保留段落结构
        text = soup.get_text(separator="\n\n", strip=True)
        return text.replace("&ensp;", " ").replace("&emsp;", " ").replace("\xa0", " ")


    async def execute(self, function_args: dict[str, Any]) -> dict[str, Any]:
        metaso_uid = self.get_config("credentials.uid")
        metaso_sid = self.get_config("credentials.sid")
        default_model = self.get_config("settings.default_model", "concise")
        is_scholar = self.get_config("settings.default_scholar", False)

        if not metaso_uid or not metaso_sid:
            raise ValueError("请在 metaso_search_plugin 的 config.toml 文件中配置 Metaso UID 和 SID")

        browser_data_dir = Path(__file__).parent / "metaso/browser_data"
        browser_data_dir.mkdir(parents=True, exist_ok=True)
        client = MetasoClient(
            metaso_uid,
            metaso_sid,
            browser_data_dir=str(browser_data_dir)
        )
        models = {
            "web": {"concise": "concise", "detail": "detail"},
            "scholar": {"concise": "concise-scholar", "detail": "detail-scholar"}
        }
        model_type = "scholar" if is_scholar else "web"
        model = models[model_type][default_model]

        """检查并更新速率限制"""
        if type(function_args) == str:
            function_args = json.loads(function_args)

        now = time.time()
        
        # 重置秒级计数器
        if now - request_count["last_reset"] > 1:
            request_count["second"] = 0
            request_count["last_reset"] = now
            
        # 重置分钟级计数器
        if now - request_count["last_minute_reset"] > 60:
            request_count["minute"] = 0
            request_count["last_minute_reset"] = now
        
        if (request_count["second"] >= RATE_LIMIT["per_second"] or 
            request_count["minute"] >= RATE_LIMIT["per_minute"]):
            raise Exception("超出速率限制")
        
        request_count["second"] += 1
        request_count["minute"] += 1

        """执行搜索"""
        # 确定使用的模型
        query = function_args.get("query")
        if not query:
            return {"name": self.name, "content": "搜索失败: 未提供搜索关键词 'query'"}

        logger.info(f"开始秘塔搜索: {query}")
        query_1 = query + "（简单介绍其具体内容，类型，回复限制在200字内，若有具体数据，需包含适当数据）"
        try:
            # 使用MetasoClient执行搜索
            async with client as c:  # 使用上下文管理器
                result = await c.get_completion(query_1, model=model)
                
                # 处理返回结果
                content = f"**在你这次回复之前，你已经上网搜索了关键词”{query}“，搜到了以下内容：**\n\n"
                content1 = result.get("content", "")
                content += self.remove_brackets(content1)
                content += "\n\n若以上内容与本次对话有关，则进行参考。若无关，忽略。"
                if not content1:
                    raise Exception("API返回内容为空")
                references = result.get("references", [])
                # 格式化输出
                output = [content]

                for i, ref in enumerate(references, 1):
                    output.append(
                        f"\n    链接: {ref.get('link', '无链接')}"
                        f"\n    来源: {ref.get('source', '未知来源')}"
                        f"\n    日期: {ref.get('date', '未知日期')}"
                    )

                logger.info(f"search_metaso结果: {content}")
                return {
                    "name": "search_metaso",
                    "content": "\n".join(output)
                }     
                
        except Exception as e:
            logger.error(f"秘塔搜索执行失败: {str(e)}")
            return {
                "name": "search_metaso",
                "content": f"秘塔搜索失败: {str(e)}"
            }

@register_plugin
class MetasoSearchPlugin(BasePlugin):
    """Metaso秘塔搜索插件"""

    # 插件基本信息
    plugin_name: str = "metaso_search_plugin"
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = ["beautifulsoup4"] # 示例依赖
    config_file_name: str = "config.toml"

    # 配置节描述
    config_section_descriptions = {
        "plugin": "插件基本信息",
        "credentials": "Metaso API 认证凭证 (必须填写)",
        "settings": "搜索相关设置"
    }

    # 配置Schema定义
    config_schema: dict = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
        },
        "credentials": {
            "uid": ConfigField(type=str, default="", description="你自己的秘塔uid，教程https://github.com/fengin/search-server"),
            "sid": ConfigField(type=str, default="", description="你自己的秘塔sid，教程https://github.com/fengin/search-server"),
        },
        "settings": {
            "default_model": ConfigField(type=str, default="detail", description='默认搜索模式: "concise" (简洁) 或 "detail" (深入)'),
            "default_scholar": ConfigField(type=bool, default=False, description="默认是否为学术搜索"),
        }
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """注册插件的全部组件"""
        return [
            (MetasoSearchTool.get_tool_info(), MetasoSearchTool)
        ]

