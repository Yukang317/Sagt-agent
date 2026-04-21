"""
Just Talk功能集成测试

测试 src/llm/llm_just_talk.py 中的 just_talk_prompt 函数与真实LLM的集成
"""

import sys
import os

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from llm.llm_just_talk import llm_just_talk


def test_real_llm_just_talk():
    """测试真实LLM的Just Talk功能"""
    print("=" * 80)
    print("Just Talk功能集成测试")
    print("=" * 80)
    print("测试目标: src/llm/llm_just_talk.py 中的 just_talk_prompt 函数")
    print("测试内容: 与真实LLM的集成调用")
    print("-" * 80)
    
    # 测试基础问答场景
    user_input = "今天天气怎么样？有什么好的建议吗？"
    
    print(f"\n🎯 测试用户输入:")
    print(f"{user_input}")
    
    print("\n🤖 正在调用LLM进行Just Talk...")
    print("请稍候，这可能需要几秒钟...")
    
    try:
        # 调用just_talk函数
        result = llm_just_talk(user_input)
        
        print("\n✅ Just Talk调用成功!")
        print(f"回复内容: {result.just_talk_output}")
        
        # 验证结果
        if result.just_talk_output and len(result.just_talk_output.strip()) > 0:
            print("✅ 回复内容有效: 生成了非空回复")
        else:
            print("❌ 回复内容无效: 回复为空")
        
        
        return result
        
    except Exception as e:
        print(f"❌ Just Talk调用失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return None


def test_different_talk_scenarios():
    """测试不同Just Talk场景"""
    print("\n" + "=" * 80)
    print("测试不同Just Talk场景")
    print("=" * 80)
    
    # 场景1：工作相关问题
    print("\n💼 场景1: 工作相关问题")
    work_input = "我在工作中遇到了一个难题，感觉压力很大，有什么好的建议吗？"
    
    try:
        result1 = llm_just_talk(work_input)
        print(f"工作问题回复: {result1.just_talk_output}...")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：生活闲聊
    print("\n💬 场景2: 生活闲聊")
    life_input = "最近想学一个新的兴趣爱好，你觉得学什么比较好？"
    
    try:
        result2 = llm_just_talk(life_input)
        print(f"生活闲聊回复: {result2.just_talk_output}...")
    except Exception as e:
        print(f"场景2测试失败: {e}")
    
    # 场景3：技术问题咨询
    print("\n🔧 场景3: 技术问题咨询")
    tech_input = "Python中如何处理异常比较好？能给个简单的例子吗？"
    
    try:
        result3 = llm_just_talk(tech_input)
        print(f"技术问题回复: {result3.just_talk_output}...")
    except Exception as e:
        print(f"场景3测试失败: {e}")
    
    # 场景4：情感支持
    print("\n❤️ 场景4: 情感支持")
    emotion_input = "今天心情不太好，感觉有点沮丧，能聊聊吗？"
    
    try:
        result4 = llm_just_talk(emotion_input)
        print(f"情感支持回复: {result4.just_talk_output}...")
    except Exception as e:
        print(f"场景4测试失败: {e}")
    
    # 场景5：创意讨论
    print("\n💡 场景5: 创意讨论")
    creative_input = "我想写一个有趣的故事，但是没有灵感，你能帮我想想吗？"
    
    try:
        result5 = llm_just_talk(creative_input)
        print(f"创意讨论回复: {result5.just_talk_output}...")
    except Exception as e:
        print(f"场景5测试失败: {e}")


def test_simple_edge_cases():
    """测试简单的边界情况"""
    print("\n" + "=" * 80)
    print("测试简单边界情况")
    print("=" * 80)
    
    # 边界情况1：很短的输入
    print("\n📝 边界情况1: 很短的输入")
    short_input = "你好"
    
    try:
        result1 = llm_just_talk(short_input)
        print(f"短输入回复: {result1.just_talk_output}...")
    except Exception as e:
        print(f"边界情况1测试失败: {e}")
    
    # 边界情况2：问号结尾的问题
    print("\n❓ 边界情况2: 问号结尾的问题")
    question_input = "什么是人工智能？"
    
    try:
        result2 = llm_just_talk(question_input)
        print(f"问题回复: {result2.just_talk_output}...")
    except Exception as e:
        print(f"边界情况2测试失败: {e}")
    
    # 边界情况3：感叹句
    print("\n❗ 边界情况3: 感叹句")
    exclaim_input = "今天真是太棒了！"
    
    try:
        result3 = llm_just_talk(exclaim_input)
        print(f"感叹句回复: {result3.just_talk_output}...")
    except Exception as e:
        print(f"边界情况3测试失败: {e}")
    
    # 边界情况4：包含表情符号
    print("\n😊 边界情况4: 包含表情符号")
    emoji_input = "今天心情很好 😊 有什么推荐的吗？"
    
    try:
        result4 = llm_just_talk(emoji_input)
        print(f"表情符号回复: {result4.just_talk_output}...")
    except Exception as e:
        print(f"边界情况4测试失败: {e}")


if __name__ == "__main__":
    # 运行基础功能测试
    result = test_real_llm_just_talk()
    
    # 如果基础测试成功，运行其他测试
    if result is not None:
        test_different_talk_scenarios()
        test_simple_edge_cases()
    
    print("\n" + "=" * 80)
    print("Just Talk功能测试完成")
    print("=" * 80)