"""数据存储客户端

本文件定义了LangGraph存储的封装客户端，提供统一的数据访问接口。

业务背景：系统需要从LangGraph存储中读取和写入各种业务数据，
包括员工信息、客户信息、聊天记录、订单信息等。

核心功能：
1. 封装LangGraph store的基本操作
2. 提供类型安全的数据访问方法
3. 处理数据格式转换（Item -> Dict）
4. 实现命名空间隔离，避免数据冲突

命名空间设计：
- ("employee",): 员工信息
- ("tags_setting",): 标签设置
- ("external_user", follow_user_id): 外部客户信息（按跟进人隔离）
- ("external_user_profile", follow_user_id): 客户画像（按跟进人隔离）
- ("wxqy_msg", from_to_sorted_key): 企业微信聊天消息
- ("wxkf_msg", external_id): 微信客服消息
- ("wxxd_order", union_id): 微信小程序订单
"""

# 导入LangGraph存储配置
from langgraph.config import get_store
# 导入调试装饰器
from utils.debug_aspect import debug
# 导入类型定义
from typing import List, Dict, Any, Optional
# 导入LangGraph存储基类
from langgraph.store.base import SearchItem, Item

class StoreClient:
    """
    LangGraph存储客户端封装类
    
    提供统一的业务数据访问接口，封装底层存储操作，
    实现数据的增删改查功能。
    """
    
    def __init__(self):
        """初始化存储客户端"""
        # 获取LangGraph全局存储实例
        self.store = get_store()

    # ==================== 辅助工具方法 ====================
    
    def item2dict(self, item: Item) -> Dict[str, Any]:
        """
        将LangGraph存储的Item对象转换为字典
        
        Args:
            item: LangGraph存储的Item对象
            
        Returns:
            字典形式的数据，如果item为空返回空字典
        """
        if not item:
            return {}
        # 如果值本身是字典，返回副本避免修改原值
        if isinstance(item.value, dict):
            return item.value.copy()
        return item.value

    def search_items_to_dict_list(self, searchitems: List[SearchItem]) -> List[Dict[str, Any]]:
        """
        将搜索结果列表转换为字典列表
        
        Args:
            searchitems: LangGraph搜索结果列表
            
        Returns:
            字典列表，如果输入为空返回空列表
        """
        if not searchitems:
            return []
        return [self.item2dict(item) for item in searchitems]


    # ==================== 通用方法 ====================
    
    @debug
    def get_item(self, namespace: tuple, key: str) -> Dict[str, Any]:
        """
        根据命名空间和键获取数据
        
        Args:
            namespace: 命名空间元组
            key: 数据键
            
        Returns:
            字典形式的数据
        """
        item = self.store.get(namespace, key)
        return self.item2dict(item)

    @debug
    def get_all_namespaces(self, limit: int = 100) -> list:
        """
        获取所有命名空间
        
        Args:
            limit: 返回数量限制，默认100
            
        Returns:
            命名空间列表
        """
        return self.store.list_namespaces(limit=limit)

    # ==================== 员工信息操作 ====================

    @debug
    def get_employee_by_user_id(self, user_id: str) -> Dict[str, Any]:
        """
        根据用户ID获取员工信息
        
        Args:
            user_id: 员工的企业微信用户ID
            
        Returns:
            员工信息字典，包含user_id、name等字段
        """
        if not user_id:
            return {}
        # 命名空间: ("employee",)
        item = self.store.get(("employee",), user_id)
        return self.item2dict(item)

    @debug
    def list_all_employee(self) -> List[Dict[str, Any]]:
        """
        获取所有员工列表
        
        Returns:
            员工信息列表
        """
        namespace = ("employee",)
        search_result = self.store.search(namespace)
        return self.search_items_to_dict_list(search_result)

    # ==================== 标签信息操作 ====================

    @debug
    def get_tags_setting_by_tag_id(self, tag_id: str) -> Dict[str, Any]:
        """
        根据标签ID获取标签设置详情
        
        Args:
            tag_id: 标签唯一标识
            
        Returns:
            标签信息字典，包含tag_id、tag_name等字段
        """
        if not tag_id:
            return {}
        item = self.store.get(("tags_setting",), tag_id)
        return self.item2dict(item)

    @debug
    def list_all_tags_setting(self) -> List[Dict[str, Any]]:
        """
        获取所有标签设置（排除已删除的）
        
        Returns:
            标签设置列表
        """
        namespace = ("tags_setting",)
        # 过滤条件：未删除的标签
        filter = {"deleted": False}
        search_result = self.store.search(namespace, filter=filter)
        return self.search_items_to_dict_list(search_result)


    # ==================== 外部客户信息操作 ====================
    
    @debug
    def get_external_user_by_external_id(self, external_id: str, follow_user_id: str) -> Dict[str, Any]:
        """
        根据外部客户ID获取客户信息
        
        命名空间设计：("external_user", follow_user_id)
        通过follow_user_id隔离不同销售人员的客户数据，确保数据安全性。
        
        Args:
            external_id: 外部客户ID（企业微信外部联系人ID）
            follow_user_id: 跟进该客户的员工ID
            
        Returns:
            客户信息字典，包含external_id、union_id、follow_user_id、nick_name等字段
        """
        if not external_id or not follow_user_id:
            return {}

        # 命名空间包含follow_user_id，实现数据隔离
        namespace = ("external_user", follow_user_id)
        key = external_id
        item = self.store.get(namespace, key)
        return self.item2dict(item)

    @debug
    def get_external_user_tag_by_external_id(self, external_id: str, follow_user_id: str) -> List[Dict[str, Any]]:
        """
        根据外部客户ID获取客户标签详情
        
        业务逻辑：先获取客户信息中的标签ID列表，再逐个获取标签详情。
        
        Args:
            external_id: 外部客户ID
            follow_user_id: 跟进该客户的员工ID
            
        Returns:
            标签详情列表
        """
        # 先获取客户基本信息
        external_user = self.get_external_user_by_external_id(external_id, follow_user_id)
        # 获取标签ID列表
        tag_ids = external_user.get("tags", [])

        tag_details = []
        
        # 逐个获取标签详情
        for tag_id in tag_ids:
            tag = self.get_tags_setting_by_tag_id(tag_id)
            if tag: 
                tag_details.append(tag)

        return tag_details

    @debug
    def upsert_external_user_tag_by_external_id(self, external_id: str, follow_user_id: str, tag_ids: List[str]) -> bool:
        """
        更新客户标签
        
        Args:
            external_id: 外部客户ID
            follow_user_id: 跟进该客户的员工ID
            tag_ids: 更新后的标签ID列表
            
        Returns:
            是否更新成功
        """
        if not external_id or not follow_user_id:
            return False

        if not tag_ids:
            tag_ids = []

        # 获取客户信息
        external_user = self.get_external_user_by_external_id(external_id, follow_user_id)

        if not external_user:
            return False
        
        # 更新标签列表
        external_user["tags"] = tag_ids

        # 保存到存储
        namespace = ("external_user", follow_user_id)
        key = external_id
        self.store.put(namespace, key, external_user)

        return True

    @debug
    def get_profile_by_external_id(self, external_id: str, follow_user_id: str) -> Dict[str, Any]:
        """
        根据外部客户ID获取客户画像
        
        Args:
            external_id: 外部客户ID
            follow_user_id: 跟进该客户的员工ID
            
        Returns:
            客户画像字典
        """
        if not external_id or not follow_user_id:
            return {}

        namespace = ("external_user_profile", follow_user_id)
        key = external_id
        item = self.store.get(namespace, key)
        return self.item2dict(item)

    @debug
    def upsert_external_user_profile(self, external_id: str, follow_user_id: str, profile: Dict[str, Any]) -> bool:
        """
        更新客户画像
        
        Args:
            external_id: 外部客户ID
            follow_user_id: 跟进该客户的员工ID
            profile: 客户画像数据
            
        Returns:
            是否更新成功
        """
        if not external_id or not follow_user_id:
            return False

        namespace = ("external_user_profile", follow_user_id)
        key = external_id
        self.store.put(namespace, key, profile)
        
        return True

    # ==================== 聊天消息操作 ====================
    
    @debug
    def list_last_wxqy_msg(self, external_id: str, follow_user_id: str, after_yyyy_mm_dd: Optional[str] = None, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """
        获取员工与客户的近期聊天消息
        
        命名空间设计：("wxqy_msg", from_to_sorted_key)
        from_to_sorted_key = sorted([external_id, follow_user_id])，确保双向消息都能被检索到。
        
        Args:
            external_id: 外部客户ID
            follow_user_id: 员工ID
            after_yyyy_mm_dd: 过滤日期（格式：YYYYMMDD），只返回该日期之后的消息
            limit: 返回数量限制，默认100
            
        Returns:
            聊天消息列表，包含from_id、content、msg_time等字段
        """
        if not external_id or not follow_user_id:
            return []

        # 排序后拼接，确保external_id和follow_user_id顺序不影响检索
        from_to_sorted_key = "".join(sorted([external_id, follow_user_id]))
        namespace = ("wxqy_msg", from_to_sorted_key)
        
        # 设置日期过滤条件
        if after_yyyy_mm_dd:
            filter = {"YYYYMMDD": {"$gte": after_yyyy_mm_dd}}
        else:
            filter = {}
            
        search_result = self.store.search(namespace, filter=filter, limit=limit)
        return self.search_items_to_dict_list(search_result)


    # ==================== 微信客服消息操作 ====================
    
    @debug
    def list_last_wxkf_msg(self, external_id: str, after_yyyy_mm_dd: Optional[str] = None, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """
        获取客户与微信客服的近期聊天消息
        
        Args:
            external_id: 外部客户ID
            after_yyyy_mm_dd: 过滤日期（格式：YYYYMMDD）
            limit: 返回数量限制，默认100
            
        Returns:
            客服聊天消息列表
        """
        if not external_id:
            return []

        namespace = ("wxkf_msg", external_id)
        
        if after_yyyy_mm_dd:
            filter = {"YYYYMMDD": {"$gte": after_yyyy_mm_dd}}
        else:
            filter = {}
            
        search_result = self.store.search(namespace, filter=filter, limit=limit)
        return self.search_items_to_dict_list(search_result)


    # ==================== 订单信息操作 ====================
    
    @debug
    def list_wxxd_order_by_union_id(self, union_id: str, after_yyyy_mm_dd: Optional[str] = None, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """
        根据UnionID获取客户订单列表
        
        UnionID是微信开放平台统一用户标识，可跨应用使用。
        
        Args:
            union_id: 微信UnionID
            after_yyyy_mm_dd: 过滤日期（格式：YYYYMMDD）
            limit: 返回数量限制，默认100
            
        Returns:
            订单列表，包含order_id、order_products、order_create_time等字段
        """
        if not union_id:
            return []

        namespace = ("wxxd_order", union_id)

        if after_yyyy_mm_dd:
            filter = {"YYYYMMDD": {"$gte": after_yyyy_mm_dd}}
        else:
            filter = {}

        search_result = self.store.search(namespace, filter=filter, limit=limit)
        return self.search_items_to_dict_list(search_result)