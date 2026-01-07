#!/bin/bash

# SBIR Skill 自動安裝腳本（Mac 版）
# 這個腳本會自動幫您安裝所有需要的東西

echo "=========================================="
echo "   SBIR Skill 自動安裝程式"
echo "=========================================="
echo ""

# 取得腳本所在目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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
    PYTHON_PATH=$(which python3)
    PYTHON_VERSION=$(python3 --version)
    echo "✅ 找到 Python: $PYTHON_VERSION"
    echo "   位置: $PYTHON_PATH"
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

# 步驟 2: 安裝依賴套件
echo "步驟 2/4: 安裝必要套件..."
echo "這可能需要幾分鐘，請稍候..."
cd mcp-server
python3 -m pip install -q mcp httpx pydantic

if [ $? -eq 0 ]; then
    echo "✅ 套件安裝成功"
else
    echo "❌ 套件安裝失敗"
    echo "請檢查網路連線，或手動執行："
    echo "cd mcp-server && pip install mcp httpx pydantic"
    exit 1
fi
cd ..
echo ""

# 步驟 3: 創建 Claude Desktop 設定檔
echo "步驟 3/4: 設定 Claude Desktop..."

CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
PROJECT_PATH=$(pwd)

# 創建目錄（如果不存在）
mkdir -p "$CLAUDE_CONFIG_DIR"

# 創建設定檔
cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "sbir-data": {
      "command": "$PYTHON_PATH",
      "args": [
        "$PROJECT_PATH/mcp-server/server.py"
      ]
    }
  }
}
EOF

if [ $? -eq 0 ]; then
    echo "✅ Claude Desktop 設定完成"
    echo "   設定檔位置: $CLAUDE_CONFIG_FILE"
else
    echo "❌ 設定檔創建失敗"
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
echo "=========================================="
