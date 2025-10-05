# Metaso 搜索插件 for MaiBot

这是一款为开源聊天机器人框架 [MaiBot](https://github.com/MaiM-with-u/MaiBot.git) 设计的 Metaso (秘塔) 搜索插件。它允许你的 AI 助手接入互联网，获取即时、准确的信息，并能根据需求在网页搜索与学术搜索之间切换。

本项目基于优秀的 [fengin/search-server](https://github.com/fengin/search-server) 项目进行开发，将其强大的搜索能力封装为适用于 MaiBot 的即用型插件。

## ✨ 插件功能

* **网页搜索**：当用户提问涉及新闻、天气、股价等即时性内容，或需要查询公开的人物、事件、概念时，插件会自动从互联网获取信息。
* **学术搜索**：可配置为默认使用学术搜索模式，为研究和学习提供便利。
* **AI 智能总结**：搜索结果由 Metaso 的 AI 进行处理，返回清晰、准确的总结性内容，而非简单的链接列表。
* **高度可配置**：用户可以自由配置搜索模式（简洁/深入）和默认搜索类型（网页/学术）。
* **内置速率限制**：包含简单的请求速率限制，避免对 API 的过度调用。

## 🚀 使用方法

### 1. 安装

1.  下载本插件的所有文件。
2.  将整个插件文件夹放入 MaiBot 项目的 `plugins` 目录下。
3.  安装插件所需的 Python 依赖：
    ```bash
    pip install beautifulsoup4 playwright
    playwright install
    ```

### 2. 配置

插件的正常运行需要你提供自己的 Metaso 凭证。

1.  第一次成功加载插件后，在插件的目录中，找到并打开 `config.toml` 文件（如果不存在，请根据以下内容创建一个）。
2.  填写你的 Metaso `uid` 和 `sid`。

    ```toml
    # config.toml

    [credentials]
    # 你的秘塔 uid
    uid = "在这里填入你的UID"
    
    # 你的秘塔 sid
    sid = "在这里填入你的SID"
    
    [settings]
    # 默认搜索模式: "concise" (简洁) 或 "detail" (深入)
    default_model = "concise"
    
    # 默认是否为学术搜索: true 或 false
    default_scholar = false
    ```

3.  **如何获取 `uid` 和 `sid`？** 请访问并遵循原项目 [fengin/search-server](https://github.com/fengin/search-server) 的教程来获取你的个人凭证。

4.  根据你的需求修改 `[settings]` 部分的默认配置。

### 3. 启用

完成配置后，重新启动 MaiBot。当 MaiBot 判断用户的问题需要联网搜索时，便会自动调用本插件。

## 🙏 致谢

* 感谢 **fengin** 开发了 `search-server`，为本项目提供了核心动力。
* 感谢 **MaiM-with-u** 团队创造了灵活易用的 MaiBot 框架。

## 📄 开源许可

本插件使用 [MIT License](./LICENSE) 开源。