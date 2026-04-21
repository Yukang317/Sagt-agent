"""SAGT Agent 核心节点定义文件

本文件定义了主图的核心处理节点，包括状态清理、欢迎消息、意图检测和任务结果确认等关键节点。
这些节点构成了状态图的基础控制流。
"""

# 导入枚举模块
from enum import Enum

# 导入类型定义模块
from typing_extensions import Literal
# 导入 LangGraph 命令类型，用于节点间路由
from langgraph.types import Command
# 导入日志工具
from utils.agent_logger import get_logger
# 导入 LangChain 可运行配置
from langchain_core.runnables import RunnableConfig
# 导入状态定义
from graphs.sagt_graph.sagt_state import SagtState, SagtStateField
# 导入业务模型
from models.sagt_models import Intent, NodeResult
# 导入意图检测 LLM 服务
from llm.llm_intent_detect import llm_intent_detect

# 获取节点模块的日志实例
logger = get_logger("sagt_node")

class NodeName(str, Enum):
    """
    节点名称枚举定义
    
    定义了主图中所有节点的唯一标识符，包括核心处理节点和子图节点。
    """
    # 主图核心节点
    CLEANUP_STATE       = "cleanup_state"       # 状态清理节点
    WELCOME_MESSAGE     = "sagt_welcome_message"# 欢迎消息节点
    INTENT_DETECTION    = "intent_detection"    # 意图检测节点
    TASK_RESULT_CONFIRM = "task_result_confirm" # 任务结果确认节点

    # 子图节点（意图识别后路由到对应的子图）
    CHAT_SUGGESTION     = "chat_suggestion"      # 生成客户聊天建议子图
    KF_CHAT_SUGGESTION  = "kf_chat_suggestion"   # 生成客服聊天建议子图
    TAG_SUGGESTION      = "tag_suggestion"       # 生成客户标签子图
    PROFILE_SUGGESTION  = "profile_suggestion"   # 生成客户画像子图
    SCHEDULE_SUGGESTION = "schedule_suggestion"  # 生成客户日程子图
    NO_CLEAR_INTENTION  = "no_clear_intention"   # 未明确意图闲聊子图

class IntentDetection(str, Enum):
    """
    意图检测枚举定义
    
    定义了系统支持的所有意图类型，与 NodeName 中的子图节点一一对应。
    用于意图识别后的路由决策。
    """
    CHAT_SUGGESTION     = NodeName.CHAT_SUGGESTION.value      # 客户聊天建议意图
    KF_CHAT_SUGGESTION  = NodeName.KF_CHAT_SUGGESTION.value   # 客服聊天建议意图
    TAG_SUGGESTION      = NodeName.TAG_SUGGESTION.value       # 客户标签意图
    PROFILE_SUGGESTION  = NodeName.PROFILE_SUGGESTION.value   # 客户画像意图
    SCHEDULE_SUGGESTION = NodeName.SCHEDULE_SUGGESTION.value  # 客户日程意图
    NO_CLEAR_INTENTION  = NodeName.NO_CLEAR_INTENTION.value   # 未明确意图

def cleanup_state_node(state: SagtState, config: RunnableConfig):
    """
    状态清理节点
    
    在每次会话开始时清理所有状态字段，确保状态图从干净状态开始执行。
    重置所有输入状态、中间状态和输出状态为初始值（None）。
    
    Args:
        state: 当前状态对象
        config: 运行配置
        
    Returns:
        包含所有状态字段重置值的字典
    """
    logger.info("=== 清理状态 ===")
    
    return {
        # 执行结果字段重置
        SagtStateField.NODE_RESULT: None,
        SagtStateField.TASK_RESULT: None,
        
        # 加载信息字段重置
        SagtStateField.EMPLOYEE_INFO: None,
        SagtStateField.CHAT_HISTORY: None,
        SagtStateField.KF_CHAT_HISTORY: None,
        SagtStateField.ORDER_HISTORY: None,
        SagtStateField.TAG_SETTING: None,
        SagtStateField.CUSTOMER_INFO: None,
        SagtStateField.CUSTOMER_TAGS: None,
        SagtStateField.CUSTOMER_PROFILE: None,
        
        # 中间输出字段重置
        SagtStateField.SUGGESTION_PROFILE: None,
        SagtStateField.SUGGESTION_TAG: None,
        SagtStateField.SUGGESTION_CHAT: None,
        SagtStateField.SUGGESTION_KF: None,
        SagtStateField.SUGGESTION_SCHEDULE: None,
        SagtStateField.NOTIFY_CONTENT: None,
    }

