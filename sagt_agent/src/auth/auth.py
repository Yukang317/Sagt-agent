"""认证模块

本模块提供智能体的认证和授权功能，基于LangGraph SDK实现。

核心功能：
1. 令牌验证：验证用户访问令牌的有效性
2. 请求认证：拦截并验证所有需要认证的请求
3. 认证上下文处理：处理认证相关的上下文信息

技术实现：
- 使用LangGraph SDK的Auth组件进行认证管理
- 基于预定义的令牌列表进行简单认证
- 支持Bearer Token认证方式

业务背景：
- 保护智能体的API接口，防止未授权访问
- 验证用户身份，确保数据安全
- 与webapp模块配合使用，实现完整的认证流程

依赖环境变量：
- DEMO_USER_TOKEN: 演示用户令牌
- DEMO_USER_ID: 演示用户ID
- DEMO_USER_EXTERNAL_ID: 演示用户外部联系人ID
"""

# 导入LangGraph SDK的认证组件
from langgraph_sdk import Auth
# 导入环境变量加载工具
from dotenv import load_dotenv
# 导入日志工具
from utils.agent_logger import get_logger
# 导入系统模块
import os
# 导入FastAPI请求对象
from fastapi import Request

# 加载环境变量（从.env文件读取配置）
load_dotenv()

# 初始化日志记录器
logger = get_logger("auth")


# ========== 认证配置 ==========

# 有效令牌字典
# 键：令牌值
# 值：用户信息（用户ID和外部联系人ID）
VALID_TOKENS = {
    os.getenv("DEMO_USER_TOKEN"): {"user_id": os.getenv("DEMO_USER_ID"), "external_id": os.getenv("DEMO_USER_EXTERNAL_ID")},
}


# ========== LangGraph认证组件 ==========

# 创建LangGraph认证实例
auth = Auth()


# ========== 认证事件处理 ==========

@auth.on
async def auth_on(ctx: Auth.types.AuthContext, value: dict):
    """
    认证事件处理器
    
    当认证上下文发生变化时触发，用于处理认证相关的事件。
    
    Args:
        ctx: 认证上下文对象，包含认证相关信息
        value: 认证值，包含用户标识等信息
        
    Returns:
        bool: 认证是否成功
    """
    # 记录认证上下文日志
    logger.info("auth_on ctx: %s", ctx)
    logger.info("auth_on value: %s", value)
    
    # 返回True表示认证成功
    return True


# ========== 令牌验证函数 ==========

async def verify_token(token: str) -> bool:
    """
    验证令牌是否有效
    
    检查给定的令牌是否存在于有效令牌列表中。
    
    Args:
        token: 待验证的令牌字符串
        
    Returns:
        bool: 令牌是否有效
    """
    return token in VALID_TOKENS


# ========== 请求认证处理器 ==========

@auth.authenticate
async def authenticate(request: Request, authorization: str|None) -> str:
    """
    请求认证处理器
    
    拦截所有请求，验证Authorization头中的Bearer令牌。
    
    Args:
        request: FastAPI请求对象
        authorization: Authorization请求头的值，即token
        
    Returns:
        str: 用户标识（用于后续业务逻辑）
        
    Raises:
        Auth.exceptions.HTTPException: 认证失败时抛出401异常
    """
    # 记录请求信息日志
    logger.info("authenticate request: %s", request)
    logger.info("authenticate authorization: %s", authorization)

    # 提取请求路径
    path = request.url.path
    logger.info("authenticate path: %s", path)

    # 提取请求方法
    method = request.method
    logger.info("authenticate method: %s", method)

    # 提取路径参数
    path_params = request.path_params
    logger.info("authenticate path_params: %s", path_params)

    # 提取查询参数
    query_params = request.query_params
    logger.info("authenticate query_params: %s", query_params)

    # 提取请求头
    headers = request.headers
    logger.info("authenticate headers: %s", headers)

    # 检查Authorization头是否存在
    if not authorization:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token")

    # 解析Authorization头（格式：Bearer <token>）
    scheme, token = authorization.split()
    
    # 验证认证方案是否为Bearer
    if scheme != "Bearer":
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token")
    
    # 验证令牌有效性
    verified = await verify_token(token)
    
    # 如果令牌无效，抛出异常
    if not verified:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token")

    # 返回用户标识（硬编码为演示用户，实际应从令牌信息中提取）
    return "ChengJianZhang"