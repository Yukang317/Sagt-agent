"""SAGT Agent 数据加载节点定义文件

本文件定义了各类数据加载节点，负责从外部数据源获取业务数据，
为后续的业务处理提供数据基础。所有节点都包含完善的异常处理机制。
"""

# 导入 LangChain 可运行配置
from langchain_core.runnables import RunnableConfig
# 导入状态定义
from graphs.sagt_graph.sagt_state import SagtState, SagtStateField
# 导入数据存储工具函数
from tools.store_tool import (
    get_tag_setting,       # 获取标签设置
    get_customer_info,     # 获取客户基本信息
    get_chat_history,      # 获取聊天历史
    get_kf_history,        # 获取微信客服聊天历史
    get_order_history,     # 获取订单历史
    get_customer_profile,  # 获取客户画像
    get_customer_tags,     # 获取客户标签
    get_employee_info      # 获取员工信息
)
# 导入配置字段定义
from graphs.sagt_graph.sagt_state import ConfigurableField
# 导入业务模型类
from models.sagt_models import (
    TagSetting,         # 标签设置模型
    CustomerInfo,       # 客户信息模型
    CustomerProfile,    # 客户画像模型
    OrderHistory,       # 订单历史模型
    KFChatHistory,      # 微信客服聊天历史模型
    ChatHistory,        # 聊天历史模型
    CustomerTags,       # 客户标签模型
    NodeResult,         # 节点执行结果模型
    EmployeeInfo        # 员工信息模型
)
# 导入日志工具
from utils.agent_logger import get_logger
# 导入枚举模块
from enum import Enum

# 获取数据加载节点模块的日志实例
logger = get_logger("sagt_node_load_data")

class NodeName(str, Enum):
    """
    数据加载节点名称枚举定义
    
    定义了所有数据加载节点的唯一标识符，用于状态图中的节点注册和引用。
    """
    LOAD_WELCOME_MESSAGE    = "load_welcome_message_node"   # 加载欢迎消息节点
    LOAD_EMPLOYEE_INFO      = "load_employee_info_node"     # 加载员工信息节点
    LOAD_TAG_SETTING        = "load_tag_setting_node"       # 加载标签设置节点
    LOAD_CUSTOMER_INFO      = "load_customer_info_node"     # 加载客户信息节点
    LOAD_CHAT_HISTORY       = "load_chat_history_node"      # 加载聊天历史节点
    LOAD_KF_CHAT_HISTORY    = "load_kf_chat_history_node"   # 加载微信客服聊天历史节点
    LOAD_ORDER_HISTORY      = "load_order_history_node"     # 加载订单历史节点

def load_welcome_message_node(state: SagtState, config: RunnableConfig):
    """
    加载欢迎消息节点
    
    在数据加载流程开始时向用户发送加载提示消息，告知用户系统正在准备数据。
    
    Args:
        state: 当前状态对象
        config: 运行配置
        
    Returns:
        包含加载提示消息的状态更新字典
    """
    logger.info("=== 加载欢迎信息 ===")
    
    return {
        SagtStateField.NODE_RESULT: 
        [NodeResult(
            execute_node_name=NodeName.LOAD_WELCOME_MESSAGE.value,  # 节点名称
            execute_result_code=0,                                   # 执行结果码（0表示成功）
            execute_result_msg="正在为您加载数据，请稍等。",            # 加载提示消息
            execute_exceptions=[]                                    # 异常列表（空表示无异常）
        )]
    }

def load_employee_info_node(state: SagtState, config: RunnableConfig):
    """
    加载员工信息节点
    
    从数据存储中获取当前操作用户（销售人员/客服人员）的基本信息。
    使用配置中的 user_id 查询员工信息。
    
    Args:
        state: 当前状态对象
        config: 运行配置，包含 user_id 配置
        
    Returns:
        包含员工信息的状态更新字典，成功时包含员工数据，失败时包含错误信息
    """
    logger.info("=== 加载员工信息 ===")

    # 从配置中获取当前用户ID
    user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    logger.info(f"user_id: {user_id}")

    try:
        # 调用工具函数获取员工信息
        employee_info: EmployeeInfo = get_employee_info(user_id=user_id)
        logger.info(f"员工信息: {employee_info}")
        
        # 返回成功结果
        return {
            SagtStateField.EMPLOYEE_INFO: employee_info,  # 存储员工信息到状态
            SagtStateField.NODE_RESULT: 
                [NodeResult(
                    execute_node_name=NodeName.LOAD_EMPLOYEE_INFO.value,
                    execute_result_code=0,
                    execute_result_msg="完成员工信息加载",
                    execute_exceptions=[]
                )]
        }
    except Exception as e:
        # 捕获异常，记录错误日志并返回默认值
        logger.error(f"加载员工信息失败: {e}")
        return {
            SagtStateField.EMPLOYEE_INFO: EmployeeInfo(),  # 返回空的员工信息对象
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_EMPLOYEE_INFO.value,
                execute_result_code=1,  # 非0表示失败
                execute_result_msg="加载员工信息失败",
                execute_exceptions=[str(e)]  # 记录异常信息
            )]
        }

