"""
SBIR Data MCP Server
專注於經濟部統計處官方 API

功能：
1. 經濟部統計處總體統計資料庫 API
2. 工研院 IEK、資策會 MIC 由 Claude 的 search_web 處理
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
import httpx
import json
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel

# ============================================
# 資料模型
# ============================================

class MOEAStatData(BaseModel):
    """經濟部統計處數據格式"""
    category: str        # 類別
    period: str          # 統計期間
    value: float         # 數值
    unit: str            # 單位
    source_url: str      # 來源網址

# ============================================
# MCP Server 初始化
# ============================================

app = Server("sbir-data-server")

# ============================================
# 工具定義
# ============================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """定義可用的工具"""
    return [
        Tool(
            name="search_knowledge_base",
            description="搜尋 SBIR 知識庫中的相關文件。可搜尋方法論、FAQ、檢核清單、案例等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜尋關鍵字，如：創新、市場分析、經費、資格等"
                    },
                    "category": {
                        "type": "string",
                        "description": "文件類別（可選）",
                        "enum": ["methodology", "faq", "checklist", "case_study", "template", "all"],
                        "default": "all"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="read_document",
            description="讀取 SBIR 知識庫中的特定文件內容",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件的相對路徑，如：references/methodology_innovation.md"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="query_moea_statistics",
            description="查詢經濟部統計處總體統計資料庫（官方 API）。可查詢產業產值、出口、就業等數據。",
            inputSchema={
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "產業別，如：機械、化工、電子、資通訊"
                    },
                    "stat_type": {
                        "type": "string",
                        "description": "統計類型：產值、出口、就業人數",
                        "enum": ["產值", "出口", "就業人數"]
                    },
                    "start_year": {
                        "type": "integer",
                        "description": "起始年份（西元年）",
                        "default": 2020
                    },
                    "end_year": {
                        "type": "integer",
                        "description": "結束年份（西元年）",
                        "default": 2024
                    }
                },
                "required": ["industry", "stat_type"]
            }
        ),
        Tool(
            name="search_moea_website",
            description="搜尋經濟部統計處網站（當 API 無法滿足需求時使用）",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜尋關鍵字"
                    }
                },
                "required": ["keyword"]
            }
        )
    ]

# ============================================
# 工具執行
# ============================================

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """執行工具"""
    if name == "search_knowledge_base":
        return await search_knowledge_base(
            arguments["query"],
            arguments.get("category", "all")
        )
    elif name == "read_document":
        return await read_document(arguments["file_path"])
    elif name == "query_moea_statistics":
        return await query_moea_statistics(
            arguments["industry"],
            arguments["stat_type"],
            arguments.get("start_year", 2020),
            arguments.get("end_year", 2024)
        )
    elif name == "search_moea_website":
        return await search_moea_website(arguments["keyword"])
    else:
        raise ValueError(f"Unknown tool: {name}")

# ============================================
# 核心功能：知識庫搜尋與讀取
# ============================================

import os
import glob

# 取得專案根目錄（server.py 的上一層）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def search_knowledge_base(query: str, category: str = "all") -> list[TextContent]:
    """
    搜尋 SBIR 知識庫中的相關文件
    """
    
    # 定義搜尋目錄
    search_dirs = {
        "methodology": "references/methodology_*.md",
        "faq": "faq/*.md",
        "checklist": "checklists/*.md",
        "case_study": "examples/case_studies/*.md",
        "template": "templates/*.md",
        "all": "**/*.md"
    }
    
    pattern = search_dirs.get(category, "**/*.md")
    search_path = os.path.join(PROJECT_ROOT, pattern)
    
    # 搜尋檔案
    files = glob.glob(search_path, recursive=True)
    
    # 過濾相關檔案（簡單的關鍵字匹配）
    query_lower = query.lower()
    relevant_files = []
    
    for file_path in files:
        # 檢查檔名
        file_name = os.path.basename(file_path).lower()
        relative_path = os.path.relpath(file_path, PROJECT_ROOT)
        
        # 讀取檔案內容的前幾行來判斷相關性
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # 只讀前 500 字元
                if query_lower in file_name or query_lower in content.lower():
                    relevant_files.append({
                        "path": relative_path,
                        "name": os.path.basename(file_path),
                        "category": get_category_from_path(relative_path)
                    })
        except Exception:
            continue
    
    # 格式化結果
    if not relevant_files:
        result = f"""
## 搜尋結果

找不到與「{query}」相關的文件。

**建議**：
- 試試其他關鍵字
- 查看完整文件列表：README.md
"""
    else:
        result = f"""
## 搜尋結果：找到 {len(relevant_files)} 個相關文件

**搜尋關鍵字**：{query}

