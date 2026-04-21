"""LLM配置文件

本文件负责初始化和配置聊天模型，是整个系统中LLM调用的唯一入口。

业务背景：系统需要与多种LLM提供商（如OpenAI、Anthropic、本地模型等）进行交互，
通过统一的配置机制，可以灵活切换不同的模型提供商和模型版本。

配置方式：通过环境变量读取配置，支持的环境变量包括：
- MODEL_PROVIDER: 模型提供商（如 openai, anthropic, ollama 等）
- MODEL_NAME: 模型名称（如 gpt-4o, claude-3-sonnet 等）
- BASE_URL: 模型API的基础URL（用于本地模型或代理）
- API_KEY: 模型API的密钥

设计特点：
- 单例模式：整个系统共享一个chat_model实例
- 环境变量驱动：便于不同环境（开发、测试、生产）使用不同配置
- 统一接口：通过LangChain的init_chat_model统一管理不同提供商
"""

# 导入LangChain的模型初始化函数
from langchain.chat_models import init_chat_model
# 导入操作系统模块，用于读取环境变量
import os
# 导入dotenv模块，用于加载.env文件中的环境变量
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

"""初始化聊天模型

使用LangChain的init_chat_model函数创建统一的LLM实例。
所有参数通过环境变量配置，实现灵活的模型切换。

配置参数：
- model_provider: 模型提供商标识
- model: 具体模型名称
- base_url: API基础URL（可选，用于本地模型或自定义端点）
- api_key: API密钥（可选，部分提供商不需要）

返回：
- chat_model: 统一的LangChain聊天模型实例，可被其他模块导入使用
"""
chat_model = init_chat_model(
    model_provider=os.getenv("MODEL_PROVIDER"),  # 从环境变量获取模型提供商
    model=os.getenv("MODEL_NAME"),              # 从环境变量获取模型名称
    base_url=os.getenv("BASE_URL"),              # 从环境变量获取API基础URL
    api_key=os.getenv("API_KEY"),                # 从环境变量获取API密钥
)