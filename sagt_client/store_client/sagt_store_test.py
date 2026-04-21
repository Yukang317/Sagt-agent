#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 主要是测试`sagt_store_api.py` 中的各种功能，提供数据初始化和清理功能
# - 作为 `sagt_store_api.py` 的测试工具，验证其功能是否正常
# - 提供了数据初始化和清理功能，方便测试环境的搭建和维护


"""
SagtStoreAPI 真实环境数据初始化脚本


注意：
- 本脚本会创建真实数据，请在测试环境中运行
- 支持清理模式，可以删除初始化的数据
- 数据使用特殊前缀以便识别和管理
"""

from typing import Optional, List
from pprint import pprint  # 用于美化打印输出
from dotenv import load_dotenv  # 用于加载环境变量
import os  # 用于操作系统相关功能

from sagt_store_api import create_sagt_store_api  # 导入创建 SagtStoreAPI 实例的工厂函数


load_dotenv()  # 加载 .env 文件中的环境变量

# 从环境变量中获取配置信息
SAGT_SERVER_URL = os.getenv("SAGT_SERVER_URL")  # SAGT 服务器 URL
SAGT_USER_ID = os.getenv("SAGT_USER_ID")  # SAGT 用户 ID
SAGT_USER_PASSWORD = os.getenv("SAGT_USER_PASSWORD")  # SAGT 用户密码





class DataInitializer:
    """数据初始化器
    
    负责 SAGT 系统数据的初始化、清理和展示
    """
    
    store_client = None  # 存储 SagtStoreAPI 实例

    def __init__(self, server_url: str, user_id: str, password: str):
        """初始化数据初始化器
        
        Args:
            server_url: SAGT 服务器 URL
            user_id: SAGT 用户 ID
            password: SAGT 用户密码
        """
        # 创建 SagtStoreAPI 实例，用于与存储服务交互
        self.store_client = create_sagt_store_api(server_url, user_id, password)
     
        

    def test_cleanup(self, prefix: Optional[List[str]] = None):
        """测试清理，删除初始化的数据
        
        Args:
            prefix: 命名空间前缀列表，用于过滤要清理的命名空间
                    例如：["external_user"] 表示只清理 external_user 相关的命名空间
                    默认为 None，表示清理所有命名空间
                    支持通配符，如 ["*"] 表示所有命名空间
        
        返回值：无（void）
        业务用途：
        - 用于测试环境中清理测试数据
        - 确保测试环境数据的一致性
        - 避免测试数据积累影响测试结果
        """
        
        # 获取指定前缀的所有命名空间
        namespaces = self.store_client.list_all_namespace(prefix=prefix).get("namespaces", [])
        # 打印获取到的命名空间列表
        pprint(namespaces)

        # 遍历每个命名空间
        for namespace in namespaces:
            pprint(50 * "-")  # 打印分隔线
            pprint(namespace)  # 打印当前命名空间
            
            # 搜索当前命名空间下的所有项目（最多200个）
            objs = self.store_client.search_items(namespace, limit = 200).get("items", [])
            
            # 遍历每个项目并删除
            for obj in objs:
                pprint(50 * "=")  # 打印分隔线
                pprint(obj)  # 打印当前项目信息
                # 删除当前项目
                self.store_client.delete_item(namespace, obj.get("key"))
        

    def show_all(self, prefix: Optional[List[str]] = None):
        """显示所有数据
        
        Args:
            prefix: 命名空间前缀列表，用于过滤要显示的命名空间
                    默认为 None，表示显示所有命名空间
        """
        
        # 获取指定前缀的所有命名空间
        namespaces = self.store_client.list_all_namespace(prefix=prefix).get("namespaces", [])
        # 打印获取到的命名空间列表
        pprint(namespaces)

        # 遍历每个命名空间
        for namespace in namespaces:
            pprint(50 * "-")  # 打印分隔线
            pprint(namespace)  # 打印当前命名空间
            
            # 搜索当前命名空间下的所有项目（最多100个）
            objs = self.store_client.search_items(namespace = namespace, limit = 100).get("items", [])
            # 打印项目数量
            pprint("数量：" + str(len(objs)))
            
            # 遍历并打印每个项目
            for obj in objs:
                pprint(50 * "=")  # 打印分隔线
                pprint(obj)  # 打印当前项目信息

    def show_namespace(self, prefix: Optional[list[str]] = None, suffix: Optional[list[str]] = None):
        """显示命名空间
        
        Args:
            prefix: 命名空间前缀列表，用于过滤要显示的命名空间
            suffix: 命名空间后缀列表，用于过滤要显示的命名空间
        """
        # 获取指定前缀和后缀的所有命名空间
        namespaces = self.store_client.list_all_namespace(prefix=prefix, suffix=suffix).get("namespaces", [])
        # 遍历并打印每个命名空间
        for namespace in namespaces:
            pprint(namespace)

    



def show_all(prefix):
    """显示所有数据的入口函数
    
    Args:
        prefix: 命名空间前缀列表
    """
    # 创建数据初始化器实例
    initializer = DataInitializer(SAGT_SERVER_URL, SAGT_USER_ID, SAGT_USER_PASSWORD)
    #initializer.show_all(prefix=["external_user"])  # 示例：只显示 external_user 相关数据
    initializer.show_all(prefix=prefix)  # 调用 show_all 方法显示数据

def test_cleanup(prefix):
    """清理数据的入口函数
    
    Args:
        prefix: 命名空间前缀列表
    """
    # 创建数据初始化器实例
    initializer = DataInitializer(SAGT_SERVER_URL, SAGT_USER_ID, SAGT_USER_PASSWORD)
    # 调用 test_cleanup 方法清理数据
    initializer.test_cleanup(prefix=prefix)

def show_namespace(prefix):
    """显示命名空间的入口函数
    
    Args:
        prefix: 命名空间前缀列表
    """
    # 创建数据初始化器实例
    initializer = DataInitializer(SAGT_SERVER_URL, SAGT_USER_ID, SAGT_USER_PASSWORD)
    # 调用 show_namespace 方法显示命名空间
    initializer.show_namespace(prefix=prefix)
    #initializer.show_namespace(prefix=["external_user","*"])  # 示例：使用通配符



if __name__ == "__main__":
    #test_cleanup(prefix=["tags_setting"])  # 示例：清理 tags_setting 命名空间的数据
    #show_namespace(prefix=["external_user"])  # 示例：显示 external_user 相关的命名空间
    show_all(prefix=["*"])  # 默认：显示所有命名空间的数据