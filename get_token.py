#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
get_token.py - Popkontv Token 取得工具 (整合版)
用於取得 popkontv.com 的登入 token 並存入 LiveRecorder 設定檔
"""

import sys
import json
import logging
import time
import base64
import os
import re
import configparser
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# 設定記錄格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 登入API端點
LOGIN_API_URL = "https://www.popkontv.com/api/proxy/member/v1/login"

# 自訂的 Authorization 字串
AUTHORIZATION = "Basic FpAhe6mh8Qtz116OENBmRddbYVirNKasktdXQiuHfm88zRaFydTsFy63tzkdZY0u"

# LiveRecorder 設定檔路徑
LIVERECORDER_CONFIG_PATH = '/root/LiveRecorder-1/config/config.ini'

def read_config(config_path: str = 'config.ini') -> configparser.ConfigParser:
    """
    讀取設定檔

    Args:
        config_path: 設定檔路徑

    Returns:
        設定物件
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_path, encoding='utf-8')
        return config
    except Exception as e:
        logger.error(f"讀取設定檔失敗: {e}")
        raise

def get_headers() -> Dict[str, str]:
    """
    取得HTTP請求標頭

    Returns:
        HTTP請求標頭字典
    """
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Authorization': AUTHORIZATION,
        'Content-Type': 'application/json',
        'Origin': 'https://www.popkontv.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Referer': 'https://www.popkontv.com/not-found',
    }

def make_request(
    url: str,
    method: str = 'GET',
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
    allow_redirects: bool = True
) -> requests.Response:
    """
    發送HTTP請求

    Args:
        url: 請求URL
        method: 請求方法 (GET, POST等)
        data: 請求資料
        headers: 請求標頭
        timeout: 逾時時間(秒)
        allow_redirects: 是否允許重新導向

    Returns:
        HTTP回應物件
    """
    if headers is None:
        headers = get_headers()

    try:
        if method.upper() == 'GET':
            response = requests.get(
                url,
                params=data,
                headers=headers,
                timeout=timeout,
                allow_redirects=allow_redirects
            )
        elif method.upper() == 'POST':
            # 根據 Content-Type 決定如何發送資料
            content_type = headers.get('Content-Type', '')

            if content_type.startswith('application/json'):
                # JSON 格式
                response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=allow_redirects
                )
            elif content_type.startswith('application/x-www-form-urlencoded'):
                # 表單格式
                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=allow_redirects
                )
            else:
                # 預設使用表單格式
                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=allow_redirects
                )

            # 輸出請求詳細資訊以幫助除錯
            logger.debug(f"POST 請求到 {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Data: {data}")
        else:
            raise ValueError(f"不支援的HTTP方法: {method}")

        # 輸出回應狀態碼和內容
        logger.debug(f"回應狀態碼: {response.status_code}")
        logger.debug(f"回應內容: {response.text[:500]}..." if len(response.text) > 500 else f"回應內容: {response.text}")

        return response
    except requests.RequestException as e:
        logger.error(f"請求失敗: {e}")
        raise

