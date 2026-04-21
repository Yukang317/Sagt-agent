"""闲聊子图定义文件（单一文件模式）

本文件定义了闲聊子图的完整实现，包括状态定义、节点实现和图定义。
该子图用于处理用户的非业务相关请求，如闲聊、咨询等。

业务背景：当用户没有明确的业务意图（如生成客户画像、标签建议等），
或者只是想进行普通对话时，系统会路由到该子图进行处理。

核心特点：
- 最简单的子图流程，仅包含欢迎消息和回复两个节点
- 直接调用LLM进行自由对话，无需业务数据
- 作为兜底子图，处理所有未明确意图的请求

业务流程：发送欢迎消息 → LLM生成回复 → 返回结果
"""

# 导入操作符模块，用于状态合并
import operator
# 导入类型定义模块
from typing import TypedDict, Annotated, List
# 导入枚举模块
from enum import Enum
# 导入LangGraph核心组件
from langgraph.graph import StateGraph, START, END
# 导入LangChain可运行配置
from langchain_core.runnables import RunnableConfig
# 导入日志工具
from utils.agent_logger import get_logger
# 导入闲聊回复生成函数
from llm.llm_just_talk import llm_just_talk
# 导入主图状态字段定义，用于字段名称映射
from graphs.sagt_graph.sagt_state import SagtStateField
# 导入配置定义
from graphs.sagt_graph.sagt_state import SagtConfig
# 导入业务模型类
from models.sagt_models import (
    TaskResult,      # 任务结果模型
    NodeResult,      # 节点执行结果模型
    JustTalkOutput   # 闲聊输出模型
)

# 获取子图的日志实例
logger = get_logger("sub_talk_graph")

class SubTalkStateField(str, Enum):
    """
    闲聊子图状态字段名称枚举
    
    通过继承主图状态字段名称，实现子图与主图之间的数据共享。
    该子图是最简单的子图，仅需要任务输入和任务结果字段。
    """
    TASK_INPUT  = SagtStateField.TASK_INPUT.value   # 用户输入的任务内容
    TASK_RESULT = SagtStateField.TASK_RESULT.value # 任务执行结果
    NODE_RESULT = SagtStateField.NODE_RESULT.value # 节点执行结果列表

class SubTalkInputState(TypedDict):
    """
    闲聊子图输入状态定义
    
    定义了子图执行所需的输入数据。
    由于是闲聊场景，仅需要用户的输入内容。
    """
    task_input: str  # 用户输入的问题或对话内容

class SubTalkOutputState(TypedDict):
    """
    闲聊子图输出状态定义
    
    定义了子图执行完成后输出的最终结果。
    """
    task_result: TaskResult                          # 任务执行的最终结果
    node_result: Annotated[List[NodeResult], operator.add]  # 各节点执行结果（使用加法合并）

# 使用多重继承，自动合并所有字段类型
class SubTalkState(SubTalkInputState, SubTalkOutputState):
    """
    闲聊子图的完整状态定义
    
    通过多重继承整合输入状态和输出状态，形成统一的状态结构。
    该状态与主图状态通过字段名称映射实现数据共享。
    
    业务特点：该子图是最简单的子图，无需复杂的业务数据，
    仅处理用户的自由对话请求。
    """
    pass


class NodeName(str, Enum):
    """
    闲聊子图节点名称枚举
    
    定义了子图中所有节点的唯一标识符：
    - WELCOME_MESSAGE: 欢迎消息节点
    - JUST_TALK: 闲聊回复节点
    """
    WELCOME_MESSAGE = "talk_welcome_node"   # 欢迎消息节点
    JUST_TALK       = "talk_reply_node"     # 闲聊回复节点

def welcome_message_node(state: SubTalkState, config: RunnableConfig):
    """
    欢迎消息节点
    
    子图执行的第一个节点，向用户发送任务开始提示消息，
    告知用户系统正在生成回复。
    
    Args:
        state: 当前子图状态
        config: 运行配置
        
    Returns:
        状态更新字典，包含节点执行结果
    """
    logger.info("=== 欢迎消息 ===")
    
    return {
        SubTalkStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.JUST_TALK.value,  # 节点名称
            execute_result_code=0,                       # 成功码
            execute_result_msg="正在为您生成回复，请稍等。", # 提示消息
            execute_exceptions=[]                        # 无异常
        )]
    }

