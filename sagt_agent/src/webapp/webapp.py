"""Web应用模块

本模块基于FastAPI构建智能体的Web服务，提供以下核心功能：
1. 健康检查接口
2. 用户认证令牌获取接口
3. 自定义请求头中间件
4. 应用生命周期管理

技术栈：
- FastAPI: 高性能Python Web框架
- Starlette: ASGI工具库（FastAPI的底层依赖）
- 环境变量配置: dotenv

业务背景：
- 提供HTTP接口供前端或外部系统调用智能体服务
- 实现简单的认证机制（基于令牌）
- 支持健康检查用于监控和运维

依赖环境变量：
- DEMO_USER_ID: 演示用户ID
- DEMO_USER_PASSWORD: 演示用户密码
- DEMO_USER_TOKEN: 演示用户令牌
- DEMO_USER_EXTERNAL_ID: 演示用户外部联系人ID
"""

# 导入异步上下文管理器
from contextlib import asynccontextmanager
# 导入FastAPI核心组件
from fastapi import FastAPI, Request, Response
# 导入Starlette中间件基类
from starlette.middleware.base import BaseHTTPMiddleware
# 导入日志工具
from utils.agent_logger import get_logger
# 导入系统模块
import os
# 导入环境变量加载工具
from dotenv import load_dotenv

# 加载环境变量（从.env文件读取配置）
load_dotenv()

# 初始化日志记录器
logger = get_logger("webapp")


# ========== 生命周期管理器 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI应用生命周期管理器
    
    用于管理应用启动和关闭时的资源初始化和清理工作。
    
    Args:
        app: FastAPI应用实例
        
    Yields:
        控制流返回给应用
    """
    # 应用启动时执行
    logger.info("Starting application...")
    
    # 让出控制，允许应用运行
    yield
    
    # 应用关闭时执行
    logger.info("Shutting down application...")


# 创建FastAPI应用实例
app = FastAPI(lifespan=lifespan)


# ========== 中间件 ==========

class HeaderMiddleware(BaseHTTPMiddleware):
    """
    自定义请求头中间件
    
    在所有响应中添加自定义HTTP头，用于标识请求来源。
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并添加自定义响应头
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: 添加了自定义头的响应对象
        """
        # 记录请求URL日志
        logger.info("custom header for request url: %s", request.url)
        
        # 调用下一个处理函数
        response = await call_next(request)
        
        # 在响应中添加自定义头
        response.headers["X-custom-header"] = "by Sagt Agent" # 每一个响应的头上盖个章，写上 "X-custom-header": "by Sagt Agent"
        
        return response


# 注册中间件到应用
app.add_middleware(HeaderMiddleware)


# ========== API路由 ==========

@app.get("/sagt/health")
async def health():
    """
    健康检查接口
    
    用于监控系统状态，返回应用运行状态。
    
    Returns:
        dict: 包含状态信息的字典
    """
    logger.info("sagt health check")
    return {"status": "ok"}


@app.post("/sagt/get_token")
async def get_token(request: Request):
    """
    获取认证令牌接口
    
    通过用户ID和密码验证后返回访问令牌。
    这是一个简化的认证机制，仅用于演示目的。
    
    Args:
        request: 请求对象，包含JSON格式的body
        
    Returns:
        dict: 成功时返回令牌信息，失败时返回403状态码
    """
    logger.info("sagt get_token")
    
    # 解析请求体为JSON
    body = await request.json()
    
    # 提取用户凭证
    password = body.get("password")
    user_id = body.get("user_id")

    # 参数校验：用户ID和密码不能为空
    if not user_id or not password:
        return Response(status_code=403)

    # 从环境变量获取演示用户配置
    demo_user_id = os.getenv("DEMO_USER_ID")
    demo_password = os.getenv("DEMO_USER_PASSWORD")

    # 验证用户凭证
    if user_id == demo_user_id and password == demo_password:
        # 验证成功，返回令牌信息
        logger.info("sagt get_token success: %s", user_id)
        return {
            "status": "ok",
            "token": os.getenv("DEMO_USER_TOKEN"),      # 访问令牌
            "user_id": os.getenv("DEMO_USER_ID"),       # 用户ID
            "external_id": os.getenv("DEMO_USER_EXTERNAL_ID")  # 外部联系人ID
        }
    else:
        # 验证失败
        logger.info("sagt get_token failed: %s", user_id)
        return Response(status_code=403)