def extract_token_from_response(response: requests.Response) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    從回應中提取token

    Args:
        response: HTTP回應物件

    Returns:
        (成功標誌, token字串, 回應資料)
    """
    try:
        if response.status_code != 200:
            logger.error(f"請求失敗，狀態碼: {response.status_code}")
            logger.error(f"回應內容: {response.text}")
            return False, None, None

        data = response.json()
        logger.debug(f"回應資料: {json.dumps(data, ensure_ascii=False, indent=2)}")

        # 檢查回應中是否包含token
        if 'token' in data:
            return True, data['token'], data
        elif 'data' in data and isinstance(data['data'], dict):
            if 'token' in data['data']:
                # PopkonTV 的標準token格式
                return True, data['data']['token'], data
            elif 'accessToken' in data['data']:
                # 某些平台的token格式
                return True, data['data']['accessToken'], data
        else:
            logger.warning("回應中未找到token")
            logger.warning(f"完整回應資料: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return False, None, data
    except Exception as e:
        logger.error(f"解析回應失敗: {e}")
        logger.error(f"原始回應內容: {response.text}")
        return False, None, None

def save_token(token: str, user_info: Dict[str, Any], expiry: Optional[int] = None) -> bool:
    """
    儲存 token 到 LiveRecorder 設定檔

    Args:
        token: 登入獲取的 token 字串
        user_info: 使用者資訊字典
        expiry: token 過期時間戳（秒），不使用

    Returns:
        儲存是否成功
    """
    try:
        # 將 token 寫入到 LiveRecorder 設定檔
        return update_liverecorder_config(token)
    except Exception as e:
        logger.error(f"儲存 token 時發生錯誤: {e}")
        return False

def update_liverecorder_config(token: str) -> bool:
    """
    將 token 更新到 LiveRecorder 設定檔

    Args:
        token: 要寫入的 token 字串

    Returns:
        更新是否成功
    """
    try:
        # 檢查設定檔是否存在
        if not os.path.exists(LIVERECORDER_CONFIG_PATH):
            logger.warning(f"LiveRecorder 設定檔不存在: {LIVERECORDER_CONFIG_PATH}")
            logger.warning("請確認路徑是否正確，或者手動建立該檔案")
            return False

        logger.info(f"正在更新 LiveRecorder 設定檔: {LIVERECORDER_CONFIG_PATH}")

        # 讀取現有設定檔
        with open(LIVERECORDER_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_content = f.read()

        # 檢查是否存在 popkontv_token 行
        if 'popkontv_token' not in config_content:
            logger.warning("設定檔中未找到 popkontv_token 行，將新增該行")
            config_content += f"\npopkontv_token = {token}\n"
            new_config_content = config_content
        else:
            # 替換 popkontv_token 行
            new_config_content = re.sub(r'popkontv_token = .*', f'popkontv_token = {token}', config_content)

        # 寫回檔案
        with open(LIVERECORDER_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(new_config_content)

        logger.info(f"Token 已成功存入: {LIVERECORDER_CONFIG_PATH}")
        logger.info(f"Token 值: {token[:10]}...{token[-10:]} (已截斷顯示)")
        return True
    except Exception as e:
        logger.error(f"更新 LiveRecorder 設定檔時發生錯誤: {e}")
        return False

def login(username: str, password: str, timeout: int = 10) -> Optional[str]:
    """
    執行登入操作並取得token

    Args:
        username: 使用者名稱
        password: 密碼
        timeout: 請求逾時時間(秒)

    Returns:
        取得到的 token，如果失敗則返回 None
    """
    # 準備登入資料
    login_data = {
        'partnerCode': 'P-00001',  # 合作夥伴代碼
        'signId': username,        # 使用者名稱
        'signPwd': password,       # 密碼
    }

    logger.info(f"正在嘗試登入帳號: {username}")

    try:
        # 發送登入請求
        headers = get_headers()

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

            # 顯示完整回應資料（如果啟用了詳細記錄）
            if config.getboolean('設定', 'verbose'):
                logger.info(f"完整回應資料: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            # 分析 JWT token 以取得過期時間
            try:
                # JWT token 由三部分組成，以點分隔，第二部分是 payload
                token_parts = token.split('.')
                if len(token_parts) >= 2:
                    # 解碼 payload
                    payload = token_parts[1]
                    # 新增必要的填充使其長度為 4 的倍數
                    payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 != 0 else ''
                    # 解碼 base64
                    decoded_payload = base64.b64decode(payload).decode('utf-8')
                    # 解析 JSON
                    payload_data = json.loads(decoded_payload)
                    # 取得過期時間
                    expiry = payload_data.get('exp')
                else:
                    expiry = None
            except Exception as e:
                logger.warning(f"解析 token 過期時間失敗: {e}")
                expiry = None

            # 儲存 token 到 LiveRecorder 設定檔
            user_info = response_data.get('data', {})
            if save_token(token, user_info, expiry):
                logger.info(f"Token 已成功存入 LiveRecorder 設定檔")
            else:
                logger.warning(f"Token 取得成功，但存入 LiveRecorder 設定檔失敗")

            return token
        else:
            logger.error("登入失敗，未能取得token")
            if response_data:
                logger.error(f"回應資料: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return None

    except Exception as e:
        logger.error(f"登入過程中發生錯誤: {e}")
        return None

def main():
    """主函數"""
    try:
        # 讀取設定
        global config
        config = read_config()

        # 取得登入資訊
        username = config.get('帳號資訊', 'username')
        password = config.get('帳號資訊', 'password')
        timeout = config.getint('設定', 'timeout')
        max_retries = config.getint('設定', 'max_retries')

        # 檢查是否已設定使用者名稱和密碼
        if username == '您的帳號' or password == '您的密碼' or not username or not password:
            logger.error("請在config.ini中設定您的帳號和密碼")
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
            logger.info("成功取得 token 並存入 LiveRecorder 設定檔！")
            logger.info(f"設定檔路徑: {LIVERECORDER_CONFIG_PATH}")
            return 0
        else:
            logger.error(f"在 {max_retries} 次嘗試後仍未能成功登入")
            return 1

    except KeyboardInterrupt:
        logger.info("程式被使用者中斷")
        return 1
    except Exception as e:
        logger.error(f"程式執行過程中發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
