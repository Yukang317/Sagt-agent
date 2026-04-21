"""日程建议生成LLM模块

本模块负责调用LLM从聊天记录中提取日程安排建议（ScheduleSuggestion）。

业务背景：销售人员在与客户沟通过程中，可能会约定跟进事项或会议，
系统需要自动识别这些日程信息并创建到企业微信日历中。

核心功能：
1. 分析销售聊天历史，提取日程相关信息
2. 识别日程标题、时间、持续时间
3. 如果有多个日程，选择最重要/最紧急的一个
4. 生成结构化的日程建议

数据来源：
- 客户信息（CustomerInfo）：客户基本标识信息
- 聊天历史（ChatHistory）：销售人员与客户的对话记录

输出：
- ScheduleSuggestion：包含日程标题、开始时间、持续时间、建议原因
"""

# 导入业务模型类
from models.sagt_models import (
    ChatHistory,        # 聊天历史模型
    CustomerInfo,       # 客户信息模型
    ScheduleSuggestion  # 日程建议模型
)
# 导入日期时间模块
from datetime import datetime
# 导入初始化好的LLM实例
from llm.llm_setting import chat_model as llm
# 导入LangChain的AIMessage类型
from langchain_core.messages import AIMessage
# 导入日志工具
from utils.agent_logger import get_logger

# 获取本模块的日志实例
logger = get_logger("llm_suggest_schedule")

def llm_schedule_suggest(
    customer_info: CustomerInfo, 
    chat_history: ChatHistory, 
    current_time=None
) -> ScheduleSuggestion:
    """
    从聊天记录中提取日程安排建议

    根据销售聊天历史，分析并提取日程安排信息。
    
    处理流程：
    1. 构建提示词（包含角色定义、数据结构、示例、聊天记录）
    2. 调用LLM分析聊天记录
    3. 提取日程信息（标题、时间、时长）
    4. 返回结构化的日程建议（失败时返回空对象）

    业务规则：
    - 如果没有明确的日程信息，返回空对象
    - 如果有多个日程，选择最重要或最紧急的一个
    - 默认持续时间为30分钟

    Args:
        customer_info: 客户基本信息
        chat_history: 聊天历史记录
        current_time: 当前时间（可选，默认使用系统时间）

    Returns:
        ScheduleSuggestion: 日程安排建议
    """
    
    # 构建完整的提示词
    prompt = _schedule_suggest_instructions.format(
        customer_info=customer_info.model_dump_json(),  # 客户信息
        chat_history=chat_history.model_dump_json(),    # 聊天历史
        current_time=current_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 当前时间
        schema_json=ScheduleSuggestion.get_schema_json(),   # 数据结构定义
        example_json=ScheduleSuggestion.get_example_json(), # 示例数据
    )

    # 记录调试日志
    logger.debug(f"prompt: {prompt}")

    # 调用LLM生成日程建议
    generated_result: AIMessage = llm.invoke(prompt)
    logger.debug(f"generated_result: {generated_result}")

    # 提取LLM输出内容（处理空结果情况）
    if generated_result and generated_result.content:
        generated_schedule_json = generated_result.content
    else:
        generated_schedule_json = "{}"

    # 解析JSON并返回结果
    try:
        # 使用Pydantic验证JSON并转换为模型对象
        generated_schedule = ScheduleSuggestion.model_validate_json(generated_schedule_json)
        logger.info(f"generated_schedule: {generated_schedule.model_dump_json()}")
        return generated_schedule
    except Exception as e:
        # 解析失败时返回空对象
        logger.error(f"生成日程安排建议失败: {e}")
        return ScheduleSuggestion()



_schedule_suggest_instructions = """
你是出色的日程安排助理，擅长对话中获得日程信息。

下面是近期销售人员与客户的聊天记录，请根据聊天记录，提取日程安排建议 ScheduleSuggestion。

【注意】如果没有明确的日程信息，可以不用生成日程建议。
【注意】要根据消息中的发送者sender和接收者receiver，分清楚消息是客户发送的还是销售人员发送的。
【注意】要根据消息中的发送时间msg_time，理解所讨论内容的时间背景，提取出日程的开始时间和持续时间，默认持续时间为30分钟。
【重要】如果对话中包含多个日程安排，请选择最重要或最紧急的一个日程进行建议。

请根据下面的 ScheduleSuggestion 数据结构定义生成 JSON：

数据结构 Schema：
-------------------
{schema_json}
-------------------

JSON 示例：
-------------------
{example_json}
-------------------


请根据下面的客户信息，生成ScheduleSuggestion，具体要求：

1、【重要】您必须回复一个有效JSON对象
2、请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
3、json对象结构必须符合ScheduleSuggestion的定义。
4、请不要在json对象中包含任何未定义的字段。
5、如果对话中包含多个日程安排，请选择最重要或最紧急的一个日程进行建议，不要返回多个日程建议



这里是客户和销售人员近期的对话记录：
-------------------
{chat_history}
-------------------


这里是客户基础信息：
-------------------
{customer_info}
-------------------

这是当前真实世界的时间，供你参考：
-------------------
{current_time}
-------------------



"""
