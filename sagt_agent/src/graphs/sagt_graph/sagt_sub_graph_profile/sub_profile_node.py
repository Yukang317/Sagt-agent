"""客户画像子图节点定义文件

本文件定义了客户画像子图的所有节点实现，包括：
- 欢迎消息节点：向用户发送开始提示
- 生成客户画像节点：调用LLM生成新的客户画像
- 人工反馈节点：等待用户确认、放弃或重新生成
- 更新客户画像节点：将确认后的画像保存到存储
- 通知节点：通过企业微信发送通知

业务流程：生成画像 → 通知用户 → 等待确认 → 更新存储（或放弃/重新生成）
"""

# 导入JSON处理模块
import json
# 导入枚举模块
from enum import Enum
# 导入类型定义模块
from typing_extensions import Literal
# 导入配置字段定义
from graphs.sagt_graph.sagt_state import ConfigurableField
# 导入LangGraph中断和命令类型
from langgraph.types import interrupt, Command
# 导入LangGraph结束节点
from langgraph.graph import END
# 导入日志工具
from utils.agent_logger import get_logger
# 导入LLM模型实例
from llm.llm_setting import chat_model as llm
# 导入画像建议生成函数
from llm.llm_suggest_profile import llm_profile_suggest
# 导入企业微信API
from tools.wechat_tool import WxWorkAPI
# 导入业务模型类
from models.sagt_models import (
    CustomerProfile,    # 客户画像模型
    NodeResult,         # 节点执行结果模型
    ChatHistory,        # 聊天历史模型
    KFChatHistory,      # 客服聊天历史模型
    OrderHistory,       # 订单历史模型
    CustomerTags        # 客户标签模型
)
# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_profile.sub_profile_state import (
    SubProfileState,       # 子图状态类型
    SubProfileStateField,  # 子图状态字段枚举
    TaskResult             # 任务结果模型
)
# 导入LangChain可运行配置
from langchain_core.runnables import RunnableConfig
# 导入存储工具函数（使用别名避免与函数名冲突）
from tools.store_tool import update_customer_profile as update_customer_profile_tool

# 获取子图节点模块的日志实例
logger = get_logger("sub_profile_node")


class HumanFeedback(str, Enum):
    """
    人工反馈类型枚举
    
    定义了用户对生成的客户画像可能的反馈操作：
    - OK: 确认接受新画像
    - DISCARD: 放弃新画像，不更新
    - RECREATE: 重新生成画像
    - FIELD_NAME: 反馈字段名称（用于解析用户输入）
    """
    OK          = "ok"       # 确认
    DISCARD     = "discard"  # 放弃
    RECREATE    = "recreate" # 重新生成
    FIELD_NAME  = "confirmed" # 反馈字段名

class NodeName(str, Enum):
    """
    客户画像子图节点名称枚举
    
    定义了子图中所有节点的唯一标识符：
    - WELCOME_MESSAGE: 欢迎消息节点
    - PROFILE_SUGGEST: 生成画像建议节点
    - PROFILE_UPDATE: 更新画像节点
    - PROFILE_FEEDBACK: 人工反馈节点
    - PROFILE_NOTIFY_FEEDBACK: 通知用户确认节点
    - PROFILE_NOTIFY_RESULT: 通知任务结果节点
    """
    WELCOME_MESSAGE         = "profile_welcome_node"          # 欢迎消息节点
    PROFILE_SUGGEST         = "profile_suggest_node"          # 生成画像建议节点
    PROFILE_UPDATE          = "profile_update_node"           # 更新画像节点
    PROFILE_FEEDBACK        = "profile_feedback_node"         # 人工反馈节点
    PROFILE_NOTIFY_FEEDBACK = "profile_notify_feedback_node"  # 通知确认节点
    PROFILE_NOTIFY_RESULT   = "profile_notify_result_node"    # 通知结果节点


