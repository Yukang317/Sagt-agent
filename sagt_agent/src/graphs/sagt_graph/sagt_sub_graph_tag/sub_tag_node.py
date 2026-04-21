"""客户标签子图节点定义文件

本文件定义了客户标签子图的所有节点实现，包括：
- 欢迎消息节点：向用户发送开始提示
- 生成标签建议节点：调用LLM生成标签变更建议
- 人工反馈节点：等待用户确认、放弃或重新生成
- 更新客户标签节点：将确认后的标签保存到存储
- 通知节点：通过企业微信发送通知

业务流程：生成标签建议 → 通知用户 → 等待确认 → 更新存储（或放弃/重新生成）
"""

# 导入类型定义模块
from typing_extensions import Literal
# 导入LangGraph中断和命令类型
from langgraph.types import interrupt, Command
# 导入LangGraph结束节点
from langgraph.graph import END
# 导入LangChain可运行配置
from langchain_core.runnables import RunnableConfig
# 导入企业微信API
from tools.wechat_tool import WxWorkAPI
# 导入业务模型类
from models.sagt_models import (
    TagSuggestion,      # 标签建议模型
    TaskResult,         # 任务结果模型
    NodeResult,         # 节点执行结果模型
    TagSetting,         # 标签设置模型
    CustomerTags,       # 客户标签模型
    ChatHistory,        # 聊天历史模型
    KFChatHistory,      # 客服聊天历史模型
    OrderHistory        # 订单历史模型
)
# 导入配置字段定义
from graphs.sagt_graph.sagt_state import ConfigurableField
# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_tag.sub_tag_state import (
    SubTagState,       # 子图状态类型
    SubTagStateField   # 子图状态字段枚举
)
# 导入日志工具
from utils.agent_logger import get_logger
# 导入标签建议生成函数
from llm.llm_suggest_tag import llm_tag_suggest
# 导入存储工具函数（使用别名避免与函数名冲突）
from tools.store_tool import update_customer_tags as update_customer_tags_tool

# 导入JSON处理模块
import json
# 导入枚举模块
from enum import Enum
# 导入日期时间模块
from datetime import datetime

# 获取子图节点模块的日志实例
logger = get_logger("sub_tag_node")


class HumanFeedback(str, Enum):
    """
    人工反馈类型枚举
    
    定义了用户对生成的标签建议可能的反馈操作：
    - OK: 确认接受标签建议
    - DISCARD: 放弃标签建议，不更新
    - RECREATE: 重新生成标签建议
    - FIELD_NAME: 反馈字段名称（用于解析用户输入）
    """
    OK          = "ok"       # 确认
    DISCARD     = "discard"  # 放弃
    RECREATE    = "recreate" # 重新生成
    FIELD_NAME  = "confirmed" # 反馈字段名

class NodeName(str, Enum):
    """
    客户标签子图节点名称枚举
    
    定义了子图中所有节点的唯一标识符：
    - WELCOME_MESSAGE: 欢迎消息节点
    - GENERATE_TAG: 生成标签建议节点
    - HUMAN_FEEDBACK: 人工反馈节点
    - UPDATE_TAG: 更新标签节点
    - NOTIFY_FEEDBACK: 通知用户确认节点
    - NOTIFY_RESULT: 通知任务结果节点
    """
    WELCOME_MESSAGE = "tag_welcome_node"      # 欢迎消息节点
    GENERATE_TAG    = "tag_generate_node"     # 生成标签建议节点
    HUMAN_FEEDBACK  = "tag_human_feedback_node" # 人工反馈节点
    UPDATE_TAG      = "tag_update_node"      # 更新标签节点
    NOTIFY_FEEDBACK = "tag_notify_feedback_node" # 通知确认节点
    NOTIFY_RESULT   = "tag_notify_result_node"   # 通知结果节点

def welcome_message_node(state: SubTagState, config: RunnableConfig):
    """
    欢迎消息节点
    
    子图执行的第一个节点，向用户发送任务开始提示消息，
    告知用户系统正在生成客户标签建议。
    
    Args:
        state: 当前子图状态
        config: 运行配置
        
    Returns:
        状态更新字典，包含节点执行结果
    """
    logger.info("=== 欢迎消息 ===")
    
    return {
        SubTagStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.WELCOME_MESSAGE.value,  # 节点名称
            execute_result_code=0,                             # 成功码
            execute_result_msg="正在为您生成客户标签建议，请稍等。", # 提示消息
            execute_exceptions=[]                              # 无异常
        )]
    }

