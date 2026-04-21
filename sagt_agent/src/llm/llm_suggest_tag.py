"""客户标签建议LLM模块

本模块负责调用LLM生成客户标签变更建议（TagSuggestion）。

业务背景：根据客户的多维度数据，分析客户特征变化，
生成标签添加或删除的建议，帮助销售人员更好地管理客户标签。

核心功能：
1. 分析客户的聊天记录、订单历史等数据
2. 对比系统定义的标签库和客户现有标签
3. 生成标签添加/删除建议（含原因说明）
4. 确保建议的标签ID在系统标签库中存在

数据来源：
- 系统标签设置（TagSetting）：所有可用标签的定义
- 客户现有标签（CustomerTags）：客户当前拥有的标签
- 销售聊天历史（ChatHistory）
- 客服聊天历史（KFChatHistory）
- 订单历史（OrderHistory）

输出：
- TagSuggestion：包含建议添加和删除的标签列表
"""

# 导入业务模型类
from models.sagt_models import (
    TagSetting,        # 系统标签设置模型
    TagSuggestion,     # 标签建议模型
    CustomerTags,      # 客户标签模型
    ChatHistory,       # 聊天历史模型
    KFChatHistory,     # 客服聊天历史模型
    OrderHistory       # 订单历史模型
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
logger = get_logger("llm_suggest_tag")

def llm_tag_suggest(
    tag_setting: TagSetting, 
    customer_tags: CustomerTags, 
    chat_history: ChatHistory, 
    kf_chat_history: KFChatHistory, 
    order_history: OrderHistory, 
    current_time=None
) -> TagSuggestion:
    """
    生成客户标签变更建议

    根据客户的多维度数据，分析客户特征，生成标签添加或删除建议。
    
    处理流程：
    1. 构建提示词（包含标签库、客户数据、输出格式要求）
    2. 调用LLM生成标签建议
    3. 解析LLM输出为结构化的TagSuggestion对象
    4. 返回结果（失败时返回空对象）

    关键约束：
    - 建议的标签ID必须在tag_setting中定义
    - 每个标签变更必须有明确原因
    - 输出必须是有效的JSON格式

    Args:
        tag_setting: 系统定义的所有标签（标签库）
        customer_tags: 客户当前拥有的标签
        chat_history: 销售聊天历史
        kf_chat_history: 客服聊天历史
        order_history: 订单历史
        current_time: 当前时间（可选，默认使用系统时间）

    Returns:
        TagSuggestion: 标签变更建议（添加/删除列表）
    """

    # 构建完整的提示词
    prompt = _tags_suggest_instructions.format(
        tag_setting=tag_setting.model_dump_json(),       # 系统标签库
        customer_tags=customer_tags.model_dump_json(),   # 客户现有标签
        chat_history=chat_history.model_dump_json(),     # 销售聊天历史
        kf_chat_history=kf_chat_history.model_dump_json(), # 客服聊天历史
        order_history=order_history.model_dump_json(),   # 订单历史
        current_time=current_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 当前时间
        schema_json=TagSuggestion.get_schema_json(),    # 数据结构定义
        example_json=TagSuggestion.get_example_json(),  # 示例数据
    )

    # 记录调试日志
    logger.debug(f"prompt: {prompt}")

    # 调用LLM生成标签建议
    generated_result: AIMessage = llm.invoke(prompt)
    logger.debug(f"generated_result: {generated_result}")

    # 提取LLM输出内容（处理空结果情况）
    if generated_result and generated_result.content:
        generated_tag_suggestion_json = generated_result.content
    else:
        generated_tag_suggestion_json = "{}"

    # 解析JSON并返回结果
    try:
        # 使用Pydantic验证JSON并转换为模型对象
        generated_tag_suggestion = TagSuggestion.model_validate_json(generated_tag_suggestion_json)
        logger.info(f"generated_tag_suggestion: {generated_tag_suggestion.model_dump_json()}")
        return generated_tag_suggestion
    except Exception as e:
        # 解析失败时返回空对象
        logger.error(f"生成客户标签建议失败: {e}")
        return TagSuggestion()


_tags_suggest_instructions = """
你的任务是根据客户的相关信息，生成客户标签变更建议：TagSuggestion。

这里是标签变更建议TagSuggestion的数据结构定义：
-------------------
{schema_json}
-------------------

json对象示例：
-------------------
{example_json}
-------------------

请根据下面的客户信息，生成TagSuggestion，具体要求：

1、【重要】您必须回复一个有效JSON对象
2、请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
3、json对象结构必须符合TagSuggestion的定义。其中tag_id必须是tag_setting中定义的标签ID（tag_id）。
4、请不要在json对象中包含任何未定义的字段。
5、每个要添加或者删除的标签，都要有明确的添加原因或者删除原因。
6、请不要添加或者删除未在tag_setting中定义的标签ID（tag_id）。

下面是客户的数据，请你根据这些数据，生成TagSuggestion：

1、这是系统定义的所有标签（tag_setting），所生成的建议标签ID（tag_id）必须是tag_setting中定义的标签ID（tag_id）。所添加或者删除的标签，必须有明确的添加原因或者删除原因。
-------------------
{tag_setting}
-------------------

2、这是客户的现有的标签信息：
-------------------
{customer_tags}
-------------------

3、这是客户和销售人员近期的对话记录：
-------------------
{chat_history}
-------------------

4、这是客户和客服近期的对话记录：
-------------------
{kf_chat_history}
-------------------

5、这是客户近期的订单信息：
-------------------
{order_history}
-------------------


"""
