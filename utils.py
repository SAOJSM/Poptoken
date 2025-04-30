#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
utils.py - 工具函數模組
提供配置讀取、HTTP請求處理等功能
"""

import configparser
import logging
import requests
import json
import time
import sys
from typing import Dict, Any, Optional, Tuple

# 設定日誌格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def read_config(config_path: str = 'config.ini') -> configparser.ConfigParser:
    """
    讀取配置文件

    Args:
        config_path: 配置文件路徑

    Returns:
        配置對象
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_path, encoding='utf-8')
        return config
    except Exception as e:
        logger.error(f"讀取配置文件失敗: {e}")
        raise

def get_headers() -> Dict[str, str]:
    """
    獲取HTTP請求頭

    Returns:
        HTTP請求頭字典
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/json',
        'Origin': 'https://www.popkontv.com',
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
        data: 請求數據
        headers: 請求頭
        timeout: 超時時間(秒)
        allow_redirects: 是否允許重定向

    Returns:
        HTTP響應對象
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
            # 根據 Content-Type 決定如何發送數據
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
                # 默認使用表單格式
                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=allow_redirects
                )

            # 輸出請求詳細信息以幫助調試
            logger.debug(f"POST 請求到 {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Data: {data}")
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

        # 輸出響應狀態碼和內容
        logger.debug(f"響應狀態碼: {response.status_code}")
        logger.debug(f"響應內容: {response.text[:500]}..." if len(response.text) > 500 else f"響應內容: {response.text}")

        return response
    except requests.RequestException as e:
        logger.error(f"請求失敗: {e}")
        raise

def extract_token_from_response(response: requests.Response) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    從響應中提取token

    Args:
        response: HTTP響應對象

    Returns:
        (成功標誌, token字符串, 響應數據)
    """
    try:
        if response.status_code != 200:
            logger.error(f"請求失敗，狀態碼: {response.status_code}")
            logger.error(f"響應內容: {response.text}")
            return False, None, None

        data = response.json()
        logger.debug(f"響應數據: {json.dumps(data, ensure_ascii=False, indent=2)}")

        # 檢查響應中是否包含token
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
            logger.warning("響應中未找到token")
            logger.warning(f"完整響應數據: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return False, None, data
    except Exception as e:
        logger.error(f"解析響應失敗: {e}")
        logger.error(f"原始響應內容: {response.text}")
        return False, None, None
