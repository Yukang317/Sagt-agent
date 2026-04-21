"""数据存储工具模块

本模块提供业务层的数据访问工具函数，封装底层存储客户端操作，
为上层业务逻辑提供类型安全的数据访问接口。

业务背景：智能体需要从存储中加载员工信息、客户信息、聊天记录、订单信息等，
并将这些数据转换为预定义的业务模型对象。

核心功能：
1. 员工信息查询
2. 客户信息查询（基本信息、标签、画像）
3. 聊天记录查询（企业微信聊天、客服聊天）
4. 订单信息查询
5. 标签设置查询

数据流转：
存储客户端(StoreClient) → 原始字典数据 → 业务模型对象 → 业务逻辑层

注意：本模块依赖 store_client.py 提供的底层存储访问能力
"""

# 导入类型定义
from typing import List, Dict, Any
# 导入日期时间处理模块
from datetime import datetime, timedelta
# 导入业务模型类
from models.sagt_models import CustomerInfo, TagInfo, ChatHistory, KFChatHistory, EmployeeInfo
from models.sagt_models import OrderInfo, OrderHistory, TagSetting, ChatMessage, CustomerProfile, CustomerTags
# 导入存储客户端
from store.store_client import StoreClient
# 导入日志工具
from utils.agent_logger import get_logger
# 导入调试装饰器
from utils.debug_aspect import debug
# 导入时间戳转换工具
from utils.datetime_string import timestamp2datetime

# 初始化存储客户端实例（全局单例）
store_client = StoreClient()

# 初始化日志记录器
logger = get_logger("store_tool")


@debug
def get_employee_info(user_id: str) -> EmployeeInfo:
    """
    根据员工ID获取员工信息
    
    业务逻辑：从存储中读取员工数据，转换为EmployeeInfo业务模型。
    如果查询失败，返回空的EmployeeInfo对象。
    
    Args:
        user_id: 员工的企业微信用户ID
        
    Returns:
        EmployeeInfo对象，包含user_id和name字段
    """
    # 创建空的员工信息对象作为默认返回值
    employee_info = EmployeeInfo()
    # 调用存储客户端获取员工数据
    employee = store_client.get_employee_by_user_id(user_id)

    # 检查是否获取到数据
    if not employee:
        logger.error(f"获取员工信息失败: {user_id}")
        return employee_info

    # 将字典数据映射到业务模型字段
    employee_info.user_id = employee.get("user_id", "")
    employee_info.name = employee.get("name", "")

    return employee_info


@debug
def get_customer_info(external_id: str, follow_user_id: str) -> CustomerInfo:
    """
    根据外部客户ID和跟进人ID获取客户信息
    
    业务逻辑：从存储中读取客户基本信息，优先使用备注名，其次使用昵称。
    
    Args:
        external_id: 外部客户ID（企业微信外部联系人ID）
        follow_user_id: 跟进该客户的员工ID
        
    Returns:
        CustomerInfo对象，包含客户的基本信息
    """
    # 创建空的客户信息对象
    customer_info = CustomerInfo()
    
    # 参数校验：必需参数不能为空
    if not external_id or not follow_user_id:
        logger.error(f"获取客户时，参数缺失: {external_id}, {follow_user_id}")
        return customer_info
    
    # 调用存储客户端获取客户数据（带数据隔离）
    external_user = store_client.get_external_user_by_external_id(external_id, follow_user_id)

    # 检查是否获取到数据
    if not external_user:
        logger.error(f"获取客户信息失败: {external_id} {follow_user_id}")
        return customer_info

    # 将字典数据映射到业务模型字段
    customer_info.external_id = external_user.get("external_id")
    customer_info.union_id = external_user.get("union_id")
    customer_info.follow_user_id = external_user.get("follow_user_id")
    
    # 获取客户昵称：优先使用备注名，其次使用默认名称
    customer_info.nick_name = external_user.get("remark_name", external_user.get("name", ""))

    return customer_info


@debug
def get_customer_tags(external_id: str, follow_user_id: str) -> CustomerTags:
    """
    获取客户的标签列表
    
    业务逻辑：先获取客户关联的标签ID列表，再逐个查询标签详情，
    将结果转换为CustomerTags业务模型。
    
    Args:
        external_id: 外部客户ID
        follow_user_id: 跟进该客户的员工ID
        
    Returns:
        CustomerTags对象，包含客户的标签信息列表
    """
    # 调用存储客户端获取客户标签详情列表
    external_user_tags = store_client.get_external_user_tag_by_external_id(external_id, follow_user_id)

    # 创建空的客户标签对象
    customer_tags = CustomerTags()
    
    # 遍历标签列表，转换为TagInfo对象
    for tag in external_user_tags:
        tag_info = TagInfo(tag_id=tag.get("tag_id"), tag_name=tag.get("tag_name"))
        customer_tags.customer_tags.append(tag_info)
    
    return customer_tags


