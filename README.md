# PopkonTV 登入 Token 獲取工具

這是一個用於獲取 PopkonTV (https://www.popkontv.com/) 登入 token 的 Python 工具，可用於測試網站登入接口的有效性。

## 功能特點

- 自動獲取登入 token
- 支持配置文件設置帳號密碼
- 詳細的日誌輸出
- 錯誤處理和重試機制

## 系統需求

- Python 3.6 或更高版本
- 需要安裝的套件：requests

## 安裝步驟

1. 克隆或下載此專案到本地
2. 安裝所需套件：

```bash
pip install requests
```

## 使用方法

1. 編輯 `config.ini` 文件，填入您的帳號和密碼：

```ini
[帳號資訊]
username = 您的帳號
password = 您的密碼

[設定]
# 是否顯示詳細日誌
verbose = True
# 登入嘗試次數
max_retries = 3
# 請求超時時間(秒)
timeout = 10
```

2. 執行主程式：

```bash
python main.py
```

3. 程式將嘗試登入並獲取 token，結果會顯示在控制台中。

4. 獲取到的 token 會自動儲存到 `token.json` 文件中，下次執行時如果 token 仍然有效，程式會詢問是否需要重新登入。

## 文件說明

- `config.ini`：配置文件，用於設置帳號密碼和其他參數
- `main.py`：主程式，處理登入邏輯和獲取 token
- `utils.py`：工具函數，提供配置讀取、HTTP 請求等功能
- `token_manager.py`： Token 管理模組，提供 token 的儲存、讀取和驗證功能
- `token.json`：儲存獲取到的 token 和相關信息（程式自動生成）
- `README.md`：本說明文件

## 注意事項

- 本工具僅用於測試和學習目的
- 請勿用於任何非法用途
- 請妥善保管您的帳號密碼信息
- 程式使用固定的 Authorization 字符串，如果失效請更新 main.py 中的 AUTHORIZATION 變量

## 常見問題

### 登入失敗怎麼辦？

- 檢查您的帳號密碼是否正確
- 確認網路連接是否正常
- 查看日誌輸出，了解具體錯誤信息

### 如何獲取更詳細的日誌？

在 `config.ini` 中將 `verbose` 設置為 `True`。

### 如何查看已儲存的 token 信息？

直接執行 `token_manager.py` 文件：

```bash
python token_manager.py
```

程式會顯示目前儲存的 token 信息，包括用戶名、暱稱、創建時間、過期時間和剩餘時間。

## 授權協議

本專案採用 MIT 授權協議。
