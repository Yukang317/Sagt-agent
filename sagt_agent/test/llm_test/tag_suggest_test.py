"""
标签建议功能集成测试

测试 src/llm/llm_tag_suggest.py 中的 tag_suggest 函数与真实LLM的集成
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from models.sagt_models import (
    TagSetting, TagSuggestion, CustomerTags, ChatHistory, 
    KFChatHistory, OrderHistory, TagInfo, ChatMessage, OrderInfo
)
from llm.llm_suggest_tag import llm_tag_suggest


def create_test_data():
    """创建测试数据"""
    # 构造标签设置数据（参考 sagt_demo_init.py）
    tags_setting = TagSetting(
        tag_setting=[
            # 基础属性标签
            TagInfo(tag_id="BASIC_001", tag_name="高净值客户", tag_reason=""),
            TagInfo(tag_id="BASIC_002", tag_name="中年男性", tag_reason=""),
            TagInfo(tag_id="BASIC_003", tag_name="已婚有子女", tag_reason=""),
            TagInfo(tag_id="BASIC_004", tag_name="制造业管理层", tag_reason=""),
            TagInfo(tag_id="BASIC_005", tag_name="家有老人", tag_reason=""),
            
            # 消费行为标签
            TagInfo(tag_id="BUY_006", tag_name="酱香型白酒偏好", tag_reason=""),
            TagInfo(tag_id="BUY_007", tag_name="茅台收藏者", tag_reason=""),
            TagInfo(tag_id="BUY_008", tag_name="高频团购客户", tag_reason=""),
            TagInfo(tag_id="BUY_009", tag_name="节日礼品采购大户", tag_reason=""),
            TagInfo(tag_id="BUY_010", tag_name="高端红酒次级需求", tag_reason=""),
            
            # 社交关系标签
            TagInfo(tag_id="SOCIAL_011", tag_name="商务宴请需求强", tag_reason=""),
            TagInfo(tag_id="SOCIAL_012", tag_name="企业领导层关系网", tag_reason=""),
            TagInfo(tag_id="SOCIAL_013", tag_name="家庭宴会场景多", tag_reason=""),
            
            # 服务敏感度标签
            TagInfo(tag_id="SERVICE_014", tag_name="需优先库存预留", tag_reason=""),
            TagInfo(tag_id="SERVICE_015", tag_name="依赖专业鉴酒服务", tag_reason=""),
            TagInfo(tag_id="SERVICE_016", tag_name="发票开具敏感型", tag_reason=""),
            
            # 生命周期标签
            TagInfo(tag_id="LIFE_017", tag_name="酒类收藏增值期", tag_reason=""),
            TagInfo(tag_id="LIFE_018", tag_name="子女教育阶段（中学）", tag_reason=""),
            TagInfo(tag_id="LIFE_019", tag_name="家庭责任高峰期（赡老育小）", tag_reason=""),
        ]
    )
    
    # 构造客户现有标签数据
    customer_tags = CustomerTags(
        customer_tags=[
            TagInfo(tag_id="BASIC_002", tag_name="中年男性", tag_reason="基于客户基本信息"),
            TagInfo(tag_id="BUY_006", tag_name="酱香型白酒偏好", tag_reason="历史购买记录显示"),
        ]
    )
    
    # 构造聊天记录数据（参考 sagt_demo_init.py）
    chat_history = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="ChengJianZhang",
                receiver="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                content="大程哥，今天刚到两箱飞天茅台，给您留了一箱，需要的话随时联系！",
                msg_time="2024-09-22 09:15:00"
            ),
            ChatMessage(
                sender="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                receiver="ChengJianZhang",
                content="太好了小张！正好中秋节要用，这箱给我留着，下午我来拿。",
                msg_time="2024-09-22 09:20:00"
            ),
            ChatMessage(
                sender="ChengJianZhang",
                receiver="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                content="程哥，您上次说老爷子十月生日？需要寿宴用酒的话提前说，我调货。",
                msg_time="2024-10-08 11:05:00"
            ),
            ChatMessage(
                sender="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                receiver="ChengJianZhang",
                content="正想找你！六十大寿要办五桌，推荐下？",
                msg_time="2024-10-08 11:15:00"
            ),
            ChatMessage(
                sender="ChengJianZhang",
                receiver="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                content="建议主桌用茅台，其他桌用红花郎15年，喜庆又实惠，我按团购价算。",
                msg_time="2024-10-08 11:20:00"
            ),
        ]
    )
    
    # 构造客服聊天记录数据
    kf_chat_history = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                receiver="客服001",
                content="请问茅台1935和飞天茅台有什么区别？",
                msg_time="2025-03-20 14:30:00"
            ),
            ChatMessage(
                sender="客服001",
                receiver="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                content="茅台1935是新推出的高端产品，采用特殊工艺，口感更加醇厚，适合收藏。",
                msg_time="2025-03-20 14:32:00"
            ),
            ChatMessage(
                sender="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                receiver="客服001",
                content="那价格比飞天茅台贵多少？",
                msg_time="2025-03-20 14:35:00"
            ),
        ]
    )
    
    # 构造订单历史数据（参考 sagt_demo_init.py）
    order_history = OrderHistory(
        orders=[
            OrderInfo(
                order_id="WX20240905",
                order_products=["53度飞天茅台（2023年产-500ml×6瓶/箱）"],
                order_create_time="2024-09-05 10:00:00"
            ),
            OrderInfo(
                order_id="WX20240912",
                order_products=["五粮液第八代普五（500ml×2瓶）"],
                order_create_time="2024-09-12 10:00:00"
            ),
            OrderInfo(
                order_id="WX20240918",
                order_products=["红花郎15年（500ml×4箱）"],
                order_create_time="2024-09-15 10:00:00"
            ),
            OrderInfo(
                order_id="WX20240922",
                order_products=["茅台王子酒（酱香经典-500ml×12瓶）"],
                order_create_time="2024-09-22 10:00:00"
            ),
            OrderInfo(
                order_id="WX20250322",
                order_products=["茅台1935（新上市-500ml×2瓶）"],
                order_create_time="2025-03-22 10:00:00"
            ),
            OrderInfo(
                order_id="WX20250411",
                order_products=["奔富Bin407红酒（750ml×6瓶）"],
                order_create_time="2025-04-11 10:00:00"
            ),
        ]
    )
    
    return tags_setting, customer_tags, chat_history, kf_chat_history, order_history


def test_real_llm_tag_suggest():
    """测试真实LLM的标签建议功能"""
    print("=" * 80)
    print("开始测试真实LLM的标签建议功能")
    print("=" * 80)
    
    # 创建测试数据
    tags_setting, customer_tags, chat_history, kf_chat_history, order_history = create_test_data()
    
    print("\n📋 输入数据概览:")
    print(f"- 标签设置: {len(tags_setting.tag_setting)} 个标签")
    print(f"- 客户现有标签: {len(customer_tags.customer_tags)} 个")
    print(f"- 聊天记录: {len(chat_history.chat_msgs)} 条消息")
    print(f"- 客服聊天记录: {len(kf_chat_history.kf_chat_msgs)} 条消息")
    print(f"- 订单历史: {len(order_history.orders)} 个订单")
    
    print("\n🏷️ 客户现有标签:")
    for tag in customer_tags.customer_tags:
        print(f"  - {tag.tag_id}: {tag.tag_name}")
    
    print("\n💬 最近聊天内容:")
    for msg in chat_history.chat_msgs[-2:]:
        sender_name = "销售" if msg.sender == "ChengJianZhang" else "客户"
        print(f"  - {sender_name}: {msg.content}")
    
    print("\n🛒 最近订单:")
    for order in order_history.orders[-3:]:
        print(f"  - {order.order_id}: {', '.join(order.order_products)}")
    
    print("\n🤖 调用LLM生成标签建议...")
    print("-" * 50)
    
    try:
        # 调用真实的LLM服务
        result = llm_tag_suggest(
            tag_setting=tags_setting,
            customer_tags=customer_tags,
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        print("✅ LLM调用成功!")
        print("\n📊 标签建议结果:")
        print(f"- 建议添加标签数量: {len(result.tag_ids_add)}")
        print(f"- 建议删除标签数量: {len(result.tag_ids_remove)}")
        
        if result.tag_ids_add:
            print("\n➕ 建议添加的标签:")
            for i, tag in enumerate(result.tag_ids_add, 1):
                print(f"  {i}. {tag.tag_id}: {tag.tag_name}")
                print(f"     原因: {tag.tag_reason}")
                print()
        
        if result.tag_ids_remove:
            print("➖ 建议删除的标签:")
            for i, tag in enumerate(result.tag_ids_remove, 1):
                print(f"  {i}. {tag.tag_id}: {tag.tag_name}")
                print(f"     原因: {tag.tag_reason}")
                print()
        
        if not result.tag_ids_add and not result.tag_ids_remove:
            print("ℹ️ LLM认为当前标签已经合适，无需调整")
        
        print("=" * 80)
        print("测试完成!")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        return None


def test_different_scenarios():
    """测试不同场景下的标签建议"""
    print("\n" + "=" * 80)
    print("测试不同场景下的标签建议")
    print("=" * 80)
    
    # 场景1：新客户（无现有标签）
    print("\n🆕 场景1: 新客户（无现有标签）")
    tags_setting, _, chat_history, kf_chat_history, order_history = create_test_data()
    empty_customer_tags = CustomerTags(customer_tags=[])
    
    try:
        result1 = llm_tag_suggest(
            tag_setting=tags_setting,
            customer_tags=empty_customer_tags,
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history
        )
        print(f"新客户建议添加 {len(result1.tag_ids_add)} 个标签")
        for tag in result1.tag_ids_add[:3]:  # 只显示前3个
            print(f"  - {tag.tag_name}: {tag.tag_reason[:50]}...")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：高价值客户（有多个高端标签）
    print("\n💎 场景2: 高价值客户")
    high_value_tags = CustomerTags(
        customer_tags=[
            TagInfo(tag_id="BASIC_001", tag_name="高净值客户", tag_reason=""),
            TagInfo(tag_id="BUY_007", tag_name="茅台收藏者", tag_reason=""),
            TagInfo(tag_id="SOCIAL_011", tag_name="商务宴请需求强", tag_reason=""),
        ]
    )
    
    try:
        result2 = llm_tag_suggest(
            tag_setting=tags_setting,
            customer_tags=high_value_tags,
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history
        )
        print(f"高价值客户建议添加 {len(result2.tag_ids_add)} 个标签，删除 {len(result2.tag_ids_remove)} 个标签")
    except Exception as e:
        print(f"场景2测试失败: {e}")


if __name__ == "__main__":
    # 运行真实LLM测试
    result = test_real_llm_tag_suggest()
    
    # 如果基础测试成功，运行不同场景测试
    if result is not None:
        test_different_scenarios()
