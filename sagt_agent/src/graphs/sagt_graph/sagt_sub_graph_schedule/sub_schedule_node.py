"""客户日程子图节点定义文件

本文件定义了客户日程子图的所有节点实现，包括：
- 欢迎消息节点：向用户发送开始提示
- 生成日程建议节点：调用LLM生成日程安排建议
- 创建日程节点：调用企业微信API创建日程

业务流程：发送欢迎消息 → 生成日程建议 → 创建到企业微信日历 → 返回结果

业务背景：该子图为销售人员提供智能日程安排建议，
基于聊天历史分析客户需求，自动生成跟进日程并创建到企业微信日历。

核心特点：
- 与企业微信日历深度集成
- 生成建议后自动创建，无需人工确认
- 提高销售人员工作效率
"""

# 导入LangChain可运行配置
from langchain_core.runnables import RunnableConfig
# 导入日程建议生成函数
from llm.llm_suggest_schedule import llm_schedule_suggest
# 导入企业微信API
from tools.wechat_tool import WxWorkAPI
# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_schedule.sub_schedule_state import SubScheduleState, SubScheduleStateField
# 导入日志工具
from utils.agent_logger import get_logger
# 导入配置字段定义
from graphs.sagt_graph.sagt_state import ConfigurableField
# 导入日期时间模块
from datetime import datetime
# 导入枚举模块
from enum import Enum
# 导入业务模型类
from models.sagt_models import (
    CustomerInfo,       # 客户信息模型
    ChatHistory,        # 聊天历史模型
    ScheduleSuggestion, # 日程建议模型
    TaskResult,         # 任务结果模型
    NodeResult          # 节点执行结果模型
)

# 获取子图节点模块的日志实例
logger = get_logger("sub_schedule_node")


class NodeName(str, Enum):
    """
    客户日程子图节点名称枚举
    
    定义了子图中所有节点的唯一标识符：
    - WELCOME_MESSAGE: 欢迎消息节点
    - GENERATE_SCHEDULE: 生成日程建议节点
    - CREATE_SCHEDULE: 创建日程节点
    """
    WELCOME_MESSAGE   = "schedule_welcome_node"   # 欢迎消息节点
    GENERATE_SCHEDULE = "schedule_generate_node"  # 生成日程建议节点
    CREATE_SCHEDULE   = "schedule_create_node"    # 创建日程节点

def welcome_message_node(state: SubScheduleState, config: RunnableConfig):
    """
    欢迎消息节点
    
    子图执行的第一个节点，向用户发送任务开始提示消息，
    告知用户系统正在生成日程建议。
    
    Args:
        state: 当前子图状态
        config: 运行配置
        
    Returns:
        状态更新字典，包含节点执行结果
    """
    logger.info("=== 欢迎消息 ===")
    
    return {
        SubScheduleStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.WELCOME_MESSAGE.value,  # 节点名称
            execute_result_code=0,                             # 成功码
            execute_result_msg="正在为您生成日程建议，请稍等。", # 提示消息
            execute_exceptions=[]                              # 无异常
        )]
    }


def generate_schedule_node(state: SubScheduleState, config: RunnableConfig):
    """
    生成日程建议节点（核心业务节点）
    
    调用LLM分析聊天历史上下文和客户信息，生成合适的日程安排建议。
    输入数据包括：客户信息、聊天历史、当前时间。
    
    业务逻辑：
    1. 从状态中获取输入数据（客户信息、聊天历史）
    2. 调用LLM生成日程建议（包含标题、时间、时长）
    3. 将建议保存到状态，供后续节点使用
    
    Args:
        state: 当前子图状态，包含输入数据
        config: 运行配置
        
    Returns:
        状态更新字典，包含生成的日程建议、任务结果和节点执行结果
    """
    logger.info("=== 生成日程 ===")

    try:
        # 调用LLM生成日程建议
        # 传入客户信息和聊天历史供LLM分析
        generated_schedule_suggestion = llm_schedule_suggest(
            customer_info=state.get(SubScheduleStateField.CUSTOMER_INFO, CustomerInfo()),  # 客户信息
            chat_history=state.get(SubScheduleStateField.CHAT_HISTORY, ChatHistory()),    # 聊天历史
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")                     # 当前时间
        )
        logger.info(f"generated_schedule_suggestion: {generated_schedule_suggestion}")

        # 返回成功结果
        return {
            SubScheduleStateField.SUGGESTION_SCHEDULE: generated_schedule_suggestion,  # 存储生成的日程建议
            SubScheduleStateField.TASK_RESULT: TaskResult(
                task_result=f"生成日程建议成功：\n{generated_schedule_suggestion.model_dump_json()}",
                task_result_explain=f"生成日程建议成功",
                task_result_code=0
            ),
            SubScheduleStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.GENERATE_SCHEDULE.value,
                execute_result_code=0,
                execute_result_msg="生成日程建议成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理异常情况
        logger.error(f"生成日程建议失败: {e}")
        return {
            SubScheduleStateField.SUGGESTION_SCHEDULE: ScheduleSuggestion(),  # 返回空日程建议
            SubScheduleStateField.TASK_RESULT: TaskResult(
                task_result=f"生成日程建议失败",
                task_result_explain=f"生成日程建议失败",
                task_result_code=1
            ),
            SubScheduleStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.GENERATE_SCHEDULE.value,
                execute_result_code=1,
                execute_result_msg=f"生成日程建议失败: {e}",
                execute_exceptions=[str(e)]
            )]
        }


