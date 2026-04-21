"""客户日程子图状态定义文件

本文件定义了客户日程子图的状态结构，包括输入状态、中间状态和输出状态。
子图状态与主图状态通过字段名称映射实现数据共享。

业务背景：该子图用于为销售人员生成**客户跟进日程建议**，并自动创建到企业微信日历中。
基于聊天历史和客户信息，AI生成合适的日程安排建议。

核心特点：
- 生成日程建议后直接创建到企业微信
- 无需人工确认环节
- 与企业微信日历深度集成
"""

# 导入操作符模块，用于状态合并
import operator
# 导入类型定义模块
from typing import TypedDict, Annotated, List
# 导入主图状态字段定义，用于字段名称映射
from graphs.sagt_graph.sagt_state import SagtStateField
# 导入业务模型类
from models.sagt_models import (
    CustomerInfo,       # 客户信息模型
    ScheduleSuggestion, # 日程建议模型
    ChatHistory,        # 聊天历史模型
    TaskResult,         # 任务结果模型
    NodeResult          # 节点执行结果模型
)
# 导入枚举模块
from enum import Enum

class SubScheduleStateField(str, Enum):
    """
    客户日程子图状态字段名称枚举
    
    通过继承主图状态字段名称，实现子图与主图之间的数据共享。
    所有字段名称与主图保持一致，确保状态能够正确传递。
    """
    # 输入字段 - 从主图状态继承
    CUSTOMER_INFO       = SagtStateField.CUSTOMER_INFO.value       # 客户基本信息
    CHAT_HISTORY        = SagtStateField.CHAT_HISTORY.value        # 销售人员与客户的聊天历史
    
    # 中间字段 - 生成的建议结果
    SUGGESTION_SCHEDULE = SagtStateField.SUGGESTION_SCHEDULE.value # AI生成的日程建议
    
    # 输出字段 - 任务结果
    TASK_RESULT         = SagtStateField.TASK_RESULT.value   # 任务最终结果
    NODE_RESULT         = SagtStateField.NODE_RESULT.value   # 各节点执行结果列表

class SubScheduleInputState(TypedDict):
    """
    客户日程子图输入状态定义
    
    定义了子图执行所需的输入数据，这些数据从主图状态中获取。
    """
    customer_info:      CustomerInfo     # 客户的基本标识信息
    chat_history:       ChatHistory      # 销售人员与客户的聊天历史记录

class SubScheduleIntermediateState(TypedDict):
    """
    客户日程子图中间状态定义
    
    定义了子图执行过程中生成的中间结果，用于后续节点使用。
    """
    suggestion_schedule: ScheduleSuggestion  # AI生成的日程安排建议

class SubScheduleOutputState(TypedDict):
    """
    客户日程子图输出状态定义
    
    定义了子图执行完成后输出的最终结果，将返回给主图。
    """
    task_result: TaskResult                          # 任务执行的最终结果
    node_result: Annotated[List[NodeResult], operator.add]  # 各节点执行结果（使用加法合并）

# 使用多重继承，自动合并所有字段类型
class SubScheduleState(SubScheduleInputState, SubScheduleIntermediateState, SubScheduleOutputState):
    """
    客户日程子图的完整状态定义
    
    通过多重继承整合输入状态、中间状态和输出状态，形成统一的状态结构。
    该状态与主图状态通过字段名称映射实现数据共享，子图可以直接访问主图加载的数据，
    生成的建议结果也会自动同步回主图状态。
    
    业务特点：生成日程建议后直接调用企业微信API创建日程，无需人工确认。
    """
    pass