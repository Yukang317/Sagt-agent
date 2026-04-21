"""客户聊天建议子图节点定义文件

本文件定义了客户聊天建议子图的所有节点实现，包括：
- 欢迎消息节点：向用户发送开始提示
- 生成聊天建议节点：调用LLM生成聊天回复建议

业务流程：发送欢迎消息 → 生成聊天建议 → 返回结果

业务背景：该子图为销售人员提供与客户聊天的智能回复建议，
基于聊天历史上下文和客户信息，自动生成合适的回复内容。

核心特点：流程简单，无需人工确认，直接返回建议结果。
"""

# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_chat_suggestion.sub_chat_suggestion_state import SubChatSuggestionState
from graphs.sagt_graph.sagt_sub_graph_chat_suggestion.sub_chat_suggestion_state import SubChatSuggestionStateField
# 导入业务模型类
from models.sagt_models import (
    CustomerInfo,       # 客户信息模型
    EmployeeInfo,       # 员工信息模型
    ChatHistory,        # 聊天历史模型
    ReplySuggestion,    # 回复建议模型
    TaskResult,         # 任务结果模型
    NodeResult          # 节点执行结果模型
)
# 导入日志工具
from utils.agent_logger import get_logger
# 导入LangChain可运行配置
from langchain_core.runnables import RunnableConfig
# 导入聊天建议生成函数
from llm.llm_suggest_chat import llm_chat_suggest
# 导入日期时间模块
from datetime import datetime
# 导入枚举模块
from enum import Enum

# 获取子图节点模块的日志实例
logger = get_logger("sub_chat_suggestion_node")

class NodeName(str, Enum):
    """
    客户聊天建议子图节点名称枚举
    
    定义了子图中所有节点的唯一标识符：
    - WELCOME_MESSAGE: 欢迎消息节点
    - GENERATE_CHAT_SUGGESTION: 生成聊天建议节点
    """
    WELCOME_MESSAGE          = "chat_welcome_node"      # 欢迎消息节点
    GENERATE_CHAT_SUGGESTION = "chat_generate_node"     # 生成聊天建议节点

def welcome_message_node(state: SubChatSuggestionState, config: RunnableConfig):
    """
    欢迎消息节点
    
    子图执行的第一个节点，向用户发送任务开始提示消息，
    告知用户系统正在生成聊天建议。
    
    Args:
        state: 当前子图状态
        config: 运行配置
        
    Returns:
        状态更新字典，包含节点执行结果
    """
    logger.info("=== 欢迎信息 ===")
    
    return {
        SubChatSuggestionStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.WELCOME_MESSAGE.value,  # 节点名称
            execute_result_code=0,                             # 成功码
            execute_result_msg="正在为您生成聊天建议，请稍等。", # 提示消息
            execute_exceptions=[]                              # 无异常
        )]
    }

def generate_chat_suggestion_node(state: SubChatSuggestionState, config: RunnableConfig):
    """
    生成聊天建议节点（核心业务节点）
    
    调用LLM分析聊天历史上下文和客户信息，生成合适的回复建议。
    输入数据包括：客户信息、员工信息、聊天历史、当前时间。
    
    业务逻辑：
    1. 从状态中获取输入数据（客户信息、员工信息、聊天历史）
    2. 调用LLM生成聊天回复建议
    3. 将建议内容作为任务结果返回
    
    特点：该子图无需人工确认，直接返回生成的建议给用户。
    
    Args:
        state: 当前子图状态，包含输入数据
        config: 运行配置
        
    Returns:
        状态更新字典，包含生成的聊天建议、任务结果和节点执行结果
    """
    logger.info("=== 生成聊天建议 ===")
    logger.debug(f"config: {config}")

    try:
        # 调用LLM生成聊天建议
        # 传入客户信息、员工信息和聊天历史供LLM分析
        chat_suggestion: ReplySuggestion = llm_chat_suggest(
            customer_info=state.get(SubChatSuggestionStateField.CUSTOMER_INFO, CustomerInfo()),  # 客户信息
            employee_info=state.get(SubChatSuggestionStateField.EMPLOYEE_INFO, EmployeeInfo()),  # 员工信息
            chat_history=state.get(SubChatSuggestionStateField.CHAT_HISTORY, ChatHistory()),    # 聊天历史
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")                           # 当前时间
        )   

        # 返回成功结果
        return {
            SubChatSuggestionStateField.SUGGESTION_CHAT: chat_suggestion,  # 存储生成的聊天建议
            SubChatSuggestionStateField.TASK_RESULT: TaskResult(
                task_result=chat_suggestion.reply_content,       # 回复内容作为任务结果
                task_result_explain=chat_suggestion.reply_reason, # 回复原因作为解释
                task_result_code=0                               # 成功码
            ),
            SubChatSuggestionStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.GENERATE_CHAT_SUGGESTION.value,
                execute_result_code=0,
                execute_result_msg="生成聊天建议成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理异常情况
        logger.error(f"生成聊天建议失败: {e}")
        return {
            SubChatSuggestionStateField.SUGGESTION_CHAT: ReplySuggestion(),  # 返回空建议
            SubChatSuggestionStateField.TASK_RESULT: TaskResult(
                task_result=f"很抱歉，生成聊天建议过程中，遇到了问题。",
                task_result_explain=f"生成聊天建议失败",
                task_result_code=1  # 失败码
            ),
            SubChatSuggestionStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.GENERATE_CHAT_SUGGESTION.value,
                execute_result_code=1,
                execute_result_msg=f"生成聊天建议失败",
                execute_exceptions=[str(e)]
            )]
        }