@debug
def update_customer_tags(external_id: str, follow_user_id: str, tag_ids_add: List[str], tag_ids_remove: List[str]) -> bool:
    """
    更新客户标签
    
    业务逻辑：获取客户当前标签列表，执行添加和删除操作，
    然后将更新后的标签列表保存回存储。
    
    Args:
        external_id: 外部客户ID
        follow_user_id: 跟进该客户的员工ID
        tag_ids_add: 需要添加的标签ID列表
        tag_ids_remove: 需要删除的标签ID列表
        
    Returns:
        是否更新成功
    """
    # 参数校验
    if not external_id or not follow_user_id:
        return False
    
    # 处理空列表参数
    if not tag_ids_add:
        tag_ids_add = []
    if not tag_ids_remove:
        tag_ids_remove = []
        
    # 获取客户当前信息
    external_user = store_client.get_external_user_by_external_id(external_id, follow_user_id)
    
    # 检查客户是否存在
    if not external_user:
        return False
    
    # 获取当前标签列表
    tag_ids: List[str] = external_user.get("tags", [])
    
    # 添加新标签（去重）
    if tag_ids_add:
        tag_ids.extend([tag_id for tag_id in tag_ids_add if tag_id not in tag_ids])
    
    # 删除指定标签
    if tag_ids_remove:
        tag_ids = [tag_id for tag_id in tag_ids if tag_id not in tag_ids_remove]
    
    # 保存更新后的标签列表
    return store_client.upsert_external_user_tag_by_external_id(external_id, follow_user_id, tag_ids)


@debug
def get_customer_profile(external_id: str, follow_user_id: str) -> CustomerProfile:
    """
    获取客户画像信息
    
    业务逻辑：从存储中读取客户画像数据，使用Pydantic模型进行验证和转换。
    
    Args:
        external_id: 外部客户ID
        follow_user_id: 跟进该客户的员工ID
        
    Returns:
        CustomerProfile对象，包含客户的画像信息
    """
    # 调用存储客户端获取客户画像数据
    profile_dict = store_client.get_profile_by_external_id(external_id, follow_user_id)

    # 检查数据是否存在
    if not profile_dict:
        return CustomerProfile()
    
    # 使用Pydantic模型验证并转换数据
    try:
        return CustomerProfile.model_validate(profile_dict)
    except Exception as e:
        logger.error(f"获取客户profile失败: {e}")
        return CustomerProfile()


@debug
def update_customer_profile(external_id: str, follow_user_id: str, profile: CustomerProfile) -> bool:
    """
    更新客户画像信息
    
    业务逻辑：将CustomerProfile对象转换为字典，保存到存储中。
    
    Args:
        external_id: 外部客户ID
        follow_user_id: 跟进该客户的员工ID
        profile: CustomerProfile对象
        
    Returns:
        是否更新成功
    """
    # 参数校验
    if not external_id or not follow_user_id or not profile:
        return False
        
    # 将Pydantic模型转换为字典并保存
    return store_client.upsert_external_user_profile(external_id, follow_user_id, profile.model_dump())