"""
        for i, file_info in enumerate(relevant_files[:10], 1):  # 最多顯示 10 個
            result += f"{i}. **{file_info['name']}**\n"
            result += f"   - 類別：{file_info['category']}\n"
            result += f"   - 路徑：`{file_info['path']}`\n"
            result += f"   - 使用 `read_document` 工具讀取此文件\n\n"
        
        if len(relevant_files) > 10:
            result += f"\n（還有 {len(relevant_files) - 10} 個相關文件未顯示）\n"
    
    return [TextContent(type="text", text=result)]

async def read_document(file_path: str) -> list[TextContent]:
    """
    讀取指定的文件內容
    """
    
    full_path = os.path.join(PROJECT_ROOT, file_path)
    
    # 安全檢查：確保路徑在專案目錄內
    if not os.path.abspath(full_path).startswith(PROJECT_ROOT):
        return [TextContent(
            type="text",
            text=f"❌ 錯誤：無法讀取專案目錄外的檔案"
        )]
    
    # 檢查檔案是否存在
    if not os.path.exists(full_path):
        return [TextContent(
            type="text",
            text=f"❌ 錯誤：找不到檔案 `{file_path}`\n\n請使用 `search_knowledge_base` 工具搜尋正確的檔案路徑。"
        )]
    
    # 讀取檔案
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = f"""
## 📄 {os.path.basename(file_path)}

**路徑**：`{file_path}`

---

{content}
"""
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 讀取檔案失敗：{str(e)}"
        )]

def get_category_from_path(path: str) -> str:
    """根據路徑判斷文件類別"""
    if "methodology" in path:
        return "方法論"
    elif "faq" in path:
        return "常見問題"
    elif "checklist" in path:
        return "檢核清單"
    elif "case_studies" in path:
        return "案例研究"
    elif "template" in path:
        return "範本"
    elif "quick_start" in path:
        return "快速啟動"
    else:
        return "其他"

# ============================================
# 核心功能：查詢經濟部統計處 API
# ============================================

async def query_moea_statistics(
    industry: str,
    stat_type: str,
    start_year: int,
    end_year: int
) -> list[TextContent]:
    """
    查詢經濟部統計處總體統計資料庫 API
    
    API 文件：https://nstatdb.dgbas.gov.tw/dgbasAll/webMain.aspx?sys=100&funid=API
    """
    
    # 產業代碼對應表（需要根據實際 API 文件調整）
    industry_codes = {
        "機械": "C29",
        "化工": "C20",
        "電子": "C26",
        "資通訊": "C26",
        "生技": "C21",
        "服務業": "G-S"
    }
    
    # 統計類型對應表
    stat_type_codes = {
        "產值": "production",
        "出口": "export",
        "就業人數": "employment"
    }
    
    industry_code = industry_codes.get(industry)
    if not industry_code:
        return [TextContent(
            type="text",
            text=f"❌ 不支援的產業別：{industry}\n\n支援的產業：{', '.join(industry_codes.keys())}"
        )]
    
    try:
        # 實際 API 呼叫
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 這裡需要根據實際 API 文件調整
            # 目前先回傳說明訊息
            
            result = f"""
## 經濟部統計處查詢結果

**產業別**：{industry}  
**統計類型**：{stat_type}  
**查詢期間**：{start_year} - {end_year}

---

⚠️ **API 實作說明**：

經濟部統計處提供總體統計資料庫 API，但需要：
1. 查詢「功能代碼」（每個統計表有唯一代碼）
2. 功能代碼列表：https://nstatdb.dgbas.gov.tw/

**建議替代方案**：
由於功能代碼查詢複雜，建議使用 Claude 的 `search_web` 工具：

```
search_web("{industry} {stat_type} site:dgbas.gov.tw OR site:moea.gov.tw")
```

**API 查詢範例**（需要功能代碼）：
```
https://nstatdb.dgbas.gov.tw/dgbasAll/webMain.aspx?sys=100&funid=API
  ?function=[功能代碼]
  &startTime={start_year}-01
  &endTime={end_year}-12
```

---

**來源**：
- 經濟部統計處：https://www.moea.gov.tw/Mns/dos/
- 總體統計資料庫：https://nstatdb.dgbas.gov.tw/
"""
            
            return [TextContent(type="text", text=result)]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ 查詢失敗：{str(e)}\n\n建議使用 Claude 的 search_web 工具作為替代方案。"
        )]

# ============================================
# 輔助功能：搜尋經濟部網站
# ============================================

async def search_moea_website(keyword: str) -> list[TextContent]:
    """提供搜尋建議（實際搜尋由 Claude 的 search_web 執行）"""
    
    result = f"""
## 經濟部統計處搜尋建議

**搜尋關鍵字**：{keyword}

---

**建議使用 Claude 的 `search_web` 工具**：

```
search_web("{keyword} site:dgbas.gov.tw OR site:moea.gov.tw")
```

**推薦查詢網站**：
- 經濟部統計處：https://www.moea.gov.tw/Mns/dos/
- 總體統計資料庫：https://nstatdb.dgbas.gov.tw/
- 產業統計：https://www.moea.gov.tw/Mns/dos/content/SubMenu.aspx?menu_id=6730

**查詢技巧**：
- 加上年份：`{keyword} 2024`
- 指定統計類型：`{keyword} 產值` 或 `{keyword} 出口`
"""
    
    return [TextContent(type="text", text=result)]

# ============================================
# Server 啟動
# ============================================

async def main():
    """啟動 MCP Server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

