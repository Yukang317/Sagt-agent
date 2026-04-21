import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append("/root/project/sagt_202509/sagt_agent/src")

from models.sagt_models import (
    ReplySuggestion, ChatHistory, CustomerInfo, ChatMessage, EmployeeInfo
)

from models.sagt_models import (
    CustomerProfile, ChatHistory, 
    KFChatHistory, OrderHistory, TagInfo, ChatMessage, OrderInfo, ProfileItem, CustomerTags
)

from models.sagt_models import (
    TagSetting, TagSuggestion, CustomerTags, ChatHistory, 
    KFChatHistory, OrderHistory, TagInfo, ChatMessage, OrderInfo
)

print("="*50)
print(ReplySuggestion.get_schema_json())
print("-"*50)
print(ReplySuggestion.get_example_json())

print("="*50)
print(CustomerProfile.get_schema_json())
print("-"*50)
print(CustomerProfile.get_example_json())

print("="*50)
print(TagSuggestion.get_schema_json())
print("-"*50)
print(TagSuggestion.get_example_json())

print("="*50)