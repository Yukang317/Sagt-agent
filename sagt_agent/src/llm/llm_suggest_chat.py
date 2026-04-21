"""聊天建议生成LLM模块

本模块负责调用LLM生成销售人员的聊天回复建议（ReplySuggestion）。

业务背景：作为酒类销售助理，根据聊天历史和客户信息，
为销售人员提供合适的回复建议，帮助维护客户关系和促进销售。

核心功能：
1. 分析客户与销售人员的聊天历史
2. 结合客户信息和销售人员信息
3. 生成合适的回复内容和理由
4. 输出结构化的回复建议

数据来源：
- 客户信息（CustomerInfo）：客户基本标识信息
- 员工信息（EmployeeInfo）：销售人员信息
- 聊天历史（ChatHistory）：客户与销售人员的对话记录

输出：
- ReplySuggestion：包含回复内容和回复原因
"""

# 导入业务模型类
from models.sagt_models import (
    ReplySuggestion,   # 回复建议模型
    ChatHistory,       # 聊天历史模型
    CustomerInfo,      # 客户信息模型
    EmployeeInfo       # 员工信息模型
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
logger = get_logger("llm_suggest_chat")

def llm_chat_suggest(
    customer_info: CustomerInfo, 
    employee_info: EmployeeInfo, 
    chat_history: ChatHistory, 
    current_time=None
) -> ReplySuggestion:
    """
    生成销售人员聊天回复建议

    根据聊天历史和客户信息，为销售人员生成合适的回复建议。
    
    处理流程：
    1. 构建提示词（包含角色定义、数据结构、示例、客户数据）
    2. 调用LLM生成回复建议
    3. 解析LLM输出为结构化的ReplySuggestion对象
    4. 返回结果（失败时返回空对象）

    业务特点：
    - 模拟酒类销售助理角色
    - 擅长维护客户关系和促进销售
    - 需理解聊天上下文和时间背景

    Args:
        customer_info: 客户基本信息
        employee_info: 销售人员信息
        chat_history: 聊天历史记录
        current_time: 当前时间（可选，默认使用系统时间）

    Returns:
        ReplySuggestion: 回复建议（包含回复内容和理由）
    """

    # 构建完整的提示词
    prompt = _chat_suggest_instructions.format(
        customer_info=customer_info.model_dump_json(),   # 客户信息
        employee_info=employee_info.model_dump_json(),   # 销售人员信息
        chat_history=chat_history.model_dump_json(),     # 聊天历史
        current_time=current_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 当前时间
        schema_json=ReplySuggestion.get_schema_json(),  # 数据结构定义
        example_json=ReplySuggestion.get_example_json(),# 示例数据
    )

    # 记录调试日志
    logger.debug(f"prompt: {prompt}")

    # 调用LLM生成回复建议
    generated_result: AIMessage = llm.invoke(prompt)
    logger.debug(f"generated_result: {generated_result}")

    # 提取LLM输出内容（处理空结果情况）
    if generated_result and generated_result.content:
        generated_reply_suggestion_json = generated_result.content
    else:
        generated_reply_suggestion_json = "{}"

    # 解析JSON并返回结果
    try:
        # 使用Pydantic验证JSON并转换为模型对象
        generated_reply_suggestion = ReplySuggestion.model_validate_json(generated_reply_suggestion_json)
        logger.info(f"generated_reply_suggestion: {generated_reply_suggestion.model_dump_json()}")
        return generated_reply_suggestion
    except Exception as e:
        # 解析失败时返回空对象
        logger.error(f"生成回复建议失败: {e}")
        return ReplySuggestion()


_chat_suggest_instructions = """
你是出色的酒类销售助理，擅长与客户进行聊天互动。除了销售产品，还特别擅长维护客户关系。

下面是近期与客户的聊天记录，请根据聊天记录，提供合适的回复建议 ReplySuggestion 。


这里是回复建议 ReplySuggestion 的数据结构定义：
-------------------
{schema_json}
-------------------

JSON对象示例：
-------------------
{example_json}
-------------------



【注意】要根据消息中的发送者sender和接收者receiver，分清楚消息是客户发送的还是销售人员发送的。
【注意】要根据消息中的发送时间msg_time，理解所讨论内容的时间背景。



请根据下面的客户信息，生成ReplySuggestion，具体要求：

1、【重要】您必须回复一个有效JSON对象
2、请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
3、json对象结构必须符合ReplySuggestion的定义。
4、请不要在json对象中包含任何未定义的字段。
5、请根据客户信息和聊天记录，生成回复建议。



这里是客户基础信息：
-------------------
{customer_info}
-------------------


这里是销售人员的基本信息：
-------------------
{employee_info}
-------------------


这里是客户和销售人员近期的对话记录：
-------------------
{chat_history}
-------------------




这是当前真实世界的时间，供你参考：
-------------------
{current_time}
-------------------

"""