def create_schedule_node(state: SubScheduleState, config: RunnableConfig):
    """
    创建日程节点（企业微信集成节点）
    
    将AI生成的日程建议创建到企业微信日历中。
    通过调用企业微信API，为当前用户创建日程安排。
    
    业务逻辑：
    1. 从状态中获取生成的日程建议
    2. 提取日程标题、开始时间、持续时间
    3. 参数校验（标题和时间不能为空）
    4. 调用企业微信API创建日程
    5. 返回创建结果
    
    Args:
        state: 当前子图状态，包含日程建议
        config: 运行配置，包含用户ID
        
    Returns:
        状态更新字典，包含任务结果和节点执行结果
    """
    logger.info("=== 创建日程 ===")

    # 创建企业微信API实例
    wxwork_api = WxWorkAPI()

    # 从配置中获取当前用户ID
    user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]

    # 创建企业微信日程
    try:
        # 获取生成的日程建议
        schedule = state.get(SubScheduleStateField.SUGGESTION_SCHEDULE, ScheduleSuggestion())
        logger.info(f"schedule: {schedule.model_dump_json()}")

        # 提取日程信息
        title = schedule.title        # 日程标题
        start = schedule.start_time   # 开始时间（格式：yyyy-MM-dd HH:mm:ss）
        duration = schedule.duration  # 持续时间（分钟）

        logger.info(f"title: {title}")
        logger.info(f"start: {start}")
        logger.info(f"duration: {duration}")

        # 参数校验：标题和时间不能为空
        if not title or not start:
            return {
                SubScheduleStateField.TASK_RESULT: TaskResult(
                    task_result=f"日程标题或开始时间不能为空",
                    task_result_explain=f"日程标题或开始时间不能为空",
                    task_result_code=1
                ),
                SubScheduleStateField.NODE_RESULT: [NodeResult(
                    execute_node_name=NodeName.CREATE_SCHEDULE.value,
                    execute_result_code=1,
                    execute_result_msg=f"日程标题或开始时间不能为空",
                    execute_exceptions=[]
                )]
            }

        # **调用企业微信API创建日程**
        result = wxwork_api.create_schedule(user_id=user_id, title=title, start_time=start, duration_minutes=duration)
        logger.info(f"日程创建成功: {result}")
        
        # 返回成功结果
        return {
            SubScheduleStateField.TASK_RESULT: TaskResult(
                task_result=f"创建日程成功",
                task_result_explain=f"创建日程成功",
                task_result_code=0
            ),
            SubScheduleStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.CREATE_SCHEDULE.value,
                execute_result_code=0,
                execute_result_msg=f"创建日程成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理创建失败
        logger.error(f"创建日程失败: {e}")
        return {
            SubScheduleStateField.TASK_RESULT: TaskResult(
                task_result=f"创建日程失败: {e}",
                task_result_explain=f"创建日程失败",
                task_result_code=1
            ),
            SubScheduleStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.CREATE_SCHEDULE.value,
                execute_result_code=1,
                execute_result_msg=f"创建日程失败: {e}",
                execute_exceptions=[str(e)]
            )]
        }

