#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAGT Agent Web API 服务

本模块是基于 FastAPI 构建的 Web API 服务，主要功能包括：
1. 用户登录认证（JWT）
2. 消息发送与流式响应
3. HITL（人工介入）中断管理
4. 静态文件服务

技术栈：
- FastAPI: 高性能异步 Web 框架
- JWT: 无状态身份认证
- SagtAgentAPI: 与 LangGraph 服务器交互的客户端

业务背景：
- 为 SAGT Agent 提供 Web 访问接口
- 支持企业微信侧边栏集成
- 实现人工确认机制（HITL）

安全特性：
- JWT 令牌认证
- 会话管理（客户端连接池）
- CORS 跨域配置
"""

# 导入 FastAPI 核心模块
from fastapi import FastAPI, HTTPException, Depends, status
# 导入 HTTP Bearer 认证
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# 导入 CORS 中间件
from fastapi.middleware.cors import CORSMiddleware
# 导入流式响应
from fastapi.responses import StreamingResponse
# 导入静态文件服务
from fastapi.staticfiles import StaticFiles
# 导入 Pydantic 数据模型
from pydantic import BaseModel, Field
# 导入类型提示
from typing import Dict, List, Optional, Any
# 导入 JSON 处理
import json
# 导入操作系统接口
import os
# 导入日期时间处理
from datetime import datetime, timedelta
# 导入 JWT 库
from jose import JWTError, jwt
# 导入环境变量加载工具
from dotenv import load_dotenv
# 导入 SAGT Agent API 客户端
from sagt_agent_api.sagt_agent_api import SagtAgentAPI

# 加载 .env 环境变量文件
load_dotenv()


# 创建 FastAPI 应用实例
app = FastAPI(
    title="SAGT Agent Web API",           # API 标题
    description="SAGT Agent Web API 服务",   # API 描述
    version="1.0.0"                        # API 版本号
)

# 添加 CORS（跨域资源共享）中间件
# 允许前端页面从不同域名访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 允许所有来源（生产环境应限制具体域名）
    allow_credentials=True,        # 允许携带凭证
    allow_methods=["*"],           # 允许所有 HTTP 方法
    allow_headers=["*"],           # 允许所有请求头
)

# 挂载静态文件目录
# 将 ./sagt_web 目录映射到 /sagt_web 路径，提供 HTML、CSS、JS 等静态资源
app.mount("/sagt_web", StaticFiles(directory="./sagt_web"), name="sagt_web")

# 初始化 HTTP Bearer 认证实例
# 用于验证请求中的 Authorization 头部（Bearer token）
security = HTTPBearer()

# 全局客户端连接池
# 使用 JWT token 作为键，存储对应的 SagtAgentAPI 客户端实例
# 实现会话级别的连接管理
clients: Dict[str, SagtAgentAPI] = {}

# ========== SAGT 服务配置 ==========
# SAGT Agent 服务器地址
SAGT_SERVER_URL = os.getenv("SAGT_SERVER_URL")
# SAGT 图定义 ID（如 "sagt"）
SAGT_GRAPH_ID = os.getenv("SAGT_GRAPH_ID")
# SAGT 服务认证用户名
SAGT_USER_ID = os.getenv("SAGT_USER_ID")
# SAGT 服务认证密码
SAGT_PASSWORD = os.getenv("SAGT_PASSWORD")

# ========== Web 服务配置 ==========
# Web 服务登录用户名（独立于 SAGT 账号）
WEB_USER_ID = os.getenv("WEB_USER_ID")
# Web 服务登录密码
WEB_PASSWORD = os.getenv("WEB_PASSWORD")

# ========== JWT 认证配置 ==========
# JWT 签名密钥（生产环境必须修改）
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
# JWT 加密算法
JWT_ALGORITHM = "HS256"
# JWT 令牌过期时间（分钟）
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ========== 业务 DEMO 配置 ==========
# 外部客户 ID（用于 DEMO 演示，模拟特定客户）
EXTERNAL_ID = os.getenv("EXTERNAL_ID")

# ========== 请求数据模型 ==========
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class SendMessageRequest(BaseModel):
    """发送消息请求模型"""
    message: Optional[str] = Field(None, description="消息内容")
    menu_id: Optional[str] = Field(None, description="菜单ID，如果是点击菜单触发")

class InterruptConfirmRequest(BaseModel):
    """中断确认请求模型"""
    confirmed: str = Field(..., description="确认结果: ok(确认), discard(丢弃), recreate(重新创建)")

# ========== 响应数据模型 ==========
class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = Field(..., description="登录是否成功")
    token: str = Field(default="", description="JWT访问令牌")
    message: str = Field(default="", description="响应消息")

class TaskResult(BaseModel):
    """任务结果模型"""
    task_result: str = Field(default="", description="任务结果内容")
    task_result_explain: str = Field(default="", description="任务结果解释说明")
    task_result_code: int = Field(default=1, description="任务结果代码，0: 结果有效，1: 结果无效")

class NodeResult(BaseModel):
    """节点执行结果模型"""
    execute_node_name: str = Field(default="", description="执行的节点名称")
    execute_result_code: int = Field(default=1, description="节点执行结果代码，0: 成功，1: 失败")
    execute_result_msg: str = Field(default="", description="节点执行结果消息")
    execute_exceptions: List[str] = Field(default=[], description="节点执行异常信息列表")

class InterruptInfo(BaseModel):
    """中断信息模型"""
    description: str = Field(..., description="中断描述信息")
    data: Dict[str, Any] = Field(..., description="中断相关数据")

# ========== JWT 工具函数 ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    创建 JWT 访问令牌
    
    Args:
        data: 要嵌入令牌的用户数据（通常包含 "sub" 字段表示用户名）
        expires_delta: 过期时间增量（可选，默认使用配置的过期时间）
        
    Returns:
        str: 编码后的 JWT 令牌字符串
    """
    # 复制数据以避免修改原始字典
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 使用默认过期时间（配置中定义的分钟数）
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 添加过期时间到载荷
    to_encode.update({"exp": expire})
    
    # 使用指定算法和密钥编码 JWT
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    验证 JWT 令牌的有效性
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        dict: 解码后的令牌载荷
        
    Raises:
        HTTPException: 令牌无效时抛出 401 错误
    """
    try:
        # 解码并验证令牌
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # 检查用户名是否存在
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError:
        # JWT 解码失败（签名无效、过期等）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ========== 依赖注入函数 ==========
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    获取当前登录用户（依赖注入函数）
    
    用于保护需要认证的 API 端点，自动验证 JWT 令牌并获取用户信息。
    
    Args:
        credentials: HTTPBearer 认证凭证（包含 JWT 令牌）
        
    Returns:
        Tuple[str, str]: (token, username) 令牌和用户名
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    # 从凭证中提取 JWT 令牌
    token = credentials.credentials
    
    # 验证令牌并获取载荷
    payload = verify_token(token)
    username = payload.get("sub")
    
    # 检查令牌对应的客户端连接是否存在（会话有效性检查）
    if token not in clients:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期，请重新登录"
        )
    
    # 返回令牌和用户名，供后续处理使用
    return token, username

async def get_client(token: str) -> SagtAgentAPI:
    """
    获取 SagtAgentAPI 客户端实例（依赖注入函数）
    
    根据 JWT 令牌从连接池中获取对应的客户端实例。
    
    Args:
        token: JWT 令牌
        
    Returns:
        SagtAgentAPI: 客户端实例
        
    Raises:
        HTTPException: 客户端未连接时抛出 401 错误
    """
    # 检查客户端连接是否存在
    if token not in clients:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="客户端未连接"
        )
    
    # 返回客户端实例
    return clients[token]

# ========== API 路由 ==========
@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录接口
    
    登录流程：
    1. 验证 Web 服务账号（独立于 SAGT 账号）
    2. 创建 SagtAgentAPI 客户端实例
    3. 使用 SAGT 账号连接到后端服务器
    4. 生成 JWT 令牌并保存客户端连接
    5. 返回登录结果
    
    Args:
        request: LoginRequest 登录请求体
        
    Returns:
        LoginResponse: 登录响应（包含令牌和状态）
    """
    try:
        # 步骤1：验证 Web 服务账号（独立于 SAGT 账号）
        if request.username != WEB_USER_ID or request.password != WEB_PASSWORD:
            return LoginResponse(
                success=False,
                message="用户名或密码错误"
            )
        
        # 步骤2：Web 账号验证成功后，创建 SAGT 客户端实例
        client = SagtAgentAPI()
        
        # 步骤3：使用配置的 SAGT 账号连接到 SAGT 服务器
        success = await client.connect(
            sagt_server_url=SAGT_SERVER_URL,
            sagt_user=SAGT_USER_ID,
            password=SAGT_PASSWORD
        )
        
        if success:
            # 步骤4：生成 JWT 令牌
            access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": request.username},
                expires_delta=access_token_expires
            )
            
            # 保存客户端连接到连接池
            clients[access_token] = client
            
            # 步骤5：返回登录成功响应
            return LoginResponse(
                success=True,
                token=access_token,
                message="登录成功"
            )
        else:
            return LoginResponse(
                success=False,
                message="后端服务连接失败，请稍后重试"
            )
            
    except Exception as e:
        # 捕获所有异常，返回友好错误信息
        return LoginResponse(
            success=False,
            message=f"登录失败: {str(e)}"
        )

