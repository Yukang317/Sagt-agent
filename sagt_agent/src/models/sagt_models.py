"""SAGT Agent 业务数据模型定义文件

本文件定义了 SAGT Agent 系统中所有核心业务数据模型，包括：
- 员工信息模型
- 标签管理模型
- 客户信息模型（含画像、标签）
- 聊天对话模型
- 订单信息模型
- 日程建议模型
- 意图检测模型
- 任务结果模型

所有模型均继承自 SagtBaseModel，具备统一的 schema 和 example 方法。
"""

# 导入类型定义模块
from typing import List, Dict, Any
# 导入 Pydantic 模型基类和字段定义
from pydantic import BaseModel, Field
# 导入 Annotated 类型用于类型约束
from typing_extensions import Annotated
# 导入自定义基础模型类
from models.sagt_base_model import SagtBaseModel

# 定义时间字符串类型约束
# 使用正则表达式强制格式：yyyy-MM-dd HH:mm:ss
TimeStr = Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')]

# ==================== 员工信息模型 ====================

class EmployeeInfo(SagtBaseModel):
    """
    员工信息模型
    
    存储企业员工的基本信息，用于身份识别和数据隔离。
    在数据加载阶段从存储中获取当前操作用户的信息。
    """
    user_id: str = Field(default="", description="用户唯一标识ID")
    name: str = Field(default="", description="员工姓名")

# ==================== 标签管理模型 ====================

class TagInfo(SagtBaseModel):
    """
    标签信息模型
    
    定义单个标签的结构，包含标签ID、名称和建议原因。
    用于标签设置、客户标签和标签建议等场景。
    """
    tag_id: str = Field(default="", description="标签唯一标识")
    tag_name: str = Field(default="", description="标签显示名称")
    tag_reason: str = Field(default="", description="标签添加/删除的建议原因")

class TagSetting(SagtBaseModel):
    """
    全局标签设置模型
    
    存储系统中所有可用的标签定义，用于标签建议时的参考。
    在数据加载阶段从存储中获取。
    """
    tag_setting: List[TagInfo] = Field(default=[], description="系统全局标签列表")

class TagSuggestion(SagtBaseModel):
    """
    标签建议模型
    
    用于 AI 生成的标签变更建议，包含建议添加和删除的标签列表。
    生成后需人工确认才能执行实际更新。
    """
    tag_ids_add: List[TagInfo] = Field(default=[], description="建议添加的标签列表")
    tag_ids_remove: List[TagInfo] = Field(default=[], description="建议删除的标签列表")

    @classmethod
    def get_example_instance(cls):
        """
        获取标签建议的示例实例
        
        用于 LLM 提示词中的示例输出，帮助模型理解期望的输出格式。
        """
        return cls(
            tag_ids_add=[
                TagInfo(tag_id="tag_id_1", tag_name="tag_name_1", tag_reason="建议添加该标签的原因"),
                TagInfo(tag_id="tag_id_2", tag_name="tag_name_2", tag_reason="建议添加该标签的原因")
            ],
            tag_ids_remove=[
                TagInfo(tag_id="tag_id_3", tag_name="tag_name_3", tag_reason="建议删除该标签的原因"),
                TagInfo(tag_id="tag_id_4", tag_name="tag_name_4", tag_reason="建议删除该标签的原因")
            ]
        )

# ==================== 客户画像模型profile ====================

class ProfileItem(SagtBaseModel):
    """
    客户画像子项模型
    
    表示客户画像中的一个维度（如姓名、年龄、兴趣爱好等）。
    采用键值对结构，便于灵活扩展画像维度。
    """
    item_name: str = Field(default="", description="画像维度名称（如：年龄、性别、兴趣爱好），即profile子项的名称")
    item_value: str = Field(default="", description="画像维度对应的值，即profile子项的值")

# ==================== 客户信息模型 ====================

class CustomerInfo(SagtBaseModel):
    """
    客户基本信息模型
    
    存储客户的核心标识信息，用于关联其他数据（聊天记录、订单等）。
    """
    external_id: str = Field(default="", description="外部客户唯一标识（微信外部联系人ID）")
    union_id: str = Field(default="", description="微信UnionID，用于跨应用标识同一用户")
    follow_user_id: str = Field(default="", description="跟进该客户的员工ID")
    nick_name: str = Field(default="", description="客户昵称或备注名")

