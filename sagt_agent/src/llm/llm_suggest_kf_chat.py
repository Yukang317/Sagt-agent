"""客服聊天建议生成LLM模块

本模块负责调用LLM生成客服人员的聊天回复建议（ReplySuggestion）。

业务背景：作为企业客服人员，根据客服聊天记录和客户信息，
为客服人员提供合适的回复建议，帮助解答客户咨询。

核心功能：
1. 分析客户与客服的聊天历史
2. 结合客户信息理解客户需求
3. 生成专业的客服回复内容和理由
4. 输出结构化的回复建议

数据来源：
- 客户信息（CustomerInfo）：客户基本标识信息
- 客服聊天历史（KFChatHistory）：客户与客服的对话记录

输出：
- ReplySuggestion：包含回复内容和回复原因

与普通聊天建议的区别：
- 目标用户：客服人员 vs 销售人员
- 聊天场景：客服咨询 vs 销售沟通
- 数据来源：客服聊天历史 vs 销售聊天历史
"""

# 导入业务模型类
from models.sagt_models import (
    ReplySuggestion,   # 回复建议模型
    KFChatHistory,     # 客服聊天历史模型
    CustomerInfo       # 客户信息模型
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
logger = get_logger("llm_suggest_kf_chat")


def llm_kf_chat_suggest(
    customer_info: CustomerInfo, 
    kf_chat_history: KFChatHistory, 
    current_time=None
) -> ReplySuggestion:
    """
    生成客服聊天回复建议

    根据客服聊天历史和客户信息，为客服人员生成合适的回复建议。
    
    处理流程：
    1. 构建提示词（包含角色定义、数据结构、示例、客户数据）
    2. 调用LLM生成回复建议
    3. 解析LLM输出为结构化的ReplySuggestion对象
    4. 返回结果（失败时返回空对象）

    业务特点：
    - 模拟专业客服人员角色
    - 擅长解答客户咨询问题
    - 需区分消息发送方（客户/客服）

    Args:
        customer_info: 客户基本信息
        kf_chat_history: 客服聊天历史记录
        current_time: 当前时间（可选，默认使用系统时间）

    Returns:
        ReplySuggestion: 回复建议（包含回复内容和理由）
    """

    # 构建完整的提示词
    prompt = _kf_chat_suggest_instructions.format(
        customer_info=customer_info.model_dump_json(),     # 客户信息
        kf_chat_history=kf_chat_history.model_dump_json(), # 客服聊天历史
        current_time=current_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 当前时间
        schema_json=ReplySuggestion.get_schema_json(),    # 数据结构定义
        example_json=ReplySuggestion.get_example_json(),  # 示例数据
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


_kf_chat_suggest_instructions = """
你是出色的客服人员，擅长解答客户的咨询。

下面是客户的客服会话记录，请根据会话记录，提供合适的回复建议 ReplySuggestion 。

【注意】要根据消息中的发送者sender和接收者receiver，分清楚消息是客户发送的还是客服人员发送的。


这里是回复建议 ReplySuggestion 的数据结构定义：
-------------------
{schema_json}
-------------------

JSON对象示例：
-------------------
{example_json}
-------------------


请根据下面的客户信息，生成ReplySuggestion，具体要求：

1、【重要】您必须回复一个有效JSON对象
2、请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
3、json对象结构必须符合ReplySuggestion的定义。
4、请不要在json对象中包含任何未定义的字段。

这里是客服和客户近期的对话记录：
-------------------
{kf_chat_history}
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

