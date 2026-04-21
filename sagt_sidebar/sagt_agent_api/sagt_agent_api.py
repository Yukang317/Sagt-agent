#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAGT Agent API 客户端封装模块

本模块提供与 LangGraph 服务器交互的客户端功能，主要包括：
1. 连接管理：通过 /sagt/get_token 端点获取认证 token，创建客户端连接
2. 助手管理：使用稳定 UUID 生成助手 ID，确保助手的唯一性和可复用性
3. 线程管理：同样使用稳定 UUID 生成线程 ID，确保线程的唯一性
4. 运行管理：支持流式运行和中断恢复功能

技术栈：
- langgraph_sdk: 与 LangGraph 服务器交互的官方 SDK
- requests: 用于 HTTP 请求（获取 token）
- uuid: 生成稳定的 UUID
- dotenv: 加载环境变量

业务背景：
- 为上层应用提供简洁的方法来管理助手、线程和运行
- 支持多用户、多客户的会话隔离
- 实现中断机制，支持人工干预流程
"""

# 导入类型提示模块
from typing import Dict, List, Optional, Any
# 导入 LangGraph SDK 客户端
from langgraph_sdk import get_client
# 导入 LangGraph SDK 数据模型
from langgraph_sdk.schema import Thread, Assistant, Interrupt, Run
# 导入 LangGraph 命令类型
from langgraph.types import Command
# 导入环境变量加载工具
from dotenv import load_dotenv
# 导入 HTTP 请求库
import requests
# 导入 UUID 生成模块
import uuid
# 导入时间模块
import time

# 加载 .env 环境变量文件
load_dotenv()


def generate_stable_uuid(name: str) -> str:
    """
    根据名称生成稳定的 UUID
    
    使用 UUID5 算法（SHA-1 哈希），确保相同的名称总是生成相同的 UUID
    这对于需要持久化和可复用的实体（如助手、线程）非常重要
    
    Args:
        name: 用于生成 UUID 的名称字符串，通常包含用户ID、客户ID等唯一标识
        
    Returns:
        str: 稳定的 UUID 字符串（格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
    """
    # 使用命名空间 UUID（DNS 命名空间）作为基础
    namespace_uuid = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    # 使用 UUID5 算法生成稳定 UUID
    stable_uuid = uuid.uuid5(namespace_uuid, name)
    # 转换为字符串返回
    return str(stable_uuid)

class SagtAgentAPI:
    """
    SAGT 客户端封装类
    
    提供与 LangGraph 服务器交互的高级接口，封装了连接管理、助手管理、
    线程管理和运行管理等核心功能，为上层应用提供简洁统一的 API。
    
    属性：
        _client: LangGraph SDK 客户端实例
        _connected: 连接状态标志
        thread_name_format: 线程名称格式模板
    """
    
    # LangGraph SDK 客户端实例（私有属性）
    _client = None
    # 连接状态标志（私有属性）
    _connected = False

    ################## 连接管理 ##################

    async def connect(self, sagt_server_url: str, sagt_user: str, password: str) -> bool:
        """
        连接到 LangGraph 服务器
        
        连接流程：
        1. 向 /sagt/get_token 端点发送认证请求，获取访问令牌
        2. 使用令牌创建 LangGraph SDK 客户端
        3. 设置连接状态为已连接
        
        Args:
            sagt_server_url: SAGT 服务器地址（如 http://localhost:8000）
            sagt_user: 用户名（员工ID）
            password: 密码
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 步骤1：向服务器获取认证 token
            # 构建请求 URL 和 JSON 体
            response = requests.post(
                f"{sagt_server_url}/sagt/get_token", 
                json={"user_id": sagt_user, "password": password}
            )

            # 检查响应状态码，非 200 表示认证失败
            if response.status_code != 200:
                self._connected = False
                return self._connected
            
            # 从响应中提取 token
            user_token = response.json().get("token")
            
            # 步骤2：创建 LangGraph 客户端连接
            # 构建 Authorization 头部（Bearer token 格式）
            headers = {"Authorization": "Bearer " + user_token}
            # 使用 SDK 创建客户端实例
            self._client = get_client(url=sagt_server_url, headers=headers)
            
            # 步骤3：设置连接状态
            self._connected = True
            return self._connected
            
        except Exception as e:
            # 任何异常都视为连接失败
            self._connected = False
            return self._connected

    async def disconnect(self):
        """
        断开与服务器的连接
        
        清理客户端实例，重置连接状态标志
        """
        # 清除客户端实例
        self._client = None
        # 重置连接状态
        self._connected = False


    async def is_connected(self) -> bool:
        """
        检查客户端是否已连接
        
        Returns:
            bool: True 表示已连接，False 表示未连接
        """
        # 同时检查连接标志和客户端实例
        return self._connected and self._client is not None
    
    ################## 助手管理 ##################
    
    async def create_assistant(self, graph_id: str, external_id: str, user_id: str) -> str:
        """
        创建或获取已存在的助手
        
        使用稳定 UUID 算法确保相同参数总是生成相同的助手 ID，
        避免重复创建。如果助手已存在，则返回已存在的助手 ID。
        
        Args:
            graph_id: 图定义的 ID（如 "sagt"）
            external_id: 客户外部 ID（微信外部联系人 ID）
            user_id: 员工 ID（销售人员 ID）
            
        Returns:
            str: 助手 ID（创建成功）或空字符串（创建失败）
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 构建助手 ID 格式字符串（包含图ID、用户ID、客户ID）
            assistant_id_format = f"{graph_id}_{user_id}_{external_id}"
            # 生成稳定的助手 ID（相同输入总是得到相同的 ID）
            assistant_id = generate_stable_uuid(assistant_id_format)

            # 使用 SDK 创建助手
            assistant = await self._client.assistants.create(
                graph_id=graph_id,                    # 指定使用的图
                config={
                    "configurable": {
                        "external_id": external_id,   # 客户外部 ID
                        "user_id": user_id            # 员工 ID
                    }
                },
                assistant_id=assistant_id,            # 使用预先生成的 ID
                if_exists="do_nothing",               # 如果已存在则不做任何操作
                name=f"SagtAgent_{assistant_id}"      # 助手显示名称
            )

            # 返回助手 ID
            return assistant['assistant_id']
        except Exception as e:
            # 创建失败返回空字符串
            return ""
    
    async def delete_assistant(self, assistant_id: str) -> bool:
        """
        删除指定的助手
        
        Args:
            assistant_id: 要删除的助手 ID
            
        Returns:
            bool: True 表示删除成功，False 表示删除失败
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 删除助手
            await self._client.assistants.delete(assistant_id=assistant_id)
            return True
        except Exception as e:
            # 删除失败返回 False
            return False


    async def list_assistants(self) -> List[Assistant]:
        """
        获取当前用户可用的助手列表
        
        Returns:
            List[Dict]: 助手对象列表，失败时返回空列表
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 搜索助手，最多返回 100 个
            assistants = await self._client.assistants.search(limit=100) # connect()中有了_client的内容
            # 确保返回列表（即使 SDK 返回 None）
            return assistants
        except Exception as e:
            # 获取失败返回空列表
            return []

    ################## 线程管理 ##################

    # 线程名称格式模板（用户ID_客户ID）
    thread_name_format = "{user_id}_{external_id}"

    async def get_thread(self, user_id: str, external_id: str) -> Thread:
        """
        获取指定用户和客户的对话线程
        
        如果线程不存在，返回 None
        
        Args:
            user_id: 员工 ID
            external_id: 客户外部 ID
            
        Returns:
            Thread: 线程对象（存在）或 None（不存在）
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")

        try:
            # 根据格式模板生成线程名称
            thread_name = self.thread_name_format.format(
                user_id=user_id, 
                external_id=external_id
            )
            # 生成稳定的线程 ID
            thread_id = generate_stable_uuid(thread_name)
            # 调用 SDK 获取线程
            thread = await self._client.threads.get(thread_id=thread_id)
            return thread
        except Exception as e:
            # 获取失败返回 None
            return None

    async def get_thread_id(self, user_id: str, external_id: str) -> str:
        """
        根据用户 ID 和客户 ID 计算线程 ID
        
        注意：此方法不检查线程是否实际存在，仅计算 ID
        
        Args:
            user_id: 员工 ID
            external_id: 客户外部 ID
            
        Returns:
            str: 线程 ID（UUID 格式）
        """
        # 根据格式模板生成线程名称
        thread_name = self.thread_name_format.format(
            user_id=user_id, 
            external_id=external_id
        )
        # 生成稳定的线程 ID
        thread_id = generate_stable_uuid(thread_name)
        return thread_id

    async def create_thread(self, user_id: str, external_id: str) -> Optional[str]:
        """
        创建新的对话线程
        
        使用稳定 UUID 确保相同参数总是创建相同的线程，
        如果线程已存在则不做任何操作。
        
        Args:
            user_id: 员工 ID
            external_id: 客户外部 ID
            
        Returns:
            Optional[str]: 线程 ID（创建成功）或 None（创建失败）
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        # 根据格式模板生成线程名称
        thread_name = self.thread_name_format.format(
            user_id=user_id, 
            external_id=external_id
        )
        # 生成稳定的线程 ID
        thread_id = generate_stable_uuid(thread_name)

        try:
            # 调用 SDK 创建线程
            thread = await self._client.threads.create(
                thread_id=thread_id,       # 使用预先生成的 ID
                if_exists="do_nothing"     # 如果已存在则不做任何操作
            )
            # 返回线程 ID
            return thread['thread_id']
        except Exception as e:
            # 创建失败返回 None
            return None

    async def delete_thread(self, thread_id: str) -> bool:
        """
        删除指定的对话线程
        
        Args:
            thread_id: 要删除的线程 ID
            
        Returns:
            bool: True 表示删除成功，False 表示删除失败
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 删除线程
            await self._client.threads.delete(thread_id=thread_id)
            return True
        except Exception as e:
            # 打印错误信息（用于调试）
            print(f"删除线程失败: {e}")
            return False


    async def list_threads(self) -> List[Dict[str, Any]]:
        """
        获取当前用户的所有对话线程列表
        
        Returns:
            List[Dict[str, Any]]: 线程列表，失败时返回空列表
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 搜索线程，最多返回 100 个
            threads = await self._client.threads.search(limit=100)
            return threads
        except Exception as e:
            # 获取失败返回空列表（注释掉了彩色输出，保持简洁）
            # console.print(f"[red]获取线程列表失败: {e}[/red]")
            return []

    async def has_interrupts(self, thread_id: str) -> bool:
        """
        检查指定线程是否存在待处理的中断
        
        中断通常用于人工确认场景（如 HITL 机制）
        
        Args:
            thread_id: 线程 ID
            
        Returns:
            bool: True 表示存在中断，False 表示不存在
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        # 获取线程的中断列表
        interrupts = await self.get_interrupts_from_thread(thread_id)
        
        # 判断是否存在中断（列表长度 > 0）
        return len(interrupts) > 0

    async def get_interrupts_from_thread(self, thread_id: str) -> List[Interrupt]:
        """
        获取指定线程的所有中断信息
        
        Args:
            thread_id: 线程 ID
            
        Returns:
            List[Interrupt]: 中断对象列表，失败时返回空列表
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 获取线程详情
            thread = await self._client.threads.get(thread_id=thread_id)
            # 从线程对象中提取中断列表（默认为空列表）
            interrupts = thread.get("interrupts", [])
            return interrupts
        except Exception as e:
            # 获取失败返回空列表
            return []


    ################## 运行管理 ##################
    async def create_stream_run(self, thread_id: str, assistant_id: str, input: Dict[str, Any]):
        """
        创建新的流式对话运行
        
        流式运行允许实时获取运行进度和结果，适用于需要即时反馈的场景。
        
        Args:
            thread_id: 线程 ID
            assistant_id: 助手 ID
            input: 输入参数（通常包含用户消息等）
            
        Returns:
            Generator: 流式运行结果生成器（成功）或 None（失败）
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 创建流式运行
            run = self._client.runs.stream(
                thread_id=thread_id,      # 指定线程
                assistant_id=assistant_id, # 指定助手
                input=input,              # 输入参数
                stream_subgraphs=True     # 启用子图级别的流式输出
            )
            return run
        except Exception as e:
            # 创建失败返回 None
            return None

    async def resume_interrupt_run(self, thread_id: str, assistant_id: str, command: Command):
        """
        恢复被中断的运行
        
        当运行因 HITL（人工介入）中断时，使用此方法提交人工决策并恢复运行。
        
        Args:
            thread_id: 线程 ID
            assistant_id: 助手 ID
            command: 人工决策命令（包含中断处理结果）
            
        Returns:
            Generator: 流式运行结果生成器（成功）或 None（失败）
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        try:
            # 调用 SDK 恢复中断的运行
            run = self._client.runs.stream(
                thread_id=thread_id,      # 指定线程
                assistant_id=assistant_id, # 指定助手
                command=command,          # 人工决策命令
                stream_subgraphs=True     # 启用子图级别的流式输出
            )
            return run
        except Exception as e:
            # 恢复失败返回 None
            return None

    async def list_runs(self, thread_id: str) -> List[Run]:
        """
        获取指定线程的所有运行记录
        
        Args:
            thread_id: 线程 ID
            
        Returns:
            List[Run]: 运行记录列表
        """
        # 前置检查：确保客户端已连接
        if not await self.is_connected():
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        # 调用 SDK 获取运行列表，最多返回 100 个
        runs = await self._client.runs.list(thread_id=thread_id, limit=100)
        return runs