class CustomerTags(SagtBaseModel):
    """
    客户标签模型
    
    存储客户当前已有的标签列表，用于客户画像分析和标签建议生成。
    """
    customer_tags: List[TagInfo] = Field(default=[], description="客户当前拥有的标签列表")

class CustomerProfile(SagtBaseModel):
    """
    客户画像模型
    
    存储客户的360度画像信息，包含多个维度的描述性数据。
    AI 根据聊天记录、订单信息等自动生成和更新。
    """
    profile_items: List[ProfileItem] = Field(default=[], description="客户画像维度列表")

    @classmethod
    def get_example_instance(cls):
        """
        获取客户画像的示例实例
        
        用于 LLM 提示词中的示例输出，展示完整的画像维度结构。
        包含23个标准画像维度：基本信息、消费特征、生活偏好、社交特征等。
        """
        return cls(
            profile_items=[
                ProfileItem(item_name="姓名", item_value="张博士"),
                ProfileItem(item_name="年龄", item_value="25"),
                ProfileItem(item_name="性别", item_value="男"),
                ProfileItem(item_name="婚姻状况", item_value="未婚"),
                ProfileItem(item_name="兴趣爱好", item_value="运动、音乐"),
                ProfileItem(item_name="教育程度", item_value="本科"),
                ProfileItem(item_name="饮酒频率", item_value="每周一次"),
                ProfileItem(item_name="饮酒场景", item_value="聚会、独自小酌"),
                ProfileItem(item_name="饮酒金额", item_value="100元"),
                ProfileItem(item_name="饮酒口感偏好", item_value="醇厚"),
                ProfileItem(item_name="饮酒购买渠道", item_value="线下实体店、线上电商平台"),
                ProfileItem(item_name="饮食习惯", item_value="无忌口、偏好的菜系等"),
                ProfileItem(item_name="出行方式", item_value="自驾、公交、地铁"),
                ProfileItem(item_name="宠物情况", item_value="是否养宠物及宠物种类"),
                ProfileItem(item_name="娱乐活动偏好", item_value="看电影、唱K等具体活动"),
                ProfileItem(item_name="家庭成员", item_value="如配偶、子女等"),
                ProfileItem(item_name="常喝的酒的种类", item_value="如白酒、红酒、啤酒等"),
                ProfileItem(item_name="喜欢的酒的品牌", item_value="如茅台、五粮液等"),
                ProfileItem(item_name="消费频率", item_value="如每周一次、每月几次等"),
                ProfileItem(item_name="消费场景", item_value="如聚会、独自小酌等"),
                ProfileItem(item_name="每次消费的大致金额", item_value="如100元"),
                ProfileItem(item_name="对酒的口感偏好", item_value="如醇厚、清爽等"),
                ProfileItem(item_name="购买渠道", item_value="如线下实体店、线上电商平台等")
            ]
        )

# ==================== 聊天对话模型 ====================

class ChatMessage(SagtBaseModel):
    """
    聊天消息模型
    
    表示单条聊天消息，包含发送者、接收者、内容和时间戳。
    用于构建聊天历史记录。
    """
    sender: str = Field(default="", description="消息发送者（如：销售人员、客户、客服）")
    receiver: str = Field(default="", description="消息接收者")
    content: str = Field(default="", description="消息内容")
    msg_time: TimeStr = Field(default="", description="消息发送时间，格式：yyyy-MM-dd HH:mm:ss")

class ReplySuggestion(SagtBaseModel):
    """
    回复建议模型
    
    存储 AI 生成的回复内容和建议理由。
    用于聊天建议和客服建议场景。
    """
    reply_content: str = Field(default="", description="生成的回复内容")
    reply_reason: str = Field(default="", description="回复建议的理由说明")

    @classmethod
    def get_example_instance(cls):
        """
        获取回复建议的示例实例
        
        用于 LLM 提示词中的示例输出。
        """
        return cls(
            reply_content="回复内容",
            reply_reason="回复原因"
        )