def just_talk_node(state: SubTalkState, config: RunnableConfig):
    """
    闲聊回复节点（核心业务节点）
    
    调用LLM直接处理用户的自由对话请求，无需业务数据。
    该节点是闲聊子图的核心，负责生成自然语言回复。
    
    业务逻辑：
    1. 从状态中获取用户输入
    2. 调用LLM生成回复
    3. 检查回复是否有效（非空）
    4. 返回结果
    
    适用场景：
    - 用户没有明确的业务意图
    - 用户想进行普通聊天
    - 用户咨询非业务相关问题
    
    Args:
        state: 当前子图状态，包含用户输入
        config: 运行配置
        
    Returns:
        状态更新字典，包含任务结果和节点执行结果
    """
    logger.info("=== 咨询回复 ===")

    try:
        # 调用LLM生成闲聊回复
        # 仅传入用户输入，无需业务数据
        generated_just_talk_output: JustTalkOutput = llm_just_talk(
            input=state.get(SubTalkStateField.TASK_INPUT, "")  # 获取用户输入
        )
        logger.info(f"generated_just_talk_output: {generated_just_talk_output}")

        # 检查回复是否有效（非空）
        if not generated_just_talk_output.just_talk_output:
            return {
                SubTalkStateField.TASK_RESULT: TaskResult(
                    task_result="我好像没有理解你的意思",
                    task_result_explain="生成回复失败",
                    task_result_code=1
                ),
                SubTalkStateField.NODE_RESULT: [NodeResult(
                    execute_node_name=NodeName.JUST_TALK.value,
                    execute_result_code=1,
                    execute_result_msg="生成回复失败",
                    execute_exceptions=[f"生成回复失败: {e}"]
                )]
            }

        # 返回成功结果
        return {
            SubTalkStateField.TASK_RESULT: TaskResult(
                task_result=generated_just_talk_output.just_talk_output,  # LLM生成的回复内容
                task_result_explain=f"生成回复成功",
                task_result_code=0
            ),
            SubTalkStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.JUST_TALK.value,
                execute_result_code=0,
                execute_result_msg="生成回复成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理异常情况
        logger.error(f"生成回复失败: {e}")
        return {
            SubTalkStateField.TASK_RESULT: TaskResult(
                task_result="抱歉，我好像有故障，无法回答你的问题",
                task_result_explain="解析失败",
                task_result_code=1
            ),
            SubTalkStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.JUST_TALK.value,
                execute_result_code=1,
                execute_result_msg="解析失败",
                execute_exceptions=[f"解析结果失败: {e}"]
            )]  
        }

"""构建闲聊子图

使用StateGraph创建子图，定义状态模式、输入模式、输出模式和配置模式。
该子图是最简单的子图，仅包含两个节点。
"""
builder = StateGraph(
    state_schema=SubTalkState,      # 子图完整状态结构
    input_schema=SubTalkInputState, # 输入数据结构
    output_schema=SubTalkOutputState, # 输出数据结构
    config_schema=SagtConfig       # 配置结构（user_id, external_id）
)

"""注册子图节点

将各个节点函数注册到状态图中。
"""
builder.add_node(NodeName.WELCOME_MESSAGE.value, welcome_message_node)  # 欢迎消息节点
builder.add_node(NodeName.JUST_TALK.value, just_talk_node)              # 闲聊回复节点

"""定义子图流程（边的连接）

定义节点之间的执行顺序和流转关系。
"""
# 开始 → 欢迎消息节点
builder.add_edge(START, NodeName.WELCOME_MESSAGE.value)
# 欢迎消息 → 闲聊回复节点
builder.add_edge(NodeName.WELCOME_MESSAGE.value, NodeName.JUST_TALK.value)
# 闲聊回复 → 结束节点
builder.add_edge(NodeName.JUST_TALK.value, END)

"""编译子图

将状态图编译为可执行的图实例，供主图调用。
"""
sub_talk_graph = builder.compile()