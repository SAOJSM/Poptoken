#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
token_manager.py - Token 管理模組
提供 token 的儲存、讀取和驗證功能
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Token 文件路徑
TOKEN_FILE = "token.json"

def save_token(token: str, user_info: Dict[str, Any], expiry: Optional[int] = None) -> bool:
    """
    儲存 token 到文件
    
    Args:
        token: 登入獲取的 token 字符串
        user_info: 用戶信息字典
        expiry: token 過期時間戳（秒），如果為 None 則默認為 24 小時
        
    Returns:
        儲存是否成功
    """
    try:
        # 如果沒有提供過期時間，默認設置為 24 小時後
        if expiry is None:
            expiry = int(time.time()) + 24 * 60 * 60
            
        # 創建 token 數據結構
        token_data = {
            "token": token,
            "created_at": int(time.time()),
            "expires_at": expiry,
            "user_info": user_info
        }
        
        # 將數據寫入文件
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
            
        print(f"Token 已成功儲存到 {TOKEN_FILE}")
        return True
    except Exception as e:
        print(f"儲存 token 時發生錯誤: {e}")
        return False

def load_token() -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    從文件讀取 token
    
    Returns:
        (成功標誌, token字符串, token數據)
    """
    try:
        # 檢查文件是否存在
        if not os.path.exists(TOKEN_FILE):
            print(f"Token 文件不存在: {TOKEN_FILE}")
            return False, None, None
            
        # 讀取文件
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
            
        # 檢查 token 是否過期
        current_time = int(time.time())
        if token_data["expires_at"] < current_time:
            print(f"Token 已過期，過期時間: {datetime.fromtimestamp(token_data['expires_at']).strftime('%Y-%m-%d %H:%M:%S')}")
            return False, None, token_data
            
        return True, token_data["token"], token_data
    except Exception as e:
        print(f"讀取 token 時發生錯誤: {e}")
        return False, None, None

def is_token_valid() -> bool:
    """
    檢查 token 是否有效
    
    Returns:
        token 是否有效
    """
    valid, _, _ = load_token()
    return valid

def get_token_info() -> Optional[Dict[str, Any]]:
    """
    獲取 token 的詳細信息
    
    Returns:
        token 詳細信息字典，如果不存在或已過期則返回 None
    """
    valid, _, token_data = load_token()
    if valid and token_data:
        # 計算剩餘有效時間
        remaining_time = token_data["expires_at"] - int(time.time())
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # 添加可讀的時間信息
        token_data["created_at_readable"] = datetime.fromtimestamp(token_data["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
        token_data["expires_at_readable"] = datetime.fromtimestamp(token_data["expires_at"]).strftime('%Y-%m-%d %H:%M:%S')
        token_data["remaining_time"] = f"{int(hours)}小時 {int(minutes)}分鐘 {int(seconds)}秒"
        
        return token_data
    return None

def delete_token() -> bool:
    """
    刪除 token 文件
    
    Returns:
        刪除是否成功
    """
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print(f"Token 文件已刪除: {TOKEN_FILE}")
            return True
        return False
    except Exception as e:
        print(f"刪除 token 文件時發生錯誤: {e}")
        return False

if __name__ == "__main__":
    # 測試代碼
    token_info = get_token_info()
    if token_info:
        print(f"當前 token 信息:")
        print(f"用戶名: {token_info['user_info'].get('signId', 'N/A')}")
        print(f"昵稱: {token_info['user_info'].get('nickName', 'N/A')}")
        print(f"創建時間: {token_info['created_at_readable']}")
        print(f"過期時間: {token_info['expires_at_readable']}")
        print(f"剩餘時間: {token_info['remaining_time']}")
    else:
        print("沒有有效的 token 或 token 已過期")
