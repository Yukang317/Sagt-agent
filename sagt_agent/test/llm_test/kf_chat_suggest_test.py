"""
客服对话建议功能集成测试

测试 src/llm/llm_suggest_kf_chat.py 中的 kf_chat_suggest 函数与真实LLM的集成
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from models.sagt_models import (
    ReplySuggestion, KFChatHistory, CustomerInfo, ChatMessage
)
from llm.llm_suggest_kf_chat import llm_kf_chat_suggest


def create_test_data():
    """创建测试数据"""
    # 构造客户信息 - 使用 CustomerInfo 模型
    customer_info = CustomerInfo(
        external_id="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
        union_id="union_123456",
        follow_user_id="ChengJianZhang",
        nick_name="程总"
    )
    
    # 构造客服聊天记录数据（客户刚发了消息，需要客服回复）
    kf_chat_history = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客服人员",
                receiver="客户",
                content="程先生您好！目前飞天茅台需预约申购，本月批次预计下周到货。您是我们的VIP客户，可以优先为您登记需求~",
                msg_time="2025-06-01 09:10:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="好的，那帮我登记两箱吧。另外问下，你们有没有茅台的收藏建议？我想投资一些有升值潜力的酒款。",
                msg_time="2025-06-01 09:15:00"
            ),
            ChatMessage(
                sender="客服人员",
                receiver="客户",
                content="已为您登记2箱飞天茅台。关于收藏投资，建议关注生肖系列和纪念版，近年来升值稳定。需要我发送详细的收藏指南吗？",
                msg_time="2025-06-01 09:20:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="这瓶2019年的茅台酒线在这里，现在值多少钱？",
                msg_time="2025-06-01 14:25:00"
            ),
            ChatMessage(
                sender="客服人员",
                receiver="客户",
                content="根据当前行情，您这瓶酒体保存完好（酒线在肩部以上），回收价约3800元。需要帮您联系专业鉴定师上门评估吗？",
                msg_time="2025-06-01 14:30:00"
            ),
            # 最新的客户消息，需要客服回复
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="那行，你安排鉴定师明天上午来看看吧，我还有几瓶想一起评估。",
                msg_time="2025-06-01 15:00:00"
            )
        ]
    )
    
    return customer_info, kf_chat_history


def test_real_llm_kf_chat_suggest():
    """测试真实LLM的客服对话建议功能"""
    print("=" * 80)
    print("客服对话建议功能集成测试")
    print("=" * 80)
    print("测试目标: src/llm/llm_suggest_kf_chat.py 中的 kf_chat_suggest 函数")
    print("测试内容: 与真实LLM的集成调用")
    print("-" * 80)
    
    # 创建测试数据
    customer_info, kf_chat_history = create_test_data()
    
    print("📋 测试数据概览:")
    print(f"👤 客户: {customer_info.nick_name} ({customer_info.external_id})")
    
    print(f"\n💬 客服聊天记录: {len(kf_chat_history.kf_chat_msgs)} 条消息")
    print("最近3条对话:")
    for msg in kf_chat_history.kf_chat_msgs[-3:]:
        sender_name = msg.sender
        print(f"  - {sender_name}: {msg.content}")
    
    # 获取最后一条消息（客户发送的，需要回复）
    last_msg = kf_chat_history.kf_chat_msgs[-1]
    last_sender = last_msg.sender
    print(f"\n🎯 最新消息（需要回复）:")
    print(f"发送者: {last_sender}")
    print(f"内容: {last_msg.content}")
    
    print("\n🤖 正在调用LLM生成客服回复建议...")
    print("请稍候，这可能需要几秒钟...")
    
    try:
        # 调用客服对话建议函数
        result = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=kf_chat_history,
            current_time="2025-06-01 15:05:00"
        )
        
        print("\n✅ LLM调用成功！")
        print("=" * 50)
        print("📝 生成的客服回复建议:")
        print(f"回复内容: {result.reply_content}")
        print(f"回复原因: {result.reply_reason}")
        print("=" * 50)
        
        # 验证返回结果的结构
        assert isinstance(result, ReplySuggestion), "返回结果应该是ReplySuggestion类型"
        assert result.reply_content, "回复内容不能为空"
        assert result.reply_reason, "回复原因不能为空"
        
        print("\n🎉 测试通过！LLM成功生成了客服回复建议")
        print(f"回复内容长度: {len(result.reply_content)} 字符")
        print(f"回复原因长度: {len(result.reply_reason)} 字符")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("请检查:")
        print("1. LLM服务是否正常运行")
        print("2. 网络连接是否正常")
        print("3. 模型配置是否正确")
        return None


def test_different_scenarios():
    """测试不同场景下的客服对话建议"""
    print("\n" + "=" * 80)
    print("测试不同场景下的客服对话建议")
    print("=" * 80)
    
    customer_info, _ = create_test_data()
    
    # 场景1：产品咨询
    print("\n🍷 场景1: 产品咨询")
    product_inquiry_chat = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="你们店里的五粮液第八代和第七代有什么区别？包装能发图看看吗？",
                msg_time="2025-06-02 15:15:00"
            )
        ]
    )
    
    try:
        result1 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=product_inquiry_chat
        )
        print(f"产品咨询场景回复: {result1.reply_content[:50]}...")
        print(f"回复原因: {result1.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：售后服务
    print("\n🔧 场景2: 售后服务")
    after_sales_chat = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="上次买的剑南春礼盒里开瓶器断了，能补发吗？",
                msg_time="2025-06-03 10:05:00"
            )
        ]
    )
    
    try:
        result2 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=after_sales_chat
        )
        print(f"售后服务场景回复: {result2.reply_content[:50]}...")
        print(f"回复原因: {result2.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景2测试失败: {e}")
    
    # 场景3：价格咨询
    print("\n💰 场景3: 价格咨询")
    price_inquiry_chat = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="问下茅台生肖酒马年和羊年的现在什么价？有回收渠道吗？",
                msg_time="2025-06-04 13:40:00"
            )
        ]
    )
    
    try:
        result3 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=price_inquiry_chat
        )
        print(f"价格咨询场景回复: {result3.reply_content[:50]}...")
        print(f"回复原因: {result3.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景3测试失败: {e}")
    
    # 场景4：红酒鉴定
    print("\n🍾 场景4: 红酒鉴定")
    wine_identification_chat = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="朋友送了箱红酒全是外文看不懂，帮忙查下什么档次？",
                msg_time="2025-06-05 18:10:00"
            )
        ]
    )
    
    try:
        result4 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=wine_identification_chat
        )
        print(f"红酒鉴定场景回复: {result4.reply_content[:50]}...")
        print(f"回复原因: {result4.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景4测试失败: {e}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 80)
    print("测试边界情况")
    print("=" * 80)
    
    customer_info, _ = create_test_data()
    
    # 边界情况1：空聊天记录
    print("\n📭 边界情况1: 空聊天记录")
    empty_chat = KFChatHistory(kf_chat_msgs=[])
    
    try:
        result1 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=empty_chat
        )
        print(f"空聊天记录回复: {result1.reply_content[:50]}...")
    except Exception as e:
        print(f"边界情况1测试失败: {e}")
    
    # 边界情况2：只有一条消息
    print("\n1️⃣ 边界情况2: 只有一条消息")
    single_msg_chat = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="你好",
                msg_time="2025-06-01 18:00:00"
            )
        ]
    )
    
    try:
        result2 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=single_msg_chat
        )
        print(f"单条消息回复: {result2.reply_content[:50]}...")
    except Exception as e:
        print(f"边界情况2测试失败: {e}")
    
    # 边界情况3：客户信息不完整
    print("\n❓ 边界情况3: 客户信息不完整")
    incomplete_customer = CustomerInfo(
        external_id="test_id",
        union_id="union_123456",
        follow_user_id="ChengJianZhang",
        nick_name=""
    )
    
    simple_chat = KFChatHistory(
        kf_chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content="有什么好酒推荐吗？",
                msg_time="2025-06-01 19:00:00"
            )
        ]
    )
    
    try:
        result3 = llm_kf_chat_suggest(
            customer_info=incomplete_customer,
            kf_chat_history=simple_chat
        )
        print(f"不完整客户信息回复: {result3.reply_content[:50]}...")
    except Exception as e:
        print(f"边界情况3测试失败: {e}")
    
    # 边界情况4：很长的对话历史
    print("\n📚 边界情况4: 很长的对话历史")
    long_chat_msgs = []
    for i in range(20):
        long_chat_msgs.extend([
            ChatMessage(
                sender="客户",
                receiver="客服人员",
                content=f"这是第{i+1}条客户消息，咨询相关产品信息。",
                msg_time=f"2025-06-01 {10+i//2}:{(i*3)%60:02d}:00"
            ),
            ChatMessage(
                sender="客服人员",
                receiver="客户",
                content=f"这是第{i+1}条客服回复，为您详细解答相关问题。",
                msg_time=f"2025-06-01 {10+i//2}:{(i*3+1)%60:02d}:00"
            )
        ])
    
    # 添加最后一条需要回复的客户消息
    long_chat_msgs.append(
        ChatMessage(
            sender="客户",
            receiver="客服人员",
            content="总结一下，我需要什么样的酒比较合适？",
            msg_time="2025-06-01 20:00:00"
        )
    )
    
    long_chat = KFChatHistory(kf_chat_msgs=long_chat_msgs)
    
    try:
        result4 = llm_kf_chat_suggest(
            customer_info=customer_info,
            kf_chat_history=long_chat
        )
        print(f"长对话历史回复: {result4.reply_content[:50]}...")
        print(f"处理了 {len(long_chat_msgs)} 条历史消息")
    except Exception as e:
        print(f"边界情况4测试失败: {e}")


if __name__ == "__main__":
    # 运行真实LLM测试
    result = test_real_llm_kf_chat_suggest()
    
    # 如果基础测试成功，运行不同场景测试
    if result is not None:
        test_different_scenarios()
        test_edge_cases()