def welcome_message(state: SubProfileState, config: RunnableConfig):
    """
    欢迎消息节点
    
    子图执行的第一个节点，向用户发送任务开始提示消息，
    告知用户系统正在生成客户画像。
    
    Args:
        state: 当前子图状态
        config: 运行配置
        
    Returns:
        状态更新字典，包含节点执行结果
    """
    logger.info("=== 欢迎消息 ===")

    return {
        SubProfileStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.WELCOME_MESSAGE.value,  # 节点名称
            execute_result_code=0,                             # 成功码
            execute_result_msg="正在生成客户画像，请稍等...",    # 提示消息
            execute_exceptions=[]                              # 无异常
        )]
    }


def generate_customer_profile(state: SubProfileState, config: RunnableConfig):
    """
    生成客户画像节点（核心业务节点）
    
    调用LLM分析多维度数据，生成客户的360度画像。
    输入数据包括：聊天历史、客服记录、订单历史、客户标签、现有画像。
    
    Args:
        state: 当前子图状态，包含输入数据
        config: 运行配置
        
    Returns:
        状态更新字典，包含生成的画像建议、通知内容和任务结果
    """
    logger.info("=== 生成客户profile ===")

    try:
        # 调用LLM生成画像建议
        # 传入多维度数据供LLM分析
        generated_profile: CustomerProfile = llm_profile_suggest(
            chat_history=state.get(SubProfileStateField.CHAT_HISTORY, ChatHistory()),       # 销售聊天历史
            kf_chat_history=state.get(SubProfileStateField.KF_CHAT_HISTORY, KFChatHistory()), # 客服聊天历史
            order_history=state.get(SubProfileStateField.ORDER_HISTORY, OrderHistory()),     # 订单历史
            customer_tags=state.get(SubProfileStateField.CUSTOMER_TAGS, CustomerTags()),     # 客户标签
            customer_profile=state.get(SubProfileStateField.CUSTOMER_PROFILE, CustomerProfile()) # 现有画像
        )
        
        logger.info(f"generated_profile: {generated_profile}")
        
        # 返回成功结果
        return {
            SubProfileStateField.SUGGESTION_PROFILE: generated_profile,  # 存储生成的画像建议
            SubProfileStateField.NOTIFY_CONTENT: f"您好，我为您的客户生成了新的Profile，需要您的确认：\n{generated_profile.model_dump_json()}",  # 通知内容
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"生成客户profile成功：\n{generated_profile.model_dump_json()}",
                task_result_explain=f"生成客户profile成功",
                task_result_code=0
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_SUGGEST.value,
                execute_result_code=0,
                execute_result_msg="生成客户profile成功，等待人工确认",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理异常情况
        logger.error(f"生成客户profile失败: {e}")
        return {
            SubProfileStateField.SUGGESTION_PROFILE: CustomerProfile(),  # 返回空画像
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"很抱歉，生成客户profile时，发生了错误",
                task_result_explain=f"生成客户profile失败",
                task_result_code=1
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_SUGGEST.value,
                execute_result_code=1,
                execute_result_msg="生成客户profile失败",
                execute_exceptions=[str(e)]
            )]
        }

def notify_human_feedback(state: SubProfileState, config: RunnableConfig):
    """
    发送人工确认通知节点
    
    通过企业微信向用户发送画像生成完成的通知，
    提醒用户需要确认新生成的客户画像。
    
    Args:
        state: 当前子图状态
        config: 运行配置
    """
    logger.info("=== 发送人工确认通知 ===")
    _notify_human(state, config, NodeName.PROFILE_NOTIFY_FEEDBACK)

def notify_human_result(state: SubProfileState, config: RunnableConfig):
    """
    发送任务结果通知节点
    
    通过企业微信向用户发送任务最终结果通知，
    告知用户画像更新是否成功。
    
    Args:
        state: 当前子图状态
        config: 运行配置
    """
    logger.info("=== 发送任务结果通知 ===")
    _notify_human(state, config, NodeName.PROFILE_NOTIFY_RESULT)

