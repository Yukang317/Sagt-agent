"""
客户画像建议功能集成测试

测试 src/llm/llm_suggest_profile.py 中的 profile_suggest 函数与真实LLM的集成
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from models.sagt_models import (
    CustomerProfile, ChatHistory, 
    KFChatHistory, OrderHistory, TagInfo, ChatMessage, OrderInfo, ProfileItem, CustomerTags
)

from llm.llm_suggest_profile import llm_profile_suggest


def create_test_data():
    """创建测试数据"""
    # 构造标签设置数据（参考 sagt_demo_init.py）

    customer_tags = CustomerTags(
        customer_tags=[
            TagInfo(tag_id="BASIC_001", tag_name="高净值客户", tag_reason=""),
            TagInfo(tag_id="BASIC_002", tag_name="中年男性", tag_reason=""),
            TagInfo(tag_id="BASIC_003", tag_name="已婚有子女", tag_reason=""),
            TagInfo(tag_id="BASIC_004", tag_name="制造业管理层", tag_reason=""),
            TagInfo(tag_id="BASIC_005", tag_name="家有老人", tag_reason=""),
            TagInfo(tag_id="BASIC_006", tag_name="酱香型白酒偏好", tag_reason=""),
            TagInfo(tag_id="BASIC_007", tag_name="茅台收藏者", tag_reason=""),
            TagInfo(tag_id="BASIC_008", tag_name="高频团购客户", tag_reason=""),
            TagInfo(tag_id="BASIC_009", tag_name="节日礼品采购大户", tag_reason=""),
            TagInfo(tag_id="BASIC_010", tag_name="高端红酒次级需求", tag_reason=""),
        ]
    )
    
    # 构造客户现有画像数据
    customer_profile = CustomerProfile(
        profile_items=[
            ProfileItem(item_name="姓名", item_value="程建章"),
            ProfileItem(item_name="性别", item_value="男"),
            ProfileItem(item_name="年龄段", item_value="中年"),
            ProfileItem(item_name="职业", item_value="制造业管理层"),
            ProfileItem(item_name="常喝的酒的种类", item_value="白酒"),
            ProfileItem(item_name="喜欢的酒的品牌", item_value="茅台"),
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
                content="好的小张，老爷子85岁生日，我们准备办个家庭聚会，大概20人左右。需要准备一些好酒，你看看有什么推荐？",
                msg_time="2024-10-08 11:10:00"
            ),
            ChatMessage(
                sender="ChengJianZhang",
                receiver="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                content="程哥，我女儿明年要上高中了，听说您儿子在重点高中读书，能给点建议吗？",
                msg_time="2024-10-15 14:30:00"
            ),
            ChatMessage(
                sender="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
                receiver="ChengJianZhang",
                content="当然可以！教育确实很重要，我们家也是很重视孩子的学习。改天详细聊聊。",
                msg_time="2024-10-15 14:35:00"
            )
        ]
    )
    
    # 构造客服对话记录
    kf_chat_history = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客服小李",
                receiver="程建章",
                content="程总您好，您上次预订的五粮液已经到货，什么时候方便取货？",
                msg_time="2024-09-20 10:00:00"
            ),
            ChatMessage(
                sender="程建章",
                receiver="客服小李",
                content="好的，我明天下午过去拿。对了，最近有什么新品推荐吗？",
                msg_time="2024-09-20 10:05:00"
            ),
            ChatMessage(
                sender="客服小李",
                receiver="程建章",
                content="有的，最近到了一批年份酒，品质很不错，您要不要了解一下？",
                msg_time="2024-09-20 10:08:00"
            )
        ]
    )
    
    # 构造订单历史数据
    order_history = OrderHistory(
        orders=[
            OrderInfo(
                order_id="ORD20240915001",
                order_time="2024-09-15 14:30:00",
                order_products=["飞天茅台 53度 500ml", "五粮液 52度 500ml"],
                order_amount=3200.00,
                order_status="已完成"
            ),
            OrderInfo(
                order_id="ORD20240920001",
                order_time="2024-09-20 16:20:00",
                order_products=["剑南春 52度 500ml", "国窖1573 52度 500ml"],
                order_amount=1800.00,
                order_status="已完成"
            ),
            OrderInfo(
                order_id="ORD20241005001",
                order_time="2024-10-05 11:15:00",
                order_products=["飞天茅台 53度 500ml*6", "茅台迎宾酒 43度 500ml*12"],
                order_amount=12800.00,
                order_status="已完成"
            ),
            OrderInfo(
                order_id="ORD20241010001",
                order_time="2024-10-10 09:45:00",
                order_products=["五粮液 52度 500ml*4", "剑南春 52度 500ml*2"],
                order_amount=4600.00,
                order_status="配送中"
            )
        ]
    )
    
    return customer_tags, customer_profile, chat_history, kf_chat_history, order_history


def test_real_llm_profile_suggest():
    """测试真实LLM的客户画像建议功能"""
    print("=" * 80)
    print("客户画像建议功能集成测试")
    print("=" * 80)
    
    # 创建测试数据
    customer_tags, customer_profile, chat_history, kf_chat_history, order_history = create_test_data()
    
    print("\n📋 测试数据概览:")
    print(f"- 标签设置数量: {len(customer_tags.customer_tags)}")
    print(f"- 现有画像项目数量: {len(customer_profile.profile_items)}")
    print(f"- 聊天记录数量: {len(chat_history.chat_msgs)}")
    print(f"- 客服对话数量: {len(kf_chat_history.kf_chat_msgs)}")
    print(f"- 订单记录数量: {len(order_history.orders)}")
    
    print("\n👤 现有客户画像:")
    for item in customer_profile.profile_items:
        print(f"  - {item.item_name}: {item.item_value}")
    
    print("\n💬 最近对话:")
    for msg in chat_history.chat_msgs[-3:]:
        sender_name = "程建章" if msg.sender == "wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg" else "销售小张"
        print(f"  - {sender_name}: {msg.content}")
    
    print("\n🛒 最近订单:")
    for order in order_history.orders[-3:]:
        print(f"  - {order.order_id}: {', '.join(order.order_products)}")
    
    print("\n🤖 调用LLM生成客户画像建议...")
    print("-" * 50)
    
    try:
        # 调用真实的LLM服务
        result = llm_profile_suggest(
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history,
            customer_tags=customer_tags,
            customer_profile=customer_profile
        )
        
        print("✅ LLM调用成功!")
        print("\n📊 客户画像建议结果:")
        print(f"- 画像项目数量: {len(result.profile_items)}")
        
        if result.profile_items:
            print("\n📝 更新后的客户画像:")
            for i, item in enumerate(result.profile_items, 1):
                print(f"  {i}. {item.item_name}: {item.item_value}")
                print()
        else:
            print("ℹ️ LLM返回了空的客户画像")
        
        # 对比分析
        print("\n🔍 画像变化分析:")
        old_items = {item.item_name: item.item_value for item in customer_profile.profile_items}
        new_items = {item.item_name: item.item_value for item in result.profile_items}
        
        # 新增的画像项
        added_items = set(new_items.keys()) - set(old_items.keys())
        if added_items:
            print("➕ 新增画像项:")
            for item_name in added_items:
                print(f"  - {item_name}: {new_items[item_name]}")
        
        # 更新的画像项
        updated_items = []
        for item_name in set(old_items.keys()) & set(new_items.keys()):
            if old_items[item_name] != new_items[item_name]:
                updated_items.append(item_name)
        
        if updated_items:
            print("🔄 更新画像项:")
            for item_name in updated_items:
                print(f"  - {item_name}: {old_items[item_name]} → {new_items[item_name]}")
        
        # 删除的画像项
        removed_items = set(old_items.keys()) - set(new_items.keys())
        if removed_items:
            print("➖ 删除画像项:")
            for item_name in removed_items:
                print(f"  - {item_name}: {old_items[item_name]}")
        
        if not added_items and not updated_items and not removed_items:
            print("ℹ️ 客户画像无变化")
        
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
    """测试不同场景下的客户画像建议"""
    print("\n" + "=" * 80)
    print("测试不同场景下的客户画像建议")
    print("=" * 80)
    
    customer_tags, _, chat_history, kf_chat_history, order_history = create_test_data()
    
    # 场景1：新客户（无现有画像）
    print("\n🆕 场景1: 新客户（无现有画像）")
    empty_customer_profile = CustomerProfile(profile_items=[])
    
    try:
        result1 = llm_profile_suggest(
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history,
            customer_tags=customer_tags,
            customer_profile=empty_customer_profile
        )
        print(f"新客户生成 {len(result1.profile_items)} 个画像项")
        for item in result1.profile_items[:5]:  # 只显示前5个
            print(f"  - {item.item_name}: {item.item_value}")
        if len(result1.profile_items) > 5:
            print(f"  ... 还有 {len(result1.profile_items) - 5} 个画像项")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：高价值客户（详细画像）
    print("\n💎 场景2: 高价值客户（详细画像）")
    detailed_profile = CustomerProfile(
        profile_items=[
            ProfileItem(item_name="姓名", item_value="程建章"),
            ProfileItem(item_name="性别", item_value="男"),
            ProfileItem(item_name="年龄", item_value="45岁"),
            ProfileItem(item_name="职业", item_value="制造业总经理"),
            ProfileItem(item_name="婚姻状况", item_value="已婚"),
            ProfileItem(item_name="家庭成员", item_value="妻子、儿子（高中生）、父亲（85岁）"),
            ProfileItem(item_name="常喝的酒的种类", item_value="白酒、红酒"),
            ProfileItem(item_name="喜欢的酒的品牌", item_value="茅台、五粮液、剑南春"),
            ProfileItem(item_name="消费频率", item_value="每月2-3次"),
            ProfileItem(item_name="每次消费的大致金额", item_value="2000-5000元"),
            ProfileItem(item_name="消费场景", item_value="商务宴请、家庭聚会、节日庆祝"),
            ProfileItem(item_name="对酒的口感偏好", item_value="醇厚、回甘"),
        ]
    )
    
    try:
        result2 = llm_profile_suggest(
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history,
            customer_tags=customer_tags,
            customer_profile=detailed_profile
        )
        print(f"高价值客户更新后有 {len(result2.profile_items)} 个画像项")
        
        # 分析变化
        old_items = {item.item_name: item.item_value for item in detailed_profile.profile_items}
        new_items = {item.item_name: item.item_value for item in result2.profile_items}
        
        changes = 0
        for item_name in new_items:
            if item_name not in old_items or old_items.get(item_name) != new_items[item_name]:
                changes += 1
        
        print(f"发现 {changes} 处画像变化")
        
    except Exception as e:
        print(f"场景2测试失败: {e}")
    
    # 场景3：简单客户（基础画像）
    print("\n👤 场景3: 简单客户（基础画像）")
    simple_profile = CustomerProfile(
        profile_items=[
            ProfileItem(item_name="姓名", item_value="张三"),
            ProfileItem(item_name="性别", item_value="男"),
        ]
    )
    
    try:
        result3 = llm_profile_suggest(
            chat_history=chat_history,
            kf_chat_history=kf_chat_history,
            order_history=order_history,
            customer_tags=customer_tags,
            customer_profile=simple_profile
        )
        print(f"简单客户扩展后有 {len(result3.profile_items)} 个画像项")
        
        # 显示新增的画像项
        old_names = {item.item_name for item in simple_profile.profile_items}
        new_items = [item for item in result3.profile_items if item.item_name not in old_names]
        
        if new_items:
            print("新增画像项:")
            for item in new_items[:5]:  # 只显示前5个
                print(f"  - {item.item_name}: {item.item_value}")
        
    except Exception as e:
        print(f"场景3测试失败: {e}")


if __name__ == "__main__":
    # 运行真实LLM测试
    result = test_real_llm_profile_suggest()
    
    # 如果基础测试成功，运行不同场景测试
    if result is not None:
        test_different_scenarios()
