#!/bin/bash

# SBIR Skill 自動安裝腳本（Mac 版）- Enhanced v3
# 這個腳本會自動幫您安裝所有需要的東西
# 重要：不會覆蓋您現有的 Claude Desktop 設定

set -e  # 遇到錯誤立即停止

echo "=========================================="
echo "   SBIR Skill 自動安裝程式"
echo "=========================================="
echo ""

# 取得腳本所在目錄（處理路徑中的空格）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

echo "📁 工作目錄: $SCRIPT_DIR"
echo ""

# 檢查是否在正確的目錄
if [ ! -f "mcp-server/server.py" ]; then
    echo "❌ 錯誤：找不到 mcp-server/server.py"
    echo ""
    echo "請確認："
    echo "1. 您已經下載完整的專案"
    echo "2. 專案資料夾名稱是 sbir-grants"
    echo "3. 資料夾內有 mcp-server 子資料夾"
    echo ""
    echo "目前位置: $SCRIPT_DIR"
    exit 1
fi

echo "✅ 找到專案資料夾"
echo ""

# 步驟 1: 檢查 Python
echo "步驟 1/4: 檢查 Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ 找到 Python: $PYTHON_VERSION"
else
    echo "❌ 找不到 Python"
    echo ""
    echo "請先安裝 Python："
    echo "1. 前往 https://www.python.org/downloads/"
    echo "2. 下載 Python 3.10 或更新版本"
    echo "3. 安裝完成後，重新執行此腳本"
    exit 1
fi
echo ""

# 步驟 2: 建立虛擬環境與安裝依賴套件
echo "步驟 2/4: 建立虛擬環境與安裝套件..."
echo "這可能需要幾分鐘，請稍候..."

# 建立虛擬環境
if [ ! -d "venv" ]; then
    echo "正在建立虛擬環境..."
    if ! python3 -m venv venv; then
        echo "❌ 虛擬環境建立失敗"
        exit 1
    fi
fi

# 使用虛擬環境的 Python 安裝套件
echo "正在安裝依賴套件..."
if ! "$SCRIPT_DIR/venv/bin/python" -m pip install --upgrade pip --quiet; then
    echo "❌ pip 升級失敗"
    exit 1
fi

if ! "$SCRIPT_DIR/venv/bin/python" -m pip install mcp httpx pydantic --quiet; then
    echo "❌ 套件安裝失敗"
    echo "請檢查網路連線"
    exit 1
fi

echo "✅ 虛擬環境與套件安裝成功"
echo ""

# 步驟 3: 設定 Claude Desktop（安全合併，不覆蓋）
echo "步驟 3/4: 設定 Claude Desktop..."

CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
PYTHON_EXE="$SCRIPT_DIR/venv/bin/python"
SERVER_SCRIPT="$SCRIPT_DIR/mcp-server/server.py"

# 創建目錄（如果不存在）
mkdir -p "$CLAUDE_CONFIG_DIR"

# 如果設定檔已存在，先備份
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.bak"
    echo "ℹ️  已備份現有設定至 claude_desktop_config.json.bak"
fi

# 使用 Python 進行 JSON 合併（更可靠，不依賴 jq）
echo "正在更新設定檔..."

"$SCRIPT_DIR/venv/bin/python" << PYEOF
import json
import os
import sys

config_file = '''$CLAUDE_CONFIG_FILE'''
python_exe = '''$PYTHON_EXE'''
server_script = '''$SERVER_SCRIPT'''

try:
    # 讀取現有設定（如果存在）
    config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    config = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告：無法讀取現有設定，將創建新設定：{e}")
            config = {}

    # 確保 mcpServers 存在
    if 'mcpServers' not in config or config['mcpServers'] is None:
        config['mcpServers'] = {}

    # 添加或更新 sbir-data
    config['mcpServers']['sbir-data'] = {
        'command': python_exe,
        'args': [server_script]
    }

    # 寫入設定檔
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("設定檔已更新")
    sys.exit(0)

except Exception as e:
    print(f"錯誤：{e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo "✅ Claude Desktop 設定已安全更新"
    echo "   設定檔位置: $CLAUDE_CONFIG_FILE"
    echo "   已保留其他 MCP Server 設定"
else
    echo "❌ 設定檔更新失敗"
    exit 1
fi
echo ""

# 步驟 4: 完成
echo "步驟 4/4: 完成安裝"
echo ""
echo "=========================================="
echo "   🎉 安裝成功！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 重新啟動 Claude Desktop"
echo "   - 完全關閉 Claude（Command + Q）"
echo "   - 重新開啟 Claude"
echo ""
echo "2. 測試是否成功："
echo "   在 Claude 中輸入："
echo "   「請使用 MCP Server 查詢機械產業的市場數據」"
echo ""
echo "3. 如果看到 Claude 呼叫 MCP Server，就代表成功了！"
echo ""
echo "4. 查看使用指南："
echo "   - FIRST_TIME_USE.md（第一次使用）"
echo "   - HOW_TO_USE.md（完整使用說明）"
echo ""
echo "注意事項："
echo "   - 已使用虛擬環境隔離依賴套件"
echo "   - 已保留您原有的 Claude Desktop 設定"
echo "   - 備份檔案：claude_desktop_config.json.bak"
echo ""
echo "=========================================="