def load_tag_setting_node(state: SagtState, config: RunnableConfig):
    """
    加载标签设置节点
    
    从数据存储中获取系统的标签设置配置，用于后续的客户标签生成和管理。
    
    Args:
        state: 当前状态对象
        config: 运行配置
        
    Returns:
        包含标签设置的状态更新字典，成功时包含标签配置数据，失败时包含错误信息
    """
    logger.info("=== 加载标签设置 ===")
    
    try:
        # 调用工具函数获取标签设置
        tag_setting: TagSetting = get_tag_setting()
        logger.info(f"标签设置: {tag_setting}")
        
        # 返回成功结果
        return {
            SagtStateField.TAG_SETTING: tag_setting,  # 存储标签设置到状态
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_TAG_SETTING.value,
                execute_result_code=0,
                execute_result_msg="完成标签设置加载",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 捕获异常，记录错误日志并返回默认值
        logger.error(f"加载标签设置失败: {e}")
        return {
            SagtStateField.TAG_SETTING: TagSetting(),  # 返回空的标签设置对象
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_TAG_SETTING.value,
                execute_result_code=1,
                execute_result_msg="加载标签设置失败",
                execute_exceptions=[str(e)]
            )]
        }


def load_customer_info_node(state: SagtState, config: RunnableConfig):
    """
    加载客户信息节点
    
    从数据存储中获取目标客户的基本信息、画像和标签。
    使用配置中的 user_id（跟进人ID）和 external_id（客户外部ID）进行查询。
    
    Args:
        state: 当前状态对象
        config: 运行配置，包含 user_id 和 external_id
        
    Returns:
        包含客户信息的状态更新字典，成功时包含客户数据，失败时包含错误信息
    """
    logger.info("=== 加载客户信息 ===")
    
    # 从配置中获取跟进人ID和客户外部ID
    follow_user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    external_id = config[ConfigurableField.configurable][ConfigurableField.external_id]
    
    logger.info(f"follow_user_id: {follow_user_id}")
    logger.info(f"external_id: {external_id}")
    
    try:
        # 调用工具函数获取客户相关信息
        customer_info: CustomerInfo = get_customer_info(
            external_id=external_id, 
            follow_user_id=follow_user_id
        )
        customer_profile: CustomerProfile = get_customer_profile(
            external_id=external_id, 
            follow_user_id=follow_user_id
        )
        customer_tags: CustomerTags = get_customer_tags(
            external_id=external_id, 
            follow_user_id=follow_user_id
        )

        logger.debug(f"客户信息: {customer_info}")
        logger.debug(f"客户Profile: {customer_profile}")
        logger.debug(f"客户标签: {customer_tags}")
        
        # 返回成功结果
        return {
            SagtStateField.CUSTOMER_INFO: customer_info,        # 存储客户基本信息
            SagtStateField.CUSTOMER_PROFILE: customer_profile,  # 存储客户画像
            SagtStateField.CUSTOMER_TAGS: customer_tags,        # 存储客户标签
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_CUSTOMER_INFO.value,
                execute_result_code=0,
                execute_result_msg="完成客户信息加载",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 捕获异常，记录错误日志并返回默认值
        logger.error(f"加载客户信息失败: {e}")
        return {
            SagtStateField.CUSTOMER_INFO: CustomerInfo(),       # 返回空的客户信息对象
            SagtStateField.CUSTOMER_PROFILE: CustomerProfile(), # 返回空的客户画像对象
            SagtStateField.CUSTOMER_TAGS: [],                   # 返回空的客户标签列表
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_CUSTOMER_INFO.value,
                execute_result_code=1,
                execute_result_msg="加载客户信息失败",
                execute_exceptions=[str(e)]
            )]
        }


def load_chat_history_node(state: SagtState, config: RunnableConfig):
    """
    加载聊天历史节点
    
    从数据存储中获取销售人员与客户之间的聊天历史记录。
    使用配置中的 user_id 和 external_id 进行查询。
    
    Args:
        state: 当前状态对象
        config: 运行配置，包含 user_id 和 external_id
        
    Returns:
        包含聊天历史的状态更新字典，成功时包含聊天记录，失败时包含错误信息
    """
    logger.info("=== 加载聊天消息 ===")

    # 从配置中获取跟进人ID和客户外部ID
    follow_user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    external_id = config[ConfigurableField.configurable][ConfigurableField.external_id]
    
    logger.info(f"follow_user_id: {follow_user_id}")
    logger.info(f"external_id: {external_id}")
    
    # 直接调用工具函数，传递配置
    try:
        # 调用工具函数获取聊天历史
        chat_history = get_chat_history(
            external_id=external_id,
            follow_user_id=follow_user_id
        )
        logger.debug(f"聊天消息: {chat_history}")
        
        # 返回成功结果
        return {
            SagtStateField.CHAT_HISTORY: chat_history,  # 存储聊天历史到状态
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_CHAT_HISTORY.value,
                execute_result_code=0,
                execute_result_msg="完成聊天消息加载",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 捕获异常，记录错误日志并返回默认值
        logger.error(f"加载聊天消息失败: {e}")
        return {
            SagtStateField.CHAT_HISTORY: ChatHistory(),  # 返回空的聊天历史对象
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_CHAT_HISTORY.value,
                execute_result_code=1,
                execute_result_msg="加载聊天消息失败",
                execute_exceptions=[str(e)]
            )]
        }


