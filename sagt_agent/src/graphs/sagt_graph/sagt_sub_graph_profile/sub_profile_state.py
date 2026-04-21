"""客户画像子图状态定义文件

本文件定义了客户画像子图的状态结构，包括输入状态、中间输出状态和输出状态。
子图状态与主图状态通过字段名称映射实现数据共享。
"""

# 导入操作符模块，用于状态合并
import operator
# 导入类型定义模块
from typing import TypedDict, Annotated, List
# 导入主图状态字段定义，用于字段名称映射
from graphs.sagt_graph.sagt_state import SagtStateField
# 导入业务模型类
from models.sagt_models import (
    ChatHistory,        # 聊天历史模型
    KFChatHistory,      # 客服聊天历史模型
    OrderHistory,       # 订单历史模型
    CustomerProfile,    # 客户画像模型
    CustomerTags,       # 客户标签模型
    TaskResult,         # 任务结果模型
    NodeResult          # 节点执行结果模型
)
# 导入枚举模块
from enum import Enum


class SubProfileStateField(str, Enum):
    """
    客户画像子图状态字段名称枚举
    
    通过继承主图状态字段名称，实现子图与主图之间的数据共享。
    所有字段名称与主图保持一致，确保状态能够正确传递。
    """
    
    # 输入字段 - 从主图状态继承
    CHAT_HISTORY = SagtStateField.CHAT_HISTORY.value       # 销售人员与客户的聊天历史
    KF_CHAT_HISTORY = SagtStateField.KF_CHAT_HISTORY.value # 客户与微信客服的聊天历史
    ORDER_HISTORY = SagtStateField.ORDER_HISTORY.value     # 客户订单历史
    CUSTOMER_TAGS = SagtStateField.CUSTOMER_TAGS.value     # 客户当前标签
    CUSTOMER_PROFILE = SagtStateField.CUSTOMER_PROFILE.value # 客户当前画像
    
    # 中间输出字段 - 生成的建议结果
    NOTIFY_CONTENT = SagtStateField.NOTIFY_CONTENT.value           # 发送给用户的通知内容
    SUGGESTION_PROFILE = SagtStateField.SUGGESTION_PROFILE.value   # AI生成的客户画像建议

    # 输出字段 - 任务结果
    TASK_RESULT = SagtStateField.TASK_RESULT.value   # 任务最终结果
    NODE_RESULT = SagtStateField.NODE_RESULT.value   # 各节点执行结果列表

class SubProfileInputState(TypedDict):
    """
    客户画像子图输入状态定义
    
    定义了子图执行所需的输入数据，这些数据从主图状态中获取。
    """
    chat_history:       ChatHistory    # 销售人员与客户的聊天历史记录
    kf_chat_history:    KFChatHistory # 客户与微信客服的聊天历史记录
    order_history:      OrderHistory   # 客户的订单历史记录
    customer_tags:      CustomerTags   # 客户当前拥有的标签列表
    customer_profile:   CustomerProfile # 客户现有的画像信息

class SubProfileIntermediateOutputState(TypedDict):
    """
    客户画像子图中间输出状态定义
    
    定义了子图执行过程中生成的中间结果，用于后续处理或通知用户。
    """
    notify_content:     str             # 需要发送给用户的通知消息内容
    suggestion_profile: CustomerProfile # AI生成的新客户画像建议

class SubProfileOutputState(TypedDict):
    """
    客户画像子图输出状态定义
    
    定义了子图执行完成后输出的最终结果，将返回给主图。
    """
    task_result: TaskResult                          # 任务执行的最终结果
    node_result: Annotated[List[NodeResult], operator.add]  # 各节点执行结果（使用加法合并）

# 使用多重继承，自动合并所有字段类型
class SubProfileState(SubProfileInputState, SubProfileIntermediateOutputState, SubProfileOutputState):
    """
    客户画像子图的完整状态定义
    
    通过多重继承整合输入状态、中间输出状态和输出状态，形成统一的状态结构。
    该状态与主图状态通过字段名称映射实现数据共享，子图可以直接访问主图加载的数据，
    生成的建议结果也会自动同步回主图状态。
    """
    pass