class ChatHistory(SagtBaseModel):
    """
    销售人员与客户聊天历史模型
    
    存储销售人员与客户之间的对话记录，用于生成聊天建议。
    """
    chat_msgs: List[ChatMessage] = Field(default=[], description="聊天消息列表")

class KFChatHistory(SagtBaseModel):
    """
    客服聊天历史模型
    
    存储客户与微信客服之间的对话记录，用于客服场景分析。
    """
    kf_chat_msgs: List[ChatMessage] = Field(default=[], description="客服聊天消息列表")

# ==================== 订单信息模型 ====================

class OrderInfo(SagtBaseModel):
    """
    订单信息模型
    
    存储单个订单的详细信息。
    """
    order_id: str = Field(default="", description="订单唯一标识")
    order_products: List[str] = Field(default="", description="订单包含的产品列表")
    order_create_time: TimeStr = Field(default="", description="订单创建时间")

class OrderHistory(SagtBaseModel):
    """
    客户订单历史模型
    
    存储客户的历史订单记录，用于消费行为分析和客户画像生成。
    """
    orders: List[OrderInfo] = Field(default=[], description="历史订单列表")

# ==================== 日程建议模型 ====================

class ScheduleSuggestion(SagtBaseModel):
    """
    日程建议模型
    
    存储 AI 生成的日程安排建议，包含标题、时间、时长和理由。
    用于辅助销售人员安排客户跟进事项。
    """
    title: str = Field(default="", title="Title", description="日程标题，描述具体事项")
    start_time: TimeStr = Field(default="", title="Start Time", description="开始时间，格式：yyyy-MM-dd HH:mm:ss")
    duration: int = Field(default=30, title="Duration", description="持续时间，单位：分钟，默认30分钟")
    schedule_reason: str = Field(default="", title="Schedule Reason", description="创建此日程的原因说明")

    @classmethod
    def get_example_instance(cls):
        """
        获取日程建议的示例实例
        
        用于 LLM 提示词中的示例输出。
        """
        return cls(
            title="日程标题，包含具体事项说明",
            start_time="2026-01-01 10:00:00",
            duration=60,
            schedule_reason="日程建议原因"
        )

# ==================== 闲聊对话模型 ====================

class JustTalkOutput(SagtBaseModel):
    """
    闲聊对话输出模型
    
    存储无明确业务意图时的自由对话响应内容。
    用于处理用户的闲聊、咨询等非业务请求。
    """
    just_talk_output: str = Field(default="", description="闲聊应答内容")
    
    @classmethod
    def get_example_instance(cls):
        """
        获取闲聊输出的示例实例
        
        用于 LLM 提示词中的示例输出。
        """
        return cls(
            just_talk_output="输出应答内容"
        )

# ==================== 意图检测模型 ====================

class Intent(SagtBaseModel):
    """
    意图模型
    
    定义系统支持的业务意图类型，用于意图识别和路由。
    """
    intent_id: str = Field(default="", description="意图唯一标识")
    intent_description: str = Field(default="", description="意图的业务场景描述")

    @classmethod
    def get_example_instance(cls):
        """
        获取意图的示例实例
        
        用于 LLM 意图检测时的示例输出。
        """
        return cls(
            intent_id="chat_suggestion",
            intent_description="生成聊天建议"
        )

# ==================== 执行结果模型 ====================

class TaskResult(SagtBaseModel):
    """
    任务结果模型
    
    存储整个任务的最终执行结果，用于返回给调用方。
    """
    task_result: str = Field(default="", description="任务执行结果内容")
    task_result_explain: str = Field(default="", description="任务结果的详细解释")
    task_result_code: int = Field(default=1, description="任务结果代码：0表示成功，1表示失败")

class NodeResult(SagtBaseModel):
    """
    节点执行结果模型
    
    存储状态图中单个节点的执行结果，用于记录执行日志和错误追踪。
    所有节点执行结果会通过 reducer 函数累积到状态中。
    """
    execute_node_name: str = Field(default="", description="执行的节点名称")
    execute_result_code: int = Field(default=1, description="节点执行结果代码：0表示成功，1表示失败")
    execute_result_msg: str = Field(default="", description="节点执行结果消息")
    execute_exceptions: List[str] = Field(default=[], description="节点执行过程中的异常信息列表")
    