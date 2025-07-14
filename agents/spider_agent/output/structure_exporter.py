"""
結構匯出工具 - 將爬取的結構資料匯出為各種格式
"""

import json
import os
import shutil
from typing import Dict, Any, List
from datetime import datetime
from ..config import SpiderConfig


class StructureExporter:
    """結構匯出工具"""
    
    def __init__(self):
        """初始化匯出工具"""
        self.config = SpiderConfig()
        self.config.ensure_output_dirs()
        
    async def export_analysis_result(self, analysis_result: Dict[str, Any], export_formats: List[str] = None) -> Dict[str, str]:
        """
        匯出分析結果
        
        Args:
            analysis_result: 分析結果資料
            export_formats: 匯出格式列表 ['json', 'html', 'markdown', 'css']
            
        Returns:
            Dict: 匯出檔案路徑字典
        """
        if export_formats is None:
            export_formats = ['json', 'html', 'markdown', 'css']
        
        exported_files = {}
        
        try:
            print("💾 開始匯出分析結果...")
            
            # 生成基礎檔名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"structure_analysis_{timestamp}"
            
            # 匯出JSON格式
            if 'json' in export_formats:
                json_path = await self._export_json(analysis_result, base_filename)
                exported_files['json'] = json_path
            
            # 匯出HTML報告
            if 'html' in export_formats:
                html_path = await self._export_html_report(analysis_result, base_filename)
                exported_files['html'] = html_path
            
            # 匯出Markdown文檔
            if 'markdown' in export_formats:
                md_path = await self._export_markdown(analysis_result, base_filename)
                exported_files['markdown'] = md_path
            
            # 匯出CSS樣式檔案
            if 'css' in export_formats:
                css_path = await self._export_css_template(analysis_result, base_filename)
                exported_files['css'] = css_path
            
            print("✅ 分析結果匯出完成")
            return exported_files
            
        except Exception as e:
            print(f"❌ 匯出分析結果時發生錯誤: {str(e)}")
            return {}
    
    async def _export_json(self, analysis_result: Dict[str, Any], base_filename: str) -> str:
        """匯出JSON格式"""
        try:
            json_path = os.path.join(self.config.STRUCTURE_DIR, f"{base_filename}.json")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON檔案已保存: {json_path}")
            return json_path
            
        except Exception as e:
            print(f"❌ 匯出JSON時發生錯誤: {str(e)}")
            return ""
    
    async def _export_html_report(self, analysis_result: Dict[str, Any], base_filename: str) -> str:
        """匯出HTML報告"""
        try:
            html_path = os.path.join(self.config.STRUCTURE_DIR, f"{base_filename}_report.html")
            
            html_content = self._generate_html_report(analysis_result)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ HTML報告已保存: {html_path}")
            return html_path
            
        except Exception as e:
            print(f"❌ 匯出HTML報告時發生錯誤: {str(e)}")
            return ""
    
    def _generate_html_report(self, analysis_result: Dict[str, Any]) -> str:
        """生成HTML報告內容"""
        page_info = analysis_result.get('page_info', {})
        html_structure = analysis_result.get('html_structure', {})
        css_analysis = analysis_result.get('css_analysis', {})
        js_analysis = analysis_result.get('javascript_analysis', {})
        layout_analysis = analysis_result.get('layout_analysis', {})
        
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>網頁結構分析報告 - {page_info.get('title', 'Unknown')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .section {{
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .section h3 {{
            color: #34495e;
            margin-top: 25px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}
        .tag-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }}
        .tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.9em;
            border: 1px solid #bbdefb;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            text-align: center;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .code-block {{
            background: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            font-family: 'Fira Code', monospace;
            font-size: 0.9em;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ 網頁結構分析報告</h1>
        <p><strong>分析網站:</strong> {page_info.get('url', 'Unknown')}</p>
        <p><strong>頁面標題:</strong> {page_info.get('title', 'Unknown')}</p>
        <p class="timestamp"><strong>分析時間:</strong> {analysis_result.get('timestamp', 'Unknown')}</p>
    </div>

    <div class="section">
        <h2>📊 頁面基本資訊</h2>
        <div class="info-grid">
            <div class="info-card">
                <h3>頁面資訊</h3>
                <p><strong>URL:</strong> {page_info.get('url', 'N/A')}</p>
                <p><strong>標題:</strong> {page_info.get('title', 'N/A')}</p>
                <p><strong>內容長度:</strong> {page_info.get('content_length', 0):,} 字元</p>
                <p><strong>Viewport:</strong> {page_info.get('viewport', 'N/A')}</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🏗️ HTML結構分析</h2>
        <div class="stats">
            {self._generate_element_stats(html_structure.get('body_structure', {}).get('element_count', {}))}
        </div>
        
        <h3>語義化元素</h3>
        <div class="tag-list">
            {self._generate_semantic_tags(html_structure.get('semantic_elements', {}))}
        </div>
        
        <h3>無障礙性分析</h3>
        {self._generate_accessibility_info(html_structure.get('accessibility', {}))}
    </div>

    <div class="section">
        <h2>🎨 CSS樣式分析</h2>
        <div class="info-grid">
            <div class="info-card">
                <h3>外部樣式表</h3>
                <p><strong>數量:</strong> {len(css_analysis.get('external_stylesheets', []))}</p>
                <p><strong>內聯樣式:</strong> {css_analysis.get('inline_styles', {}).get('inline_styles_count', 0)}</p>
                <p><strong>CSS變數:</strong> {len(css_analysis.get('css_variables', {}))}</p>
            </div>
            <div class="info-card">
                <h3>響應式設計</h3>
                <p><strong>Viewport Meta:</strong> {'✅' if css_analysis.get('responsive_design', {}).get('has_viewport_meta') else '❌'}</p>
                <p><strong>媒體查詢:</strong> {css_analysis.get('responsive_design', {}).get('media_queries_count', 0)}</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>⚡ JavaScript分析</h2>
        <div class="info-grid">
            <div class="info-card">
                <h3>JavaScript資源</h3>
                <p><strong>外部腳本:</strong> {len([js for js in js_analysis.get('js_resources', []) if js.get('src')])}</p>
                <p><strong>內聯腳本:</strong> {len([js for js in js_analysis.get('js_resources', []) if js.get('hasContent')])}</p>
            </div>
            <div class="info-card">
                <h3>檢測到的框架</h3>
                <div class="tag-list">
                    {self._generate_framework_tags(js_analysis.get('frameworks', []))}
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📐 頁面佈局</h2>
        {self._generate_layout_info(layout_analysis)}
    </div>

    <div class="section">
        <h2>🧭 導航結構</h2>
        {self._generate_navigation_info(analysis_result.get('navigation_analysis', {}))}
    </div>

    <div class="section">
        <h2>📝 表單分析</h2>
        {self._generate_forms_info(analysis_result.get('forms_analysis', {}))}
    </div>

    <div class="section">
        <h2>🖱️ 互動元素</h2>
        {self._generate_interactive_info(analysis_result.get('interactive_analysis', {}))}
    </div>

</body>
</html>
        """
        
        return html_template
    
    def _generate_element_stats(self, element_count: Dict[str, int]) -> str:
        """生成元素統計HTML"""
        stats_html = ""
        for element, count in element_count.items():
            stats_html += f"""
            <div class="stat-card">
                <span class="stat-number">{count}</span>
                <div>{element.upper()}</div>
            </div>
            """
        return stats_html
    
    def _generate_semantic_tags(self, semantic_elements: Dict[str, List]) -> str:
        """生成語義化標籤HTML"""
        tags_html = ""
        for tag, elements in semantic_elements.items():
            if elements:
                tags_html += f'<span class="tag">{tag} ({len(elements)})</span>'
        return tags_html
    
    def _generate_accessibility_info(self, accessibility: Dict[str, Any]) -> str:
        """生成無障礙性資訊HTML"""
        return f"""
        <div class="info-grid">
            <div class="info-card">
                <p><strong>圖片Alt屬性:</strong> {accessibility.get('alt_texts', 0)} ✅ / {accessibility.get('missing_alt', 0)} ❌</p>
                <p><strong>ARIA標籤:</strong> {accessibility.get('aria_labels', 0)}</p>
                <p><strong>Landmark元素:</strong> {', '.join(accessibility.get('landmarks', []))}</p>
            </div>
        </div>
        """
    
    def _generate_framework_tags(self, frameworks: List[str]) -> str:
        """生成框架標籤HTML"""
        if not frameworks:
            return '<span class="tag">未檢測到框架</span>'
        
        tags_html = ""
        for framework in frameworks:
            tags_html += f'<span class="tag">{framework}</span>'
        return tags_html
    
    def _generate_layout_info(self, layout: Dict[str, Any]) -> str:
        """生成佈局資訊HTML"""
        viewport = layout.get('viewport', {})
        scroll = layout.get('scroll', {})
        
        return f"""
        <div class="info-grid">
            <div class="info-card">
                <h3>視窗資訊</h3>
                <p><strong>寬度:</strong> {viewport.get('width', 0)}px</p>
                <p><strong>高度:</strong> {viewport.get('height', 0)}px</p>
            </div>
            <div class="info-card">
                <h3>文件尺寸</h3>
                <p><strong>總寬度:</strong> {scroll.get('width', 0)}px</p>
                <p><strong>總高度:</strong> {scroll.get('height', 0)}px</p>
            </div>
        </div>
        """
    
    def _generate_navigation_info(self, navigation: Dict[str, Any]) -> str:
        """生成導航資訊HTML"""
        return f"""
        <div class="info-grid">
            <div class="info-card">
                <h3>導航統計</h3>
                <p><strong>導航元素:</strong> {len(navigation.get('nav_elements', []))}</p>
                <p><strong>選單項目:</strong> {len(navigation.get('menu_items', []))}</p>
                <p><strong>連結總數:</strong> {len(navigation.get('links', []))}</p>
            </div>
        </div>
        """
    
    def _generate_forms_info(self, forms: Dict[str, Any]) -> str:
        """生成表單資訊HTML"""
        return f"""
        <div class="info-grid">
            <div class="info-card">
                <h3>表單統計</h3>
                <p><strong>表單數量:</strong> {forms.get('forms_count', 0)}</p>
                <div class="tag-list">
                    {self._generate_input_type_tags(forms.get('input_types', {}))}
                </div>
            </div>
        </div>
        """
    
    def _generate_input_type_tags(self, input_types: Dict[str, int]) -> str:
        """生成輸入類型標籤HTML"""
        tags_html = ""
        for input_type, count in input_types.items():
            tags_html += f'<span class="tag">{input_type} ({count})</span>'
        return tags_html
    
    def _generate_interactive_info(self, interactive: Dict[str, Any]) -> str:
        """生成互動元素資訊HTML"""
        return f"""
        <div class="stats">
            <div class="stat-card">
                <span class="stat-number">{interactive.get('buttons', 0)}</span>
                <div>按鈕</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{interactive.get('clickable_elements', 0)}</span>
                <div>可點擊元素</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{interactive.get('modals', 0)}</span>
                <div>模態框</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{interactive.get('dropdowns', 0)}</span>
                <div>下拉選單</div>
            </div>
        </div>
        """
    
    async def _export_markdown(self, analysis_result: Dict[str, Any], base_filename: str) -> str:
        """匯出Markdown文檔"""
        try:
            md_path = os.path.join(self.config.STRUCTURE_DIR, f"{base_filename}.md")
            
            md_content = self._generate_markdown_content(analysis_result)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"✅ Markdown文檔已保存: {md_path}")
            return md_path
            
        except Exception as e:
            print(f"❌ 匯出Markdown時發生錯誤: {str(e)}")
            return ""
    
    def _generate_markdown_content(self, analysis_result: Dict[str, Any]) -> str:
        """生成Markdown內容"""
        page_info = analysis_result.get('page_info', {})
        
        markdown_content = f"""# 🕷️ 網頁結構分析報告

## 基本資訊
- **網站URL**: {page_info.get('url', 'Unknown')}
- **頁面標題**: {page_info.get('title', 'Unknown')}
- **分析時間**: {analysis_result.get('timestamp', 'Unknown')}

## HTML結構分析
{self._generate_markdown_html_analysis(analysis_result.get('html_structure', {}))}

## CSS樣式分析
{self._generate_markdown_css_analysis(analysis_result.get('css_analysis', {}))}

## JavaScript分析
{self._generate_markdown_js_analysis(analysis_result.get('javascript_analysis', {}))}

## 頁面佈局
{self._generate_markdown_layout_analysis(analysis_result.get('layout_analysis', {}))}

## 建議事項
{self._generate_markdown_recommendations(analysis_result)}
"""
        
        return markdown_content
    
    def _generate_markdown_html_analysis(self, html_structure: Dict[str, Any]) -> str:
        """生成HTML分析的Markdown內容"""
        element_count = html_structure.get('body_structure', {}).get('element_count', {})
        
        content = "### 元素統計\n"
        for element, count in element_count.items():
            content += f"- **{element}**: {count}\n"
        
        return content
    
    def _generate_markdown_css_analysis(self, css_analysis: Dict[str, Any]) -> str:
        """生成CSS分析的Markdown內容"""
        return f"""### CSS資源
- 外部樣式表: {len(css_analysis.get('external_stylesheets', []))}
- 內聯樣式: {css_analysis.get('inline_styles', {}).get('inline_styles_count', 0)}
- CSS變數: {len(css_analysis.get('css_variables', {}))}

### 響應式設計
- Viewport Meta: {'✅' if css_analysis.get('responsive_design', {}).get('has_viewport_meta') else '❌'}
- 媒體查詢: {css_analysis.get('responsive_design', {}).get('media_queries_count', 0)}
"""
    
    def _generate_markdown_js_analysis(self, js_analysis: Dict[str, Any]) -> str:
        """生成JavaScript分析的Markdown內容"""
        frameworks = js_analysis.get('frameworks', [])
        frameworks_text = ', '.join(frameworks) if frameworks else '未檢測到'
        
        return f"""### JavaScript資源
- 外部腳本: {len([js for js in js_analysis.get('js_resources', []) if js.get('src')])}
- 內聯腳本: {len([js for js in js_analysis.get('js_resources', []) if js.get('hasContent')])}

### 檢測到的框架
{frameworks_text}
"""
    
    def _generate_markdown_layout_analysis(self, layout: Dict[str, Any]) -> str:
        """生成佈局分析的Markdown內容"""
        viewport = layout.get('viewport', {})
        
        return f"""### 視窗資訊
- 寬度: {viewport.get('width', 0)}px
- 高度: {viewport.get('height', 0)}px

### 主要區塊
{len(layout.get('sections', []))} 個主要區塊
"""
    
    def _generate_markdown_recommendations(self, analysis_result: Dict[str, Any]) -> str:
        """生成建議事項的Markdown內容"""
        recommendations = []
        
        # 檢查無障礙性
        accessibility = analysis_result.get('html_structure', {}).get('accessibility', {})
        if accessibility.get('missing_alt', 0) > 0:
            recommendations.append("- 建議為所有圖片添加alt屬性以提升無障礙性")
        
        # 檢查響應式設計
        responsive = analysis_result.get('css_analysis', {}).get('responsive_design', {})
        if not responsive.get('has_viewport_meta'):
            recommendations.append("- 建議添加viewport meta標籤以支援響應式設計")
        
        if not recommendations:
            recommendations.append("- 目前網站結構良好，未發現明顯問題")
        
        return '\n'.join(recommendations)
    
    async def _export_css_template(self, analysis_result: Dict[str, Any], base_filename: str) -> str:
        """匯出CSS樣板檔案"""
        try:
            css_path = os.path.join(self.config.ASSETS_DIR, f"{base_filename}_template.css")
            
            css_content = self._generate_css_template(analysis_result)
            
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            print(f"✅ CSS樣板已保存: {css_path}")
            return css_path
            
        except Exception as e:
            print(f"❌ 匯出CSS樣板時發生錯誤: {str(e)}")
            return ""
    
    def _generate_css_template(self, analysis_result: Dict[str, Any]) -> str:
        """生成CSS樣板內容"""
        css_variables = analysis_result.get('css_analysis', {}).get('css_variables', {})
        
        css_template = """/* 
 * 基於網站結構分析生成的CSS樣板
 * 可用於ByteC Network Dashboard的樣式參考
 */

/* CSS變數 */
:root {
"""
        
        # 添加檢測到的CSS變數
        for var_name, var_value in css_variables.items():
            css_template += f"  {var_name}: {var_value};\n"
        
        # 添加基本變數（如果沒有檢測到）
        if not css_variables:
            css_template += """  --primary-color: #3498db;
  --secondary-color: #2c3e50;
  --success-color: #27ae60;
  --warning-color: #f39c12;
  --danger-color: #e74c3c;
  --background-color: #f8f9fa;
  --text-color: #333;
  --border-color: #dee2e6;
  --border-radius: 4px;
  --box-shadow: 0 2px 4px rgba(0,0,0,0.1);
"""
        
        css_template += """}

/* 基礎樣式 */
* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  line-height: 1.6;
  color: var(--text-color);
  background-color: var(--background-color);
  margin: 0;
  padding: 0;
}

/* 容器樣式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 卡片樣式 */
.card {
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
  margin-bottom: 20px;
}

/* 按鈕樣式 */
.btn {
  display: inline-block;
  padding: 10px 20px;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 導航樣式 */
.navbar {
  background: white;
  box-shadow: var(--box-shadow);
  padding: 1rem 0;
}

.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  margin-right: 2rem;
}

.nav-link {
  color: var(--text-color);
  text-decoration: none;
  transition: color 0.3s ease;
}

.nav-link:hover {
  color: var(--primary-color);
}

/* 表格樣式 */
.table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.table th {
  background-color: var(--background-color);
  font-weight: 600;
}

/* 表單樣式 */
.form-group {
  margin-bottom: 1rem;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .container {
    padding: 0 15px;
  }
  
  .nav-menu {
    flex-direction: column;
  }
  
  .nav-item {
    margin-right: 0;
    margin-bottom: 0.5rem;
  }
}

/* 工具類 */
.text-center { text-align: center; }
.text-right { text-align: right; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 1rem; }
.mb-4 { margin-bottom: 1.5rem; }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 1rem; }
.p-4 { padding: 1.5rem; }
"""
        
        return css_template
    
    async def create_dashboard_template(self, analysis_result: Dict[str, Any]) -> str:
        """創建Dashboard HTML樣板"""
        try:
            template_path = os.path.join(self.config.STRUCTURE_DIR, "bytec_dashboard_template.html")
            
            template_content = self._generate_dashboard_template(analysis_result)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            print(f"✅ Dashboard樣板已保存: {template_path}")
            return template_path
            
        except Exception as e:
            print(f"❌ 創建Dashboard樣板時發生錯誤: {str(e)}")
            return ""
    
    def _generate_dashboard_template(self, analysis_result: Dict[str, Any]) -> str:
        """生成Dashboard HTML樣板"""
        return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ByteC Network Dashboard</title>
    <link rel="stylesheet" href="assets/template.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <div class="nav-brand">
                <h2>ByteC Network</h2>
            </div>
            <ul class="nav-menu">
                <li class="nav-item"><a href="#" class="nav-link">Dashboard</a></li>
                <li class="nav-item"><a href="#" class="nav-link">Reports</a></li>
                <li class="nav-item"><a href="#" class="nav-link">Performance</a></li>
                <li class="nav-item"><a href="#" class="nav-link">Settings</a></li>
            </ul>
        </div>
    </nav>

    <main class="container">
        <header class="page-header">
            <h1>Performance Dashboard</h1>
            <p>基於Involve Asia結構分析的現代化儀表板</p>
        </header>

        <div class="dashboard-grid">
            <div class="card">
                <h3>📊 數據總覽</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-number">1,234</span>
                        <span class="stat-label">總轉換</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">$5,678</span>
                        <span class="stat-label">總收益</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>📈 性能報告</h3>
                <div class="chart-container">
                    <!-- 圖表區域 -->
                    <p>圖表將在此顯示</p>
                </div>
            </div>

            <div class="card">
                <h3>📋 最新活動</h3>
                <div class="activity-list">
                    <div class="activity-item">
                        <span class="activity-time">2小時前</span>
                        <span class="activity-text">新轉換記錄</span>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script src="assets/dashboard.js"></script>
</body>
</html>""" 