"""客服聊天建议子图状态定义文件

本文件定义了客服聊天建议子图的状态结构，包括输入状态、中间输出状态和输出状态。
子图状态与主图状态通过字段名称映射实现数据共享。

业务背景：该子图用于为企业客服人员生成与客户聊天的回复建议，
基于客服聊天历史和客户信息，调用LLM生成合适的回复内容。

与普通聊天建议的区别：
- 普通聊天建议：面向销售人员，处理私域聊天场景
- 客服聊天建议：面向客服人员，处理微信客服聊天场景
"""

# 导入操作符模块，用于状态合并
import operator
# 导入类型定义模块
from typing import TypedDict, Annotated, List
# 导入主图状态字段定义，用于字段名称映射
from graphs.sagt_graph.sagt_state import SagtStateField
# 导入业务模型类
from models.sagt_models import (
    KFChatHistory,    # 客服聊天历史模型
    CustomerInfo,     # 客户信息模型
    ReplySuggestion,  # 回复建议模型
    TaskResult,       # 任务结果模型
    NodeResult        # 节点执行结果模型
)
# 导入枚举模块
from enum import Enum


class SubKFChatSuggestionStateField(str, Enum):
    """
    客服聊天建议子图状态字段名称枚举
    
    通过继承主图状态字段名称，实现子图与主图之间的数据共享。
    所有字段名称与主图保持一致，确保状态能够正确传递。
    """
    
    # 输入字段 - 从主图状态继承
    KF_CHAT_HISTORY = SagtStateField.KF_CHAT_HISTORY.value  # 客户与微信客服的聊天历史
    CUSTOMER_INFO = SagtStateField.CUSTOMER_INFO.value       # 客户基本信息

    # 中间输出字段 - 生成的建议结果
    SUGGESTION_KF = SagtStateField.SUGGESTION_KF.value       # AI生成的客服回复建议

    # 输出字段 - 任务结果
    TASK_RESULT = SagtStateField.TASK_RESULT.value   # 任务最终结果
    NODE_RESULT = SagtStateField.NODE_RESULT.value   # 各节点执行结果列表

class SubKFChatSuggestionInputState(TypedDict):
    """
    客服聊天建议子图输入状态定义
    
    定义了子图执行所需的输入数据，这些数据从主图状态中获取。
    """
    customer_info:      CustomerInfo     # 客户的基本标识信息
    kf_chat_history:    KFChatHistory   # 客户与微信客服的聊天历史记录

class SubKFChatSuggestionIntermediateOutputState(TypedDict):
    """
    客服聊天建议子图中间输出状态定义
    
    定义了子图执行过程中生成的中间结果。
    """
    suggestion_kf:      ReplySuggestion  # AI生成的客服回复建议

class SubKFChatSuggestionOutputState(TypedDict):
    """
    客服聊天建议子图输出状态定义
    
    定义了子图执行完成后输出的最终结果，将返回给主图。
    """
    task_result:        TaskResult                          # 任务执行的最终结果
    node_result:        Annotated[List[NodeResult], operator.add]  # 各节点执行结果（使用加法合并）
    
# 使用多重继承，自动合并所有字段类型
class SubKFChatSuggestionState(SubKFChatSuggestionInputState, SubKFChatSuggestionIntermediateOutputState, SubKFChatSuggestionOutputState):
    """
    客服聊天建议子图的完整状态定义
    
    通过多重继承整合输入状态、中间输出状态和输出状态，形成统一的状态结构。
    该状态与主图状态通过字段名称映射实现数据共享，子图可以直接访问主图加载的数据，
    生成的建议结果也会自动同步回主图状态。
    
    业务特点：该子图流程相对简单，无需人工确认，直接生成建议返回结果。
    适用场景：企业微信客服与客户的沟通场景。
    """
    pass