def generate_customer_tag(state: SubTagState, config: RunnableConfig):
    """
    生成客户标签建议节点（核心业务节点）
    
    调用LLM分析多维度数据，生成客户标签的添加和删除建议。
    输入数据包括：标签设置、客户现有标签、聊天历史、客服记录、订单历史。
    
    Args:
        state: 当前子图状态，包含输入数据
        config: 运行配置
        
    Returns:
        状态更新字典，包含生成的标签建议、通知内容和任务结果
    """
    logger.info("=== 生成客户标签建议 ===")

    try:
        # 调用LLM生成标签建议
        # 传入多维度数据供LLM分析
        generated_tag_suggestion = llm_tag_suggest(
            tag_setting=state.get(SubTagStateField.TAG_SETTING, TagSetting()),      # 系统标签配置
            customer_tags=state.get(SubTagStateField.CUSTOMER_TAGS, CustomerTags()), # 客户现有标签
            chat_history=state.get(SubTagStateField.CHAT_HISTORY, ChatHistory()),   # 销售聊天历史
            kf_chat_history=state.get(SubTagStateField.KF_CHAT_HISTORY, KFChatHistory()), # 客服聊天历史
            order_history=state.get(SubTagStateField.ORDER_HISTORY, OrderHistory()), # 订单历史
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),              # 当前时间
        )
        
        # 返回成功结果
        return {
            SubTagStateField.SUGGESTION_TAG: generated_tag_suggestion,  # 存储生成的标签建议
            SubTagStateField.NOTIFY_CONTENT: f"您好，我为您的客户生成了新的标签建议，需要您的确认：\n{generated_tag_suggestion.model_dump_json()}",  # 通知内容
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"生成客户标签建议成功：\n{generated_tag_suggestion.model_dump_json()}",
                task_result_explain=f"生成客户标签建议成功",
                task_result_code=0
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.GENERATE_TAG.value,
                execute_result_code=0,
                execute_result_msg="生成客户标签建议成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        # 处理异常情况
        logger.error(f"生成客户标签建议失败: {e}")
        return {
            SubTagStateField.SUGGESTION_TAG: TagSuggestion(),  # 返回空标签建议
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"生成客户标签建议失败",
                task_result_explain=f"生成客户标签建议失败",
                task_result_code=1
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.GENERATE_TAG.value,
                execute_result_code=1,
                execute_result_msg=f"生成客户标签建议失败: {e}",
                execute_exceptions=[str(e)]
            )]
        }

def notify_human_feedback(state: SubTagState, config: RunnableConfig):
    """
    发送人工确认通知节点
    
    通过企业微信向用户发送标签建议生成完成的通知，
    提醒用户需要确认新生成的标签建议。
    
    Args:
        state: 当前子图状态
        config: 运行配置
    """
    logger.info("=== 发送人工确认通知 ===")
    _notify_human(state, config, NodeName.NOTIFY_FEEDBACK)

def notify_human_result(state: SubTagState, config: RunnableConfig):
    """
    发送任务结果通知节点
    
    通过企业微信向用户发送任务最终结果通知，
    告知用户标签更新是否成功。
    
    Args:
        state: 当前子图状态
        config: 运行配置
    """
    logger.info("=== 发送任务结果通知 ===")
    _notify_human(state, config, NodeName.NOTIFY_RESULT)

def _notify_human(state: SubTagState, config: RunnableConfig, node_name: NodeName):
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
    content = state.get(SubTagStateField.NOTIFY_CONTENT, "")

    # 参数校验
    if not user_id or not content:
        return {
            SubTagStateField.NODE_RESULT: [NodeResult(
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
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=node_name.value,
                execute_result_code=0,
                execute_result_msg="通知用户成功",
                execute_exceptions=[]
            )]
        }
    except Exception as e:
        logger.error(f"用户通知失败: {e}")
        return {
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=node_name.value,
                execute_result_code=1,
                execute_result_msg="通知用户失败",
                execute_exceptions=[str(e)]
            )]
        }
    