@app.post("/api/logout")
async def logout(user_info=Depends(get_current_user)):
    """
    用户登出接口
    
    登出流程：
    1. 获取当前用户信息
    2. 断开与 SAGT 服务器的连接
    3. 从连接池中删除客户端实例
    
    Args:
        user_info: 依赖注入获取的用户信息（token, username）
        
    Returns:
        Dict: 登出结果
    """
    try:
        # 获取令牌和用户名
        token, username = user_info
        
        # 如果存在客户端连接，断开并删除
        if token in clients:
            await clients[token].disconnect()
            del clients[token]
        
        return {"success": True, "message": "登出成功"}
        
    except Exception as e:
        # 捕获异常，返回错误信息
        return {"success": False, "message": f"登出失败: {str(e)}"}

@app.post("/api/send_message")
async def send_message(request: SendMessageRequest, user_info=Depends(get_current_user)):
    """
    发送消息给 SAGT Agent（流式响应）
    
    消息发送流程：
    1. 获取用户认证信息和客户端实例
    2. 创建/获取助手和线程
    3. 准备输入数据（支持菜单点击或文本消息）
    4. 创建流式运行并返回 Server-Sent Events 响应
    
    Args:
        request: SendMessageRequest 消息请求体
        user_info: 依赖注入获取的用户信息
        
    Returns:
        StreamingResponse: 流式响应（Server-Sent Events 格式）
    """
    try:
        # 步骤1：获取用户认证信息和客户端实例
        token, username = user_info
        client = await get_client(token)
        
        # 步骤2：创建/获取助手和线程
        # 使用 Web 用户名作为用户标识
        web_user_id = username
        
        # 创建助手（如果已存在则返回已存在的ID）
        assistant_id = await client.create_assistant(
            graph_id=SAGT_GRAPH_ID,
            external_id=EXTERNAL_ID,
            user_id=web_user_id
        )
        
        # 创建线程（如果已存在则返回已存在的ID）
        thread_id = await client.create_thread(
            user_id=web_user_id,
            external_id=EXTERNAL_ID
        )
        
        # 步骤3：准备输入数据
        # task_input 承担两种职责：指令名称、对话内容
        # Agent 会自动区分是否为指令，非指令则进入咨询流程
        if request.menu_id:
            # 菜单点击场景：使用菜单ID作为输入
            input_data = {"task_input": request.menu_id}
        elif request.message:
            # 文本输入场景：直接使用消息内容
            input_data = {"task_input": request.message}
        else:
            # 缺少必要参数
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供消息内容或菜单ID"
            )
        
        # 步骤4：创建流式运行
        stream = await client.create_stream_run(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input=input_data
        )
        
        # 定义流式生成器
        async def generate_stream():
            """
            生成 Server-Sent Events 流式响应
            
            将 Agent 的响应逐块发送给前端，实现实时消息推送。
            """
            try:
                # 异步遍历流式响应
                async for chunk in stream:
                    # 构建事件数据（兼容不同格式的 chunk）
                    chunk_data = {
                        "event": getattr(chunk, 'event', 'unknown'),
                        "data": getattr(chunk, 'data', {})
                    }
                    # 以 SSE 格式发送（data: <json>\n\n）
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    
            except Exception as e:
                # 处理流式传输中的异常
                error_data = {
                    "event": "error",
                    "data": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        # 返回流式响应
        return StreamingResponse(   # 第8行导入的StreamingResponse类，fastapi
            generate_stream(),
            media_type="text/plain",          # SSE 使用 text/plain
            headers={"Cache-Control": "no-cache"}  # 禁用缓存
        )
        
    except Exception as e:
        # 捕获所有异常并返回 500 错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )

@app.get("/api/get_interrupt")
async def get_interrupt(user_info=Depends(get_current_user)):
    """
    获取线程中断信息（HITL 人工确认机制）
    
    用于检查当前对话线程是否存在需要人工确认的中断。
    HITL（Human-In-The-Loop）机制允许人工干预 Agent 的决策流程。
    
    Args:
        user_info: 依赖注入获取的用户信息
        
    Returns:
        Dict: 包含 has_interrupt 和 interrupt_info 字段
    """
    try:
        # 获取用户信息和客户端实例
        token, username = user_info
        client = await get_client(token)
        
        # 获取线程 ID
        web_user_id = username
        thread_id = await client.get_thread_id(
            user_id=web_user_id,
            external_id=EXTERNAL_ID
        )
        
        # 检查线程 ID 是否有效
        if not thread_id:
            return {"has_interrupt": False, "interrupt_info": None}
        
        # 检查线程是否存在中断
        has_interrupt = await client.has_interrupts(thread_id)
        
        if has_interrupt:
            # 获取中断详情
            interrupts = await client.get_interrupts_from_thread(thread_id)
            return {
                "has_interrupt": True,
                "interrupt_info": interrupts
            }
        else:
            return {"has_interrupt": False, "interrupt_info": None}
            
    except Exception as e:
        # 捕获异常并返回 500 错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取中断信息失败: {str(e)}"
        )