def _notify_human(state: SubProfileState, config: RunnableConfig, node_name: NodeName):
    """
    通用通知函数（内部函数）
    
    通过企业微信API向指定用户发送通知消息。
    这是一个通用函数，被notify_human_feedback和notify_human_result调用。
    
    Args:
        state: 当前子图状态
        config: 运行配置
        node_name: 调用此函数的节点名称
        
    Returns:
        状态更新字典，包含通知发送结果
    """
    # 创建企业微信API实例
    wxwork_api = WxWorkAPI()

    # 从配置中获取用户ID
    user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    # 从状态中获取通知内容
    content = state.get(SubProfileStateField.NOTIFY_CONTENT, "")

    # 参数校验
    if not user_id or not content:
        return {
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=node_name.value,
                execute_result_code=1,
                execute_result_msg=f"缺少参数，无法发送通知",
                execute_exceptions=[]
            )]
        }
    
    # 调用企业微信API发送通知
    try:
        result = wxwork_api.notify_user(user_id=user_id, content=content)
        logger.info(f"用户通知成功: {result}")
        
        return {
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=node_name.value,
                execute_result_code=0,
                execute_result_msg="通知用户成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        logger.error(f"用户通知失败: {e}")
        return {
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=node_name.value,
                execute_result_code=1,
                execute_result_msg="通知用户失败",
                execute_exceptions=[str(e)]
            )]
        }

def human_feedback(state: SubProfileState, config: RunnableConfig) -> Command[Literal[NodeName.PROFILE_SUGGEST.value, NodeName.PROFILE_UPDATE.value, END]]:
    """
    人工反馈节点（核心交互节点）
    
    使用LangGraph的interrupt机制暂停执行，等待用户反馈。
    用户可以选择：确认(ok)、放弃(discard)、重新生成(recreate)。
    
    期待的反馈格式：
        {"confirmed": "ok"}      - 确认并更新画像
        {"confirmed": "discard"} - 放弃，不更新
        {"confirmed": "recreate"}- 重新生成
        
    Args:
        state: 当前子图状态
        config: 运行配置
        
    Returns:
        Command对象，包含下一步要跳转到的节点
    """
    logger.info("=== 等待人工反馈 ===")

    # 使用interrupt暂停执行，等待用户输入
    human_feedback = interrupt({
        "description": "这是帮您生成的客户Profile，您可以确认、放弃、重新生成。",
        "old_profile": state.get(SubProfileStateField.CUSTOMER_PROFILE, {}),   # 显示原画像供对比
        "new_profile": state.get(SubProfileStateField.SUGGESTION_PROFILE, {})  # 显示新生成的画像
    })

    logger.info(f"用户反馈: {human_feedback}")
    logger.info(f"用户反馈类型: {type(human_feedback)}")
    logger.info(f"用户反馈内容: {json.dumps(human_feedback, ensure_ascii=False)}")

    # 解析用户反馈
    try:
        feedback_dict = human_feedback  # 直接使用，interrupt返回的已是字典
        confirmed = feedback_dict.get(HumanFeedback.FIELD_NAME, "")
        logger.info(f"用户反馈确认值: {confirmed}")
    except (json.JSONDecodeError, AttributeError) as e:
        # 解析失败处理
        logger.error(f"解析human_feedback失败: {e}")
        execute_result = {
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"解析human_feedback失败",
                task_result_explain=f"解析human_feedback失败",
                task_result_code=1
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_FEEDBACK.value,
                execute_result_code=1,
                execute_result_msg=f"解析human_feedback失败",
                execute_exceptions=[str(e)]
            )]
        }
        return Command(goto=END, update=execute_result)

    # 根据用户反馈进行路由
    if confirmed == HumanFeedback.OK:
        # 用户确认，跳转到更新节点
        logger.info("用户已确认结果符合要求")
        execute_result = {
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_FEEDBACK.value,
                execute_result_code=0,
                execute_result_msg=f"用户已确认结果，生成的Profile符合要求",
                execute_exceptions=[]
            )]
        }
        return Command(goto=NodeName.PROFILE_UPDATE.value, update=execute_result)
    
    if confirmed == HumanFeedback.DISCARD:
        # 用户放弃，结束流程
        logger.info("用户放弃结果")
        execute_result = {
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"用户放弃结果，生成的Profile不符合要求",
                task_result_explain=f"用户放弃结果，生成的Profile不符合要求",
                task_result_code=1
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_FEEDBACK.value,
                execute_result_code=0,
                execute_result_msg=f"用户放弃结果，生成的Profile不符合要求",
                execute_exceptions=[]
            )]
        }
        return Command(goto=END, update=execute_result)
    
    if confirmed == HumanFeedback.RECREATE:
        # 用户要求重新生成，跳回生成节点
        logger.info("用户需要重新生成")
        execute_result = {
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"用户需要重新生成Profile",
                task_result_explain=f"用户需要重新生成Profile",
                task_result_code=1
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_FEEDBACK.value,
                execute_result_code=0,
                execute_result_msg=f"用户需要重新生成Profile",
                execute_exceptions=[]
            )]
        }
        return Command(goto=NodeName.PROFILE_SUGGEST.value, update=execute_result)
    
    # 未知反馈，结束流程
    logger.info("指令异常，系统自动结束")
    execute_result = {
        SubProfileStateField.TASK_RESULT: TaskResult(
            task_result=f"指令异常，系统自动结束",
            task_result_explain=f"指令异常，系统自动结束",
            task_result_code=1
        ),
        SubProfileStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.PROFILE_FEEDBACK.value,
            execute_result_code=0,
            execute_result_msg=f"指令异常，系统自动结束",
            execute_exceptions=[]
        )]
    }
    return Command(goto=END, update=execute_result)