def human_feedback(state: SubTagState, config: RunnableConfig) -> Command[Literal[NodeName.GENERATE_TAG.value, NodeName.UPDATE_TAG.value, END]]:
    """
    人工反馈节点（核心交互节点）
    
    使用LangGraph的interrupt机制暂停执行，等待用户反馈。
    用户可以选择：确认(ok)、放弃(discard)、重新生成(recreate)。
    
    期待的反馈格式：
        {"confirmed": "ok"}      - 确认并更新标签
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
        "description": "这是帮您生成的客户标签建议，您可以确认、放弃、重新生成。",
        "old_tags": state.get(SubTagStateField.CUSTOMER_TAGS, {}),   # 显示原标签供对比
        "new_tags": state.get(SubTagStateField.SUGGESTION_TAG, {})   # 显示新生成的标签建议
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
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"解析human_feedback失败",
                task_result_explain=f"解析human_feedback失败",
                task_result_code=1
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.HUMAN_FEEDBACK.value,
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
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.HUMAN_FEEDBACK.value,
                execute_result_code=0,
                execute_result_msg=f"用户已确认结果符合要求",
                execute_exceptions=[]
            )]
        }
        return Command(goto=NodeName.UPDATE_TAG.value, update=execute_result)
    
    if confirmed == HumanFeedback.DISCARD:
        # 用户放弃，结束流程
        logger.info("用户放弃结果")
        execute_result = {
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"用户放弃结果",
                task_result_explain=f"用户放弃结果",
                task_result_code=1
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.HUMAN_FEEDBACK.value,
                execute_result_code=0,
                execute_result_msg=f"用户放弃结果",
                execute_exceptions=[]
            )]
        }
        return Command(goto=END, update=execute_result)
    
    if confirmed == HumanFeedback.RECREATE:
        # 用户要求重新生成，跳回生成节点
        logger.info("用户需要重新生成")
        execute_result = {
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"用户需要重新生成",
                task_result_explain=f"用户需要重新生成",
                task_result_code=1
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.HUMAN_FEEDBACK.value,
                execute_result_code=0,
                execute_result_msg=f"用户需要重新生成",
                execute_exceptions=[]
            )]
        }
        return Command(goto=NodeName.GENERATE_TAG.value, update=execute_result)
    
    # 未知反馈，结束流程
    logger.info("指令异常，系统自动结束")
    execute_result = {
        SubTagStateField.TASK_RESULT: TaskResult(
            task_result=f"指令异常，系统自动结束",
            task_result_explain=f"指令异常，系统自动结束",
            task_result_code=1
        ),
        SubTagStateField.NODE_RESULT: [NodeResult(
            execute_node_name=NodeName.HUMAN_FEEDBACK.value,
            execute_result_code=0,
            execute_result_msg=f"指令异常，系统自动结束",
            execute_exceptions=[]
        )]
    }
    return Command(goto=END, update=execute_result)


def update_customer_tag(state: SubTagState, config: RunnableConfig):
    """
    更新客户标签节点
    
    将用户确认后的标签建议保存到数据存储中。
    从标签建议中提取需要添加和删除的标签ID，调用存储工具进行更新。
    
    注意：开发环境中不更新企业微信的用户标签（需要同一个自建应用创建的标签才能更新），
    而是使用SAGT自有的长期记忆模式存储用户标签。
    
    Args:
        state: 当前子图状态，包含生成的标签建议
        config: 运行配置，包含用户ID和外部ID
        
    Returns:
        状态更新字典，包含更新结果
    """
    logger.info("=== 更新客户标签 ===")

    # 获取必要参数
    user_id = config[ConfigurableField.configurable][ConfigurableField.user_id]
    external_id = config[ConfigurableField.configurable][ConfigurableField.external_id]
 
    # 调用存储工具更新标签
    try:
        # 获取生成的标签建议
        tag_suggestion = state.get(SubTagStateField.SUGGESTION_TAG, TagSuggestion())
        tags_add = tag_suggestion.tag_ids_add      # 建议添加的标签
        tags_remove = tag_suggestion.tag_ids_remove # 建议删除的标签

        # 提取标签ID列表（过滤空ID）
        tag_ids_add = [tag.tag_id for tag in tags_add if tag.tag_id]
        tag_ids_remove = [tag.tag_id for tag in tags_remove if tag.tag_id]

        # 检查是否有需要更新的标签
        if len(tag_ids_add) == 0 and len(tag_ids_remove) == 0:
            logger.info("没有需要更新的标签")
            return {
                SubTagStateField.NOTIFY_CONTENT: f"您好，没有需要更新的标签，任务结束", 
                SubTagStateField.TASK_RESULT: TaskResult(
                    task_result=f"没有需要更新的标签",
                    task_result_explain=f"没有需要更新的标签",
                    task_result_code=0
                ),
                SubTagStateField.NODE_RESULT: [NodeResult(
                    execute_node_name=NodeName.UPDATE_TAG.value,
                    execute_result_code=0,
                    execute_result_msg="没有需要更新的标签，任务结束",
                    execute_exceptions=[]
                )]
            }

        # 调用SAGT自有的长期记忆模式存储用户标签
        # 参数：external_id(客户外部ID), follow_user_id(跟进人ID), tag_ids_add(添加的标签ID), tag_ids_remove(删除的标签ID)
        update_customer_tags_tool(
            external_id=external_id, 
            follow_user_id=user_id, 
            tag_ids_add=tag_ids_add, 
            tag_ids_remove=tag_ids_remove
        )

        logger.info(f"客户标签更新成功")
        
        # 返回成功结果
        return {
            SubTagStateField.NOTIFY_CONTENT: f"您好，我已为您更新客户标签，更新结果如下：\n{tag_suggestion.model_dump_json()}",
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"更新客户标签成功：\n{tag_suggestion.model_dump_json()}",
                task_result_explain=f"更新客户标签成功",
                task_result_code=0
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.UPDATE_TAG.value,
                execute_result_code=0,
                execute_result_msg="更新客户标签成功",
                execute_exceptions=[]
            )]  
        }
    except Exception as e:
        # 处理更新失败
        logger.error(f"更新客户标签失败: {e}")
        return {
            SubTagStateField.NOTIFY_CONTENT: f"很抱歉，更新客户标签时，发生了错误：\n{str(e)}",
            SubTagStateField.TASK_RESULT: TaskResult(
                task_result=f"更新客户标签失败",
                task_result_explain=f"更新客户标签失败",
                task_result_code=1
            ),
            SubTagStateField.NODE_RESULT: [NodeResult(
                execute_node_name=NodeName.UPDATE_TAG.value,
                execute_result_code=1,
                execute_result_msg=f"更新客户标签失败: {e}",
                execute_exceptions=[str(e)]
            )]
        }