@debug
def get_chat_history(external_id: str, follow_user_id: str) -> ChatHistory:
    """
    获取员工与客户的近期聊天记录
    
    业务逻辑：从存储中读取聊天消息列表，解析消息发送者和接收者，
    转换为ChatHistory业务模型。
    
    注意：当前实现包含模拟的示例消息，用于演示和测试。
    
    Args:
        external_id: 外部客户ID
        follow_user_id: 跟进该客户的员工ID
        
    Returns:
        ChatHistory对象，包含聊天消息列表
    """
    # 调用存储客户端获取企业微信聊天消息
    msgs = store_client.list_last_wxqy_msg(external_id, follow_user_id)
    
    # 创建空的聊天历史对象
    chat_history = ChatHistory()

    # 检查是否获取到消息
    if not msgs:
        return chat_history
    
    # 遍历消息列表，转换为ChatMessage对象
    for msg in msgs:
        from_id = msg.get("from_id")
        content = msg.get("content")
        msg_time = timestamp2datetime(msg.get("msg_time"))
        
        # 根据发送者ID判断角色
        if from_id == follow_user_id:
            sender = "销售人员"
            receiver = "客户"
        else:
            sender = "客户"
            receiver = "销售人员"
        
        # 添加消息到聊天历史
        chat_history.chat_msgs.append(ChatMessage(sender=sender, receiver=receiver, content=content, msg_time=msg_time))
    
    # 模拟追加员工回复消息（演示数据）
    chat_history.chat_msgs.append(
        ChatMessage(
            sender="销售人员", 
            receiver="客户", 
            content="程哥，这是您辛苦培养的成果，真是让人敬佩，后面如果需要庆祝一下，或者需要什么帮助，都可以找我。", 
            msg_time=(datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    # 模拟追加客户回复消息（演示数据）
    chat_history.chat_msgs.append(
        ChatMessage(
            sender="客户", 
            receiver="销售人员", 
            content="正想办个酒席，庆祝一下。明天上午10点左右，我去你那里找你商量一下筹办酒席的事情。", 
            msg_time=(datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    return chat_history


@debug
def get_kf_history(external_id: str) -> KFChatHistory:
    """
    获取客户与微信客服的近期聊天记录
    
    业务逻辑：从存储中读取客服消息列表，根据origin字段判断消息来源，
    转换为KFChatHistory业务模型。
    
    origin字段说明：
    - 3: 客户发送
    - 5: 客服发送
    
    Args:
        external_id: 外部客户ID
        
    Returns:
        KFChatHistory对象，包含客服聊天消息列表
    """
    # 调用存储客户端获取微信客服消息
    msgs = store_client.list_last_wxkf_msg(external_id)
    
    # 创建空的客服聊天历史对象
    chat_history = KFChatHistory()
    
    # 检查是否获取到消息
    if not msgs:
        return chat_history
    
    # 遍历消息列表，转换为ChatMessage对象
    for msg in msgs:
        external_id = msg.get("external_id")
        content = msg.get("content")
        msg_time = timestamp2datetime(msg.get("msg_time"))
        
        # 获取消息来源标识
        origin = msg.get("origin")

        # 根据origin判断发送者角色
        if origin == 3:
            sender = "客户"
            receiver = "客服"
        elif origin == 5:
            sender = "客服"
            receiver = "客户"
        else:
            sender = "其他"
            receiver = "其他"
        
        # 添加消息到客服聊天历史
        chat_history.kf_chat_msgs.append(ChatMessage(sender=sender, receiver=receiver, content=content, msg_time=msg_time))
    
    return chat_history


@debug
def get_order_history(union_id: str) -> OrderHistory:
    """
    获取客户的订单历史记录
    
    业务逻辑：从存储中读取客户的订单列表，转换为OrderHistory业务模型。
    
    Args:
        union_id: 微信UnionID（跨应用用户标识）
        
    Returns:
        OrderHistory对象，包含订单信息列表
    """
    # 调用存储客户端获取订单列表
    orders = store_client.list_wxxd_order_by_union_id(union_id)

    # 创建空的订单历史对象
    order_history = OrderHistory()
    
    # 检查是否获取到订单
    if not orders:
        return order_history
    
    # 遍历订单列表，转换为OrderInfo对象
    for order in orders:
        order_id = order.get("order_id")
        order_products = order.get("order_products")
        order_create_time = timestamp2datetime(order.get("order_create_time"))
        order_history.orders.append(OrderInfo(order_id=order_id, order_products=order_products, order_create_time=order_create_time))
    
    return order_history


@debug
def get_tag_setting() -> TagSetting:
    """
    获取系统的标签设置列表
    
    业务逻辑：从存储中读取所有未删除的标签设置，转换为TagSetting业务模型。
    
    Returns:
        TagSetting对象，包含系统标签设置列表
    """
    # 调用存储客户端获取所有标签设置
    settings = store_client.list_all_tags_setting()
    
    # 创建空的标签设置对象
    tag_setting = TagSetting()
    
    # 检查是否获取到设置
    if not settings:
        return tag_setting
    
    # 遍历标签设置列表，转换为TagInfo对象
    for setting in settings:
        tag_id = setting.get("tag_id")
        tag_name = setting.get("tag_name")
        tag_setting.tag_setting.append(TagInfo(tag_id=tag_id, tag_name=tag_name))
    
    return tag_setting