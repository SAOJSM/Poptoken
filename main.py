#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
main.py - 主程式
用於獲取 popkontv.com 的登入 token
"""

import sys
import json
import logging
import time
import base64
from utils import read_config, make_request, extract_token_from_response, logger
import token_manager

# 登入API端點
LOGIN_API_URL = "https://www.popkontv.com/api/proxy/member/v1/login"

# 自定義的 Authorization 字符串
AUTHORIZATION = "Basic FpAhe6mh8Qtz116OENBmRddbYVirNKasktdXQiuHfm88zRaFydTsFy63tzkdZY0u"

def login(username: str, password: str, timeout: int = 10) -> None:
    """
    執行登入操作並獲取token

    Args:
        username: 用戶名
        password: 密碼
        timeout: 請求超時時間(秒)
    """
    # 準備登入數據
    login_data = {
        'partnerCode': 'P-00001',  # 合作夥伴代碼
        'signId': username,        # 用戶名
        'signPwd': password,       # 密碼
    }

    logger.info(f"正在嘗試登入帳號: {username}")

    try:
        # 發送登入請求
        # 先創建一個包含正確請求頭的字典
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Authorization': AUTHORIZATION,
            'Content-Type': 'application/json',
            'Origin': 'https://www.popkontv.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            'Referer': 'https://www.popkontv.com/not-found',
        }

        response = make_request(
            url=LOGIN_API_URL,
            method="POST",
            data=login_data,
            headers=headers,
            timeout=timeout
        )

        # 提取token
        success, token, response_data = extract_token_from_response(response)

        if success and token:
            logger.info("登入成功！")
            logger.info(f"Token: {token}")

            # 顯示完整響應數據（如果啟用了詳細日誌）
            if config.getboolean('設定', 'verbose'):
                logger.info(f"完整響應數據: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            # 分析 JWT token 以獲取過期時間
            try:
                # JWT token 由三部分組成，以點分隔，第二部分是 payload
                token_parts = token.split('.')
                if len(token_parts) >= 2:
                    # 解碼 payload
                    payload = token_parts[1]
                    # 添加必要的填充使其長度為 4 的倍數
                    payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 != 0 else ''
                    # 解碼 base64
                    decoded_payload = base64.b64decode(payload).decode('utf-8')
                    # 解析 JSON
                    payload_data = json.loads(decoded_payload)
                    # 獲取過期時間
                    expiry = payload_data.get('exp')
                else:
                    expiry = None
            except Exception as e:
                logger.warning(f"解析 token 過期時間失敗: {e}")
                expiry = None

            # 儲存 token
            user_info = response_data.get('data', {})
            token_manager.save_token(token, user_info, expiry)

            return token
        else:
            logger.error("登入失敗，未能獲取token")
            if response_data:
                logger.error(f"響應數據: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return None

    except Exception as e:
        logger.error(f"登入過程中發生錯誤: {e}")
        return None

def main():
    """主函數"""
    try:
        # 讀取配置
        global config
        config = read_config()

        # 檢查是否已有有效的 token
        token_info = token_manager.get_token_info()
        if token_info:
            logger.info("發現有效的 token，無需重新登入")
            logger.info(f"用戶名: {token_info['user_info'].get('signId', 'N/A')}")
            logger.info(f"昵稱: {token_info['user_info'].get('nickName', 'N/A')}")
            logger.info(f"過期時間: {token_info['expires_at_readable']}")
            logger.info(f"剩餘時間: {token_info['remaining_time']}")

            # 詢問用戶是否要強制重新登入
            force_login = input("已有有效的 token，是否仍要重新登入？(y/n): ").strip().lower()
            if force_login != 'y':
                return 0
            else:
                logger.info("強制重新登入...")

        # 獲取登入信息
        username = config.get('帳號資訊', 'username')
        password = config.get('帳號資訊', 'password')
        timeout = config.getint('設定', 'timeout')
        max_retries = config.getint('設定', 'max_retries')

        # 檢查是否已設置用戶名和密碼
        if username == '您的帳號' or password == '您的密碼':
            logger.error("請在config.ini中設置您的帳號和密碼")
            sys.exit(1)

        # 嘗試登入
        retry_count = 0
        token = None

        while retry_count < max_retries and token is None:
            if retry_count > 0:
                logger.info(f"重試登入 ({retry_count}/{max_retries})...")

            token = login(username, password, timeout)
            retry_count += 1

        if token:
            logger.info("成功獲取token！")
            return 0
        else:
            logger.error(f"在 {max_retries} 次嘗試後仍未能成功登入")
            return 1

    except KeyboardInterrupt:
        logger.info("程式被用戶中斷")
        return 1
    except Exception as e:
        logger.error(f"程式執行過程中發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
