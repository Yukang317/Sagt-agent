"""客户画像生成LLM模块

本模块负责调用LLM生成客户画像（CustomerProfile）。

业务背景：根据客户的多维度数据（聊天记录、订单历史、标签等），
自动生成或更新客户的360度画像，包含24个维度的客户信息。

核心功能：
1. 整合客户的聊天历史、订单信息、标签等数据
2. 调用LLM进行信息提取和分析
3. 输出结构化的客户画像数据
4. 支持增量更新（保留旧画像中有价值的信息）

数据来源：
- 销售聊天历史（ChatHistory）
- 客服聊天历史（KFChatHistory）
- 订单历史（OrderHistory）
- 客户标签（CustomerTags）
- 现有客户画像（CustomerProfile）

输出：
- CustomerProfile：包含24个维度的客户画像信息
"""

# 导入业务模型类
from models.sagt_models import (
    CustomerTags,       # 客户标签模型
    ChatHistory,        # 聊天历史模型
    KFChatHistory,      # 客服聊天历史模型
    OrderHistory,       # 订单历史模型
    CustomerProfile     # 客户画像模型
)
# 导入初始化好的LLM实例
from llm.llm_setting import chat_model as llm
# 导入LangChain的AIMessage类型
from langchain_core.messages import AIMessage
# 导入日志工具
from utils.agent_logger import get_logger

# 获取本模块的日志实例
logger = get_logger("llm_suggest_profile")

def llm_profile_suggest(
    chat_history: ChatHistory, 
    kf_chat_history: KFChatHistory, 
    order_history: OrderHistory, 
    customer_tags: CustomerTags, 
    customer_profile: CustomerProfile
) -> CustomerProfile:
    """
    生成客户画像建议

    根据客户的多维度数据，调用LLM生成或更新客户画像。
    
    处理流程：
    1. 构建提示词（包含数据结构定义、示例、客户数据）
    2. 调用LLM生成回复
    3. 解析LLM输出为结构化的CustomerProfile对象
    4. 返回结果（失败时返回空对象）

    Args:
        chat_history: 销售人员与客户的聊天历史
        kf_chat_history: 客服与客户的聊天历史
        order_history: 客户订单历史
        customer_tags: 客户当前标签
        customer_profile: 客户现有画像（用于增量更新）

    Returns:
        CustomerProfile: 生成的客户画像对象
    """

    # 构建完整的提示词
    prompt = _profile_instructions.format(
        chat_history=chat_history.model_dump_json(),           # 销售聊天历史
        kf_chat_history=kf_chat_history.model_dump_json(),   # 客服聊天历史
        order_history=order_history.model_dump_json(),       # 订单历史
        customer_tags=customer_tags.model_dump_json(),       # 客户标签
        customer_profile=customer_profile.model_dump_json(), # 现有画像
        schema_json=CustomerProfile.get_schema_json(),      # 数据结构定义
        example_json=CustomerProfile.get_example_json(),    # 示例数据
    )

    # 记录调试日志
    logger.debug(f"prompt: {prompt}")

    # 调用LLM生成客户画像
    generated_result: AIMessage = llm.invoke(prompt)
    logger.debug(f"generated_result: {generated_result}")

    # 提取LLM输出内容（处理空结果情况）
    if generated_result and generated_result.content:
        generated_profile_json = generated_result.content
    else:
        generated_profile_json = "{}"

    # 解析JSON并返回结果
    try:
        # 使用Pydantic验证JSON并转换为模型对象
        generated_profile = CustomerProfile.model_validate_json(generated_profile_json)
        logger.info(f"generated_profile: {generated_profile.model_dump_json()}")
        return generated_profile
    except Exception as e:
        # 解析失败时返回空对象
        logger.error(f"生成客户profile建议失败: {e}")
        return CustomerProfile()


# 客户画像生成提示词模板
# 包含：角色定义、数据结构、示例、输入数据、输出要求
_profile_instructions = """
你的任务是根据客户的相关信息，提取客户的profile信息：CustomerProfile。

这里是客户profile信息CustomerProfile的数据结构定义：
-------------------
{schema_json}
-------------------

json对象示例：
-------------------
{example_json}
-------------------


请根据下面的客户信息，生成CustomerProfile：

1、【重要】您必须回复一个有效JSON对象。
2、请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
3、JSON对象结构必须符合CustomerProfile的定义
4、内容包含你认为可以描述客户情况的所有信息。
5、旧profile中需要保留的信息，也更新到新的profile中，业务系统使用新profile时，会完整覆盖旧的profile。



示例目标字段：

1. 【姓名】:包括昵称、曾用名等可能相关的称呼。
2. 【年龄】: 精确到具体岁数，若提及大概年龄段也需注明。
3. 【性别】: 明确是男、女或其他表述。
4. 【职业】: 具体的工作类型，如包含多个职业可全部列出。
5. 【兴趣爱好】: 如具体的运动项目、音乐类型等。
6. 【婚姻状况】: 是否已婚、未婚、离异等。
7. 【教育程度】: 如高中、本科、硕士等。
8. 【饮酒频率】: 如每周一次、每月几次等。
9. 【饮酒场景】: 如聚会、独自小酌等。
10. 【饮酒金额】: 如100元。
11. 【饮酒口感偏好】: 如醇厚、清爽等。
12. 【饮酒购买渠道】: 如线下实体店、线上电商平台等。
13. 【饮食习惯】: 如是否有忌口、偏好的菜系等。
14. 【出行方式】: 如自驾、公交、地铁等。
15. 【宠物情况】: 是否养宠物及宠物种类。
16. 【娱乐活动偏好】: 如看电影、唱K等具体活动。
17. 【家庭成员】: 如配偶、子女等。
18. 【常喝的酒的种类】: 如白酒、红酒、啤酒等。
19. 【喜欢的酒的品牌】: 如茅台、五粮液等。
20. 【消费频率】: 如每周一次、每月几次等。
21. 【消费场景】: 如聚会、独自小酌等。
22. 【每次消费的大致金额】: 如100元。
23. 【对酒的口感偏好】: 如醇厚、清爽等。
24. 【购买渠道】: 如线下实体店、线上电商平台等。

下面是客户的数据：



这里是客户和销售人员近期的对话记录：
-------------------
{chat_history}
-------------------

这里是客户和客服近期的对话记录：
-------------------
{kf_chat_history}
-------------------

这里是客户近期的订单信息：
-------------------
{order_history}
-------------------

这里是客户的标签信息：
-------------------
{customer_tags}
-------------------

这里是客户之前的profile信息：
-------------------
{customer_profile}
-------------------

"""