def welcome_message(state: SagtState, config: RunnableConfig):
    """
    欢迎消息节点
    
    在会话开始时向用户发送欢迎消息，告知用户系统已准备就绪。
    
    Args:
        state: 当前状态对象
        config: 运行配置
        
    Returns:
        包含节点执行结果的字典，包含欢迎消息内容
    """
    logger.info("=== 欢迎消息 ===")
    
    return {
        SagtStateField.NODE_RESULT: 
        [NodeResult(
            execute_node_name=NodeName.WELCOME_MESSAGE.value,  # 节点名称
            execute_result_code=0,                             # 执行结果码（0表示成功）
            execute_result_msg="您好，我是Sagt，很高兴为您服务",  # 欢迎消息内容
            execute_exceptions=[]                              # 异常列表（空表示无异常）
        )]
    }

def intent_detection(state: SagtState, config: RunnableConfig) -> Command[Literal[*[intent.value for intent in IntentDetection]]]:
    """
    意图检测节点
    
    根据用户输入识别业务意图，并路由到对应的处理子图。
    
    处理逻辑：
    1. 定义支持的意图列表及描述
    2. 获取用户输入的任务内容
    3. 如果输入直接是意图标识，则直接路由
    4. 否则（当前实现）默认路由到闲聊子图
    
    Args:
        state: 当前状态对象，包含用户输入
        config: 运行配置
        
    Returns:
        Command 对象，包含要跳转的目标节点名称
    """
    logger.info("=== 意图检测 ===")
    
    # 定义系统支持的意图列表及对应的业务场景描述
    intents = [
        Intent(
            intent_id=IntentDetection.CHAT_SUGGESTION.value,
            intent_description="我是销售人员，正在和客户沟通，我需要知道如何回复比较合适————客户聊天建议(sub_chat_suggestion)"
        ),
        Intent(
            intent_id=IntentDetection.KF_CHAT_SUGGESTION.value,
            intent_description="我是企业客服，在帮助客户解决问题，请帮助我生成客服回复建议————客户聊天建议(sub_kf_chat_suggestion)"
        ),
        Intent(
            intent_id=IntentDetection.TAG_SUGGESTION.value,
            intent_description="我的客户情况有更新，我需要更新客户标签————客户标签(sub_tag)"
        ),
        Intent(
            intent_id=IntentDetection.PROFILE_SUGGESTION.value,
            intent_description="我的客户情况有更新，我需要更新客户画像————客户画像(sub_profile)"
        ),
        Intent(
            intent_id=IntentDetection.SCHEDULE_SUGGESTION.value,
            intent_description="我和客户沟通过程中，我需要创建日程，方便提醒我跟进事项————客户日程(sub_schedule)"
        ),
        Intent(
            intent_id=IntentDetection.NO_CLEAR_INTENTION.value,
            intent_description="我想咨询一些问题，或者没有明确的意图，仅仅是聊聊天————未明确意图(sub_talk)"
        )
    ]

    # 获取用户输入的任务内容
    task_input = state.get(SagtStateField.TASK_INPUT, "")

    # 如果任务输入直接是意图标识字符串，则直接跳转到对应节点
    if task_input in [intent.value for intent in IntentDetection]:
        return Command(goto=task_input)

    # 暂时不做意图检测，直接返回未明确意图，如果不在意图列表中，则默认设置为未明确意图
    # TODO: 生产环境应启用 LLM 意图检测
    # intent = llm_intent_detect(task_input, intents)
    
    # 非任务值，直接返回未明确意图
    # 当前实现：默认路由到未明确意图（闲聊）子图
    intent_id = IntentDetection.NO_CLEAR_INTENTION.value
    
    # 安全检查：确保意图ID在合法范围内.如果意图不在意图列表中，则默认设置为未明确意图  
    if intent_id not in [intent.value for intent in IntentDetection]:
        intent_id = IntentDetection.NO_CLEAR_INTENTION.value 
    
    # 返回路由命令
    return Command(goto=intent_id)
    

def task_result_confirm(state: SagtState, config: RunnableConfig):
    """
    任务结果确认节点
    
    在所有子图执行完成后，确认任务已完成并返回最终结果。
    
    Args:
        state: 当前状态对象
        config: 运行配置
        
    Returns:
        包含任务完成确认信息的字典
    """
    logger.info("=== 任务结果确认 ===")

    return {
        SagtStateField.NODE_RESULT: 
        [NodeResult(
            execute_node_name=NodeName.TASK_RESULT_CONFIRM.value,  # 节点名称
            execute_result_code=0,                                  # 执行结果码（0表示成功）
            execute_result_msg="任务已完成，希望您能满意",            # 任务完成消息
            execute_exceptions=[]                                   # 异常列表（空表示无异常）
        )]
    }