def update_customer_profile(state: SubProfileState, config: RunnableConfig):
    """
    更新客户画像节点
    
    将用户确认后的新画像保存到数据存储中。
    只有在用户确认(ok)且生成成功的情况下才执行更新。
    
    Args:
        state: 当前子图状态，包含生成的画像建议
        config: 运行配置，包含用户ID和外部ID
        
    Returns:
        状态更新字典，包含更新结果
    """
    logger.info("=== 更新客户profile ===")

    # 获取必要参数
    follow_user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    external_id = config[ConfigurableField.configurable][ConfigurableField.external_id]
    task_result = state.get(SubProfileStateField.TASK_RESULT, TaskResult())
    task_result_code = task_result.task_result_code

    # 参数校验
    if not external_id or not follow_user_id or task_result_code != 0:
        return {
            SubProfileStateField.NOTIFY_CONTENT: f"缺少参数或任务结果不成功，无法更新客户profile",
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"缺少参数或任务结果不成功，无法更新客户profile",
                task_result_explain=f"缺少参数或任务结果不成功，无法更新客户profile",
                task_result_code=1
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_UPDATE.value,
                execute_result_code=task_result_code,
                execute_result_msg=f"缺少参数或任务结果不成功，无法更新客户profile",
                execute_exceptions=[]
            )]
        }

    # 调用存储工具更新画像
    try:
        # 获取生成的画像建议
        profile = state.get(SubProfileStateField.SUGGESTION_PROFILE, CustomerProfile())
        # 调用工具函数保存到存储
        update_customer_profile_tool(
            external_id=external_id, 
            follow_user_id=follow_user_id, 
            profile=profile
        )
        logger.info(f"客户profile更新成功")
        
        # 返回成功结果
        return {
            SubProfileStateField.NOTIFY_CONTENT: f"更新客户profile成功：\n{profile.model_dump_json()}",
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"更新客户profile成功：\n{profile.model_dump_json()}",
                task_result_explain=f"更新客户profile成功",
                task_result_code=0
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_UPDATE.value,
                execute_result_code=0,
                execute_result_msg=f"更新客户profile成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理更新失败
        logger.error(f"更新客户profile失败: {e}")
        return {
            SubProfileStateField.NOTIFY_CONTENT: f"更新客户profile失败：\n{str(e)}",
            SubProfileStateField.TASK_RESULT: TaskResult(
                task_result=f"更新客户profile失败：\n{str(e)}",
                task_result_explain=f"更新客户profile失败",
                task_result_code=1
            ),
            SubProfileStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.PROFILE_UPDATE.value,
                execute_result_code=1,
                execute_result_msg=f"更新客户profile失败",
                execute_exceptions=[str(e)]
            )] 
        }