def load_kf_chat_history_node(state: SagtState, config: RunnableConfig):
    """
    加载微信客服聊天历史节点
    
    从数据存储中获取客户与微信客服之间的聊天历史记录。
    使用配置中的 external_id 进行查询。
    
    Args:
        state: 当前状态对象
        config: 运行配置，包含 external_id
        
    Returns:
        包含微信客服聊天历史的状态更新字典，成功时包含聊天记录，失败时包含错误信息
    """
    logger.info("=== 加载微信客服信息 ===")

    # 从配置中获取客户外部ID
    external_id = config[ConfigurableField.configurable][ConfigurableField.external_id]
    logger.info(f"external_id: {external_id}")
    

    # 直接调用工具函数，传递配置
    try:
        # 调用工具函数获取微信客服聊天历史
        kf_chat_history = get_kf_history(external_id=external_id)
        logger.debug(f"微信客服信息: {kf_chat_history}")
        
        # 返回成功结果
        return {
            SagtStateField.KF_CHAT_HISTORY: kf_chat_history,  # 存储微信客服聊天历史到状态
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_KF_CHAT_HISTORY.value,
                execute_result_code=0,
                execute_result_msg="完成微信客服信息加载",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 捕获异常，记录错误日志并返回默认值
        logger.error(f"加载微信客服信息失败: {e}")
        return {
            SagtStateField.KF_CHAT_HISTORY: KFChatHistory(),  # 返回空的微信客服聊天历史对象
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_KF_CHAT_HISTORY.value,
                execute_result_code=1,
                execute_result_msg="加载微信客服信息失败",
                execute_exceptions=[str(e)]
            )]
        }


def load_order_history_node(state: SagtState, config: RunnableConfig):
    """
    加载订单历史节点
    
    从数据存储中获取客户的订单历史记录。
    首先获取客户信息中的 union_id，然后使用 union_id 查询订单历史。
    
    Args:
        state: 当前状态对象
        config: 运行配置，包含 user_id 和 external_id
        
    Returns:
        包含订单历史的状态更新字典，成功时包含订单记录，失败时包含错误信息
    """
    logger.info("=== 加载订单信息 ===")

    # 从配置中获取跟进人ID和客户外部ID
    follow_user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    external_id = config[ConfigurableField.configurable][ConfigurableField.external_id]
    
    logger.info(f"follow_user_id: {follow_user_id}")
    logger.info(f"external_id: {external_id}")
    
    # 获取客户信息以获取 union_id
    customer_info: CustomerInfo = get_customer_info(
        external_id=external_id, 
        follow_user_id=follow_user_id
    )
    union_id = customer_info.union_id

    # 直接调用工具函数，传递配置
    try:
        # 检查 union_id 是否存在
        if not union_id:
            # 如果没有 union_id，返回错误状态
            return {
                SagtStateField.ORDER_HISTORY: OrderHistory(),
                SagtStateField.NODE_RESULT: [NodeResult(
                    execute_node_name=NodeName.LOAD_ORDER_HISTORY.value,
                    execute_result_code=1,
                    execute_result_msg="没有获取到该客户的union_id",
                    execute_exceptions=["客户信息中没有union_id"]
                )]
            }

        # 使用 union_id 查询订单历史
        order_history: OrderHistory = get_order_history(union_id=union_id)
        logger.info(f"订单信息: {order_history}")
        
        # 返回成功结果
        return {
            SagtStateField.ORDER_HISTORY: order_history,  # 存储订单历史到状态
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_ORDER_HISTORY.value,
                execute_result_code=0,
                execute_result_msg="完成订单信息加载",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 捕获异常，记录错误日志并返回默认值
        logger.error(f"加载订单信息失败: {e}")
        return {
            SagtStateField.ORDER_HISTORY: OrderHistory(),  # 返回空的订单历史对象
            SagtStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.LOAD_ORDER_HISTORY.value,
                execute_result_code=1,
                execute_result_msg="加载订单信息失败",
                execute_exceptions=[str(e)]
            )]
        }