"""SAGT Agent 状态定义文件

本文件定义了 SAGT Agent 状态图的核心数据结构，包括输入状态、输出状态、中间状态和配置信息。
这些状态结构在节点间传递数据，实现整个系统的状态管理。
"""

# 导入操作符模块
import operator
# 导入类型定义模块
from typing_extensions import Annotated, List, TypedDict
# 导入枚举模块
from enum import Enum
# 导入业务模型类
from models.sagt_models import (
    ScheduleSuggestion,  # 日程建议模型
    TagSetting,          # 标签设置模型
    EmployeeInfo,        # 员工信息模型
    ChatHistory,         # 聊天历史模型
    KFChatHistory,       # 微信客服聊天历史模型
    OrderHistory,        # 订单历史模型
    TaskResult,          # 任务结果模型
    NodeResult           # 节点执行结果模型
)
from models.sagt_models import (
    CustomerInfo,        # 客户信息模型
    TagSuggestion,       # 标签建议模型
    ReplySuggestion,     # 回复建议模型
    CustomerProfile,     # 客户画像模型
    CustomerTags         # 客户标签模型
)


def reducer_node_result(current: List[NodeResult], update: List[NodeResult]) -> List[NodeResult]:
    """
    自定义 node_result 的 reducer 函数，用于合并节点执行结果列表
    
    LangGraph 中状态更新时会调用 reducer 函数来处理状态字段的合并。
    本函数实现了节点结果的累加逻辑：
    - 如果新更新为空列表，则重置结果列表
    - 否则将新结果追加到现有结果列表中
    
    Args:
        current: 当前状态中的节点结果列表
        update: 新的节点结果更新列表
        
    Returns:
        合并后的节点结果列表
    """
    # 如果 update 为空列表，则置空 node_result
    if not update: 
        return []

    # 否则，将新结果追加到现有结果列表中
    return current + update

class InputState(TypedDict):
    '''
    主图的输入状态定义
    
    定义了进入状态图时需要提供的初始输入数据。
    '''
    task_input: str  # 任务输入，即用户的查询或请求内容


class OutputState(TypedDict):
    '''
    主图的输出状态定义
    
    定义了状态图执行完成后输出的结果数据。
    '''
    task_result: TaskResult                          # 任务执行结果
    node_result: Annotated[List[NodeResult], reducer_node_result]  # 各节点执行结果列表（使用自定义reducer合并）

class IntermediateInputState(TypedDict):
    '''
    中间输入状态定义
    
    定义了从外部数据源加载的各类信息，为后续业务处理提供数据基础。
    '''
    employee_info:      EmployeeInfo      # 员工信息
    chat_history:       ChatHistory       # 聊天历史记录
    kf_chat_history:    KFChatHistory    # 微信客服聊天历史
    order_history:      OrderHistory      # 订单历史记录
    tag_setting:        TagSetting        # 标签设置配置
    customer_info:      CustomerInfo      # 客户基本信息
    customer_tags:      CustomerTags      # 客户标签列表
    customer_profile:   CustomerProfile   # 客户画像信息

class IntermediateOutputState(TypedDict):
    '''
    中间输出状态定义
    
    定义了各子图生成的建议结果，用于后续处理或返回给用户。
    '''
    suggestion_profile: CustomerProfile    # 生成的客户画像建议
    suggestion_tag:     TagSuggestion      # 生成的客户标签建议
    suggestion_chat:    ReplySuggestion    # 生成的客户聊天回复建议
    suggestion_kf:      ReplySuggestion    # 生成的客服聊天回复建议
    suggestion_schedule:ScheduleSuggestion # 生成的客户日程建议
    notify_content:     str                # 通知内容

class SagtState(InputState, IntermediateInputState, IntermediateOutputState, OutputState):
    '''
    主图的完整状态定义
    
    通过多重继承整合所有状态类型，形成统一的状态结构。
    包含：输入状态、中间输入状态、中间输出状态、输出状态。
    '''
    pass

class SagtStateField(str, Enum):
    '''
    主图状态字段名称枚举定义
        主图的State字段名称定义，避免在代码里直接写字符串，eg：不用写 "employee_info" ，而是写 SagtStateField.EMPLOYEE_INFO.value
    提供类型安全的状态字段访问方式，避免硬编码字符串导致的错误。
    '''

    # 任务输入字段
    TASK_INPUT          = "task_input"

    # 加载的信息字段（从外部数据源获取）
    EMPLOYEE_INFO       = "employee_info"      # 员工信息
    CHAT_HISTORY        = "chat_history"       # 聊天历史
    KF_CHAT_HISTORY     = "kf_chat_history"    # 微信客服聊天历史
    ORDER_HISTORY       = "order_history"      # 订单历史
    TAG_SETTING         = "tag_setting"        # 标签设置
    CUSTOMER_INFO       = "customer_info"      # 客户信息
    CUSTOMER_TAGS       = "customer_tags"      # 客户标签
    CUSTOMER_PROFILE    = "customer_profile"   # 客户画像

    # 中间输出字段（各子图生成的建议）
    SUGGESTION_PROFILE  = "suggestion_profile"   # 客户画像建议
    SUGGESTION_TAG      = "suggestion_tag"       # 客户标签建议
    SUGGESTION_CHAT     = "suggestion_chat"      # 客户聊天建议
    SUGGESTION_KF       = "suggestion_kf"        # 客服聊天建议
    SUGGESTION_SCHEDULE = "suggestion_schedule"  # 客户日程建议
    NOTIFY_CONTENT      = "notify_content"       # 通知内容

    # 执行结果字段
    TASK_RESULT         = "task_result"   # 任务最终结果
    NODE_RESULT         = "node_result"   # 各节点执行结果列表


class SagtConfig(TypedDict):
    '''
    主图的配置参数定义
    - 运行时系统需要知道当前是哪个员工在使用，才能加载对应客户的信息
    定义了状态图执行时需要的配置信息，通过 config 参数传递给各节点。
    '''
    user_id:      str  # 当前操作用户ID（销售人员/客服人员）
    external_id:  str  # 外部客户ID（用于标识具体客户）


class ConfigurableField(str, Enum):
    '''
    配置字段名称枚举定义
    
    提供类型安全的配置字段访问方式。
    主图的配置字段名称定义，给配置参数的“访问路径”起别名。
    比如，要获取员工ID，不用写 config["configurable"]["user_id"] ，而是写 config[ConfigurableField.configurable][ConfigurableField.user_id] 。
    '''
    configurable    = "configurable"   # 配置根节点
    user_id         = "user_id"        # 用户ID配置字段
    external_id     = "external_id"    # 外部客户ID配置字段
    