@app.post("/api/confirm_interrupt")
async def confirm_interrupt(request: InterruptConfirmRequest, user_info=Depends(get_current_user)):
    """
    确认中断并恢复运行（流式响应）
    
    当 Agent 遇到需要人工确认的决策点时会暂停执行（中断）。
    用户确认后，通过此接口恢复运行并继续执行。
    
    确认选项：
    - ok: 确认并继续
    - discard: 丢弃当前结果
    - recreate: 重新创建
    
    Args:
        request: InterruptConfirmRequest 确认请求体
        user_info: 依赖注入获取的用户信息
        
    Returns:
        StreamingResponse: 流式响应（继续执行的结果）
    """
    try:
        # 获取用户信息和客户端实例
        token, username = user_info
        client = await get_client(token)
        
        # 获取助手和线程 ID
        web_user_id = username
        assistant_id = await client.create_assistant(
            graph_id=SAGT_GRAPH_ID,
            external_id=EXTERNAL_ID,
            user_id=web_user_id
        )
        
        thread_id = await client.get_thread_id(
            user_id=web_user_id,
            external_id=EXTERNAL_ID
        )
        
        # 准备确认命令（符合 LangGraph 中断恢复格式）
        confirmed = {"confirmed": request.confirmed}
        command = {"resume": confirmed}
        
        # 恢复中断的运行
        stream = await client.resume_interrupt_run(
            thread_id=thread_id,
            assistant_id=assistant_id,
            command=command
        )
        
        # 定义流式生成器
        async def generate_stream():
            """生成继续执行的流式响应"""
            try:
                async for chunk in stream:
                    chunk_data = {
                        "event": getattr(chunk, 'event', 'unknown'),
                        "data": getattr(chunk, 'data', {})
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            except Exception as e:
                error_data = {
                    "event": "error",
                    "data": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        # 返回流式响应
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        # 捕获异常并返回 500 错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认中断失败: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """
    健康检查接口
    
    用于监控服务状态，返回服务健康状态。
    
    Returns:
        Dict: 包含 status 和 message 字段
    """
    return {"status": "healthy", "message": "SAGT Agent Web API 运行正常"}

# ========== 应用入口 ==========
if __name__ == "__main__":
    """
    应用启动入口
    
    使用 uvicorn 作为 ASGI 服务器运行 FastAPI 应用。
    监听所有网络接口（0.0.0.0），端口 8000。
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
