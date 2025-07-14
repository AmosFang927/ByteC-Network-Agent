"""
網頁結構分析器 - 分析網頁的架構、樣式和功能
"""

import json
import re
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import cssutils
from urllib.parse import urljoin, urlparse
from ..config import SpiderConfig


class StructureAnalyzer:
    """網頁結構分析器"""
    
    def __init__(self, playwright_client):
        """
        初始化結構分析器
        
        Args:
            playwright_client: Playwright客戶端實例
        """
        self.client = playwright_client
        self.config = SpiderConfig()
        self.analysis_result = {}
        
    async def analyze_page_structure(self, url: str) -> Dict[str, Any]:
        """
        分析頁面完整結構
        
        Args:
            url: 頁面URL
            
        Returns:
            Dict: 分析結果
        """
        try:
            print("🔍 開始分析頁面結構...")
            
            # 獲取頁面基本資訊
            page_info = await self._get_page_info(url)
            
            # 獲取HTML結構
            html_structure = await self._analyze_html_structure()
            
            # 分析CSS樣式
            css_analysis = await self._analyze_css_styles()
            
            # 分析JavaScript功能
            js_analysis = await self._analyze_javascript()
            
            # 分析頁面佈局
            layout_analysis = await self._analyze_layout()
            
            # 分析導航結構
            navigation_analysis = await self._analyze_navigation()
            
            # 分析表單元素
            forms_analysis = await self._analyze_forms()
            
            # 分析互動元素
            interactive_analysis = await self._analyze_interactive_elements()
            
            # 整合分析結果
            self.analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "page_info": page_info,
                "html_structure": html_structure,
                "css_analysis": css_analysis,
                "javascript_analysis": js_analysis,
                "layout_analysis": layout_analysis,
                "navigation_analysis": navigation_analysis,
                "forms_analysis": forms_analysis,
                "interactive_analysis": interactive_analysis
            }
            
            print("✅ 頁面結構分析完成")
            return self.analysis_result
            
        except Exception as e:
            print(f"❌ 分析頁面結構時發生錯誤: {str(e)}")
            return {}
    
    async def _get_page_info(self, url: str) -> Dict[str, Any]:
        """獲取頁面基本資訊"""
        try:
            print("📄 獲取頁面基本資訊...")
            
            page_content = await self.client.get_page_content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 獲取頁面標題
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # 獲取meta標籤
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            # 獲取viewport設定
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            viewport_content = viewport.get('content') if viewport else ""
            
            return {
                "title": title_text,
                "url": url,
                "meta_tags": meta_tags,
                "viewport": viewport_content,
                "content_length": len(page_content)
            }
            
        except Exception as e:
            print(f"❌ 獲取頁面基本資訊時發生錯誤: {str(e)}")
            return {}
    
    async def _analyze_html_structure(self) -> Dict[str, Any]:
        """分析HTML結構"""
        try:
            print("🏗️ 分析HTML結構...")
            
            page_content = await self.client.get_page_content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 分析文檔結構
            structure = {
                "doctype": "html5" if "<!DOCTYPE html>" in page_content else "other",
                "html_attributes": dict(soup.html.attrs) if soup.html else {},
                "head_elements": self._analyze_head_elements(soup),
                "body_structure": self._analyze_body_structure(soup),
                "semantic_elements": self._find_semantic_elements(soup),
                "accessibility": self._analyze_accessibility(soup)
            }
            
            return structure
            
        except Exception as e:
            print(f"❌ 分析HTML結構時發生錯誤: {str(e)}")
            return {}
    
    def _analyze_head_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """分析head元素"""
        head = soup.find('head')
        if not head:
            return {}
        
        elements = {
            "stylesheets": [],
            "scripts": [],
            "links": [],
            "meta_count": len(head.find_all('meta'))
        }
        
        # 分析CSS連結
        for link in head.find_all('link', rel='stylesheet'):
            elements["stylesheets"].append({
                "href": link.get('href'),
                "media": link.get('media', 'all'),
                "integrity": link.get('integrity')
            })
        
        # 分析JavaScript
        for script in head.find_all('script'):
            elements["scripts"].append({
                "src": script.get('src'),
                "type": script.get('type', 'text/javascript'),
                "async": script.has_attr('async'),
                "defer": script.has_attr('defer')
            })
        
        # 分析其他連結
        for link in head.find_all('link'):
            if link.get('rel') != 'stylesheet':
                elements["links"].append({
                    "rel": link.get('rel'),
                    "href": link.get('href'),
                    "type": link.get('type')
                })
        
        return elements
    
    def _analyze_body_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """分析body結構"""
        body = soup.find('body')
        if not body:
            return {}
        
        structure = {
            "body_attributes": dict(body.attrs),
            "main_sections": [],
            "element_count": {},
            "id_classes": {
                "ids": [],
                "classes": []
            }
        }
        
        # 統計元素數量
        for tag in ['div', 'section', 'article', 'aside', 'header', 'footer', 'nav', 'main']:
            count = len(body.find_all(tag))
            if count > 0:
                structure["element_count"][tag] = count
        
        # 收集主要區塊
        for section in body.find_all(['section', 'main', 'article']):
            structure["main_sections"].append({
                "tag": section.name,
                "id": section.get('id'),
                "class": section.get('class'),
                "content_preview": section.get_text()[:100] + "..." if len(section.get_text()) > 100 else section.get_text()
            })
        
        # 收集ID和class
        for element in body.find_all(True):
            if element.get('id'):
                structure["id_classes"]["ids"].append(element.get('id'))
            if element.get('class'):
                structure["id_classes"]["classes"].extend(element.get('class'))
        
        # 去重
        structure["id_classes"]["ids"] = list(set(structure["id_classes"]["ids"]))
        structure["id_classes"]["classes"] = list(set(structure["id_classes"]["classes"]))
        
        return structure
    
    def _find_semantic_elements(self, soup: BeautifulSoup) -> Dict[str, List]:
        """尋找語義化元素"""
        semantic_tags = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        semantic_elements = {}
        
        for tag in semantic_tags:
            elements = soup.find_all(tag)
            semantic_elements[tag] = [
                {
                    "id": elem.get('id'),
                    "class": elem.get('class'),
                    "content_preview": elem.get_text()[:50] + "..." if len(elem.get_text()) > 50 else elem.get_text()
                }
                for elem in elements
            ]
        
        return semantic_elements
    
    def _analyze_accessibility(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """分析無障礙性"""
        accessibility = {
            "alt_texts": 0,
            "missing_alt": 0,
            "aria_labels": 0,
            "heading_structure": [],
            "landmarks": []
        }
        
        # 檢查圖片alt屬性
        images = soup.find_all('img')
        for img in images:
            if img.get('alt'):
                accessibility["alt_texts"] += 1
            else:
                accessibility["missing_alt"] += 1
        
        # 檢查ARIA標籤
        aria_elements = soup.find_all(True, attrs=lambda x: x and any(key.startswith('aria-') for key in x.keys()))
        accessibility["aria_labels"] = len(aria_elements)
        
        # 檢查標題結構
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            if headings:
                accessibility["heading_structure"].append({
                    f"h{i}": len(headings),
                    "texts": [h.get_text().strip()[:50] for h in headings[:3]]
                })
        
        # 檢查landmark元素
        landmarks = soup.find_all(['header', 'nav', 'main', 'aside', 'footer'])
        accessibility["landmarks"] = [elem.name for elem in landmarks]
        
        return accessibility
    
    async def _analyze_css_styles(self) -> Dict[str, Any]:
        """分析CSS樣式"""
        try:
            print("🎨 分析CSS樣式...")
            
            # 獲取CSS資源
            css_links = await self._get_css_resources()
            
            # 分析內聯樣式
            inline_styles = await self._analyze_inline_styles()
            
            # 分析CSS變數和主題
            css_variables = await self._extract_css_variables()
            
            # 分析響應式設計
            responsive_design = await self._analyze_responsive_design()
            
            return {
                "external_stylesheets": css_links,
                "inline_styles": inline_styles,
                "css_variables": css_variables,
                "responsive_design": responsive_design
            }
            
        except Exception as e:
            print(f"❌ 分析CSS樣式時發生錯誤: {str(e)}")
            return {}
    
    async def _get_css_resources(self) -> List[Dict]:
        """獲取CSS資源"""
        try:
            # 執行JavaScript獲取所有CSS連結
            script = """
            const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
            return links.map(link => ({
                href: link.href,
                media: link.media || 'all',
                disabled: link.disabled
            }));
            """
            
            css_links = await self.client._mcp_evaluate(script)
            return css_links or []
            
        except Exception as e:
            print(f"❌ 獲取CSS資源時發生錯誤: {str(e)}")
            return []
    
    async def _analyze_inline_styles(self) -> Dict[str, Any]:
        """分析內聯樣式"""
        try:
            page_content = await self.client.get_page_content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 收集style標籤
            style_tags = soup.find_all('style')
            style_content = []
            
            for style in style_tags:
                style_content.append(style.get_text())
            
            # 收集內聯樣式
            inline_styles = []
            for element in soup.find_all(True, style=True):
                inline_styles.append({
                    "tag": element.name,
                    "style": element.get('style'),
                    "id": element.get('id'),
                    "class": element.get('class')
                })
            
            return {
                "style_tags_count": len(style_tags),
                "style_content": style_content,
                "inline_styles_count": len(inline_styles),
                "inline_styles": inline_styles[:10]  # 限制數量
            }
            
        except Exception as e:
            print(f"❌ 分析內聯樣式時發生錯誤: {str(e)}")
            return {}
    
    async def _extract_css_variables(self) -> Dict[str, Any]:
        """提取CSS變數"""
        try:
            script = """
            const rootStyles = getComputedStyle(document.documentElement);
            const variables = {};
            
            // 獲取CSS自定義屬性
            for (let i = 0; i < rootStyles.length; i++) {
                const prop = rootStyles[i];
                if (prop.startsWith('--')) {
                    variables[prop] = rootStyles.getPropertyValue(prop).trim();
                }
            }
            
            return variables;
            """
            
            css_variables = await self.client._mcp_evaluate(script)
            return css_variables or {}
            
        except Exception as e:
            print(f"❌ 提取CSS變數時發生錯誤: {str(e)}")
            return {}
    
    async def _analyze_responsive_design(self) -> Dict[str, Any]:
        """分析響應式設計"""
        try:
            page_content = await self.client.get_page_content()
            
            # 檢查viewport meta tag
            has_viewport = 'viewport' in page_content
            
            # 檢查媒體查詢
            media_queries = re.findall(r'@media[^{]+{[^}]*}', page_content, re.IGNORECASE)
            
            # 檢查響應式類別
            responsive_classes = []
            responsive_patterns = [
                r'\.col-\w+',
                r'\.row',
                r'\.container',
                r'\.responsive',
                r'\.mobile',
                r'\.tablet',
                r'\.desktop'
            ]
            
            for pattern in responsive_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                responsive_classes.extend(matches)
            
            return {
                "has_viewport_meta": has_viewport,
                "media_queries_count": len(media_queries),
                "responsive_classes": list(set(responsive_classes))
            }
            
        except Exception as e:
            print(f"❌ 分析響應式設計時發生錯誤: {str(e)}")
            return {}
    
    async def _analyze_javascript(self) -> Dict[str, Any]:
        """分析JavaScript功能"""
        try:
            print("⚡ 分析JavaScript功能...")
            
            # 獲取JavaScript資源
            js_resources = await self._get_js_resources()
            
            # 分析事件監聽器
            event_listeners = await self._analyze_event_listeners()
            
            # 檢查框架和庫
            frameworks = await self._detect_frameworks()
            
            return {
                "js_resources": js_resources,
                "event_listeners": event_listeners,
                "frameworks": frameworks
            }
            
        except Exception as e:
            print(f"❌ 分析JavaScript時發生錯誤: {str(e)}")
            return {}
    
    async def _get_js_resources(self) -> List[Dict]:
        """獲取JavaScript資源"""
        try:
            script = """
            const scripts = Array.from(document.querySelectorAll('script'));
            return scripts.map(script => ({
                src: script.src || null,
                type: script.type || 'text/javascript',
                async: script.async,
                defer: script.defer,
                hasContent: script.innerHTML.length > 0
            }));
            """
            
            js_resources = await self.client._mcp_evaluate(script)
            return js_resources or []
            
        except Exception as e:
            print(f"❌ 獲取JavaScript資源時發生錯誤: {str(e)}")
            return []
    
    async def _analyze_event_listeners(self) -> Dict[str, Any]:
        """分析事件監聽器"""
        try:
            script = """
            const events = {};
            const elements = document.querySelectorAll('*');
            
            elements.forEach(element => {
                const attributes = Array.from(element.attributes);
                attributes.forEach(attr => {
                    if (attr.name.startsWith('on')) {
                        const eventType = attr.name.substring(2);
                        if (!events[eventType]) {
                            events[eventType] = 0;
                        }
                        events[eventType]++;
                    }
                });
            });
            
            return events;
            """
            
            event_listeners = await self.client._mcp_evaluate(script)
            return event_listeners or {}
            
        except Exception as e:
            print(f"❌ 分析事件監聽器時發生錯誤: {str(e)}")
            return {}
    
    async def _detect_frameworks(self) -> List[str]:
        """檢測JavaScript框架"""
        try:
            script = """
            const frameworks = [];
            
            // 檢測常見框架
            if (typeof React !== 'undefined') frameworks.push('React');
            if (typeof Vue !== 'undefined') frameworks.push('Vue');
            if (typeof Angular !== 'undefined') frameworks.push('Angular');
            if (typeof jQuery !== 'undefined') frameworks.push('jQuery');
            if (typeof $ !== 'undefined') frameworks.push('jQuery-like');
            if (typeof bootstrap !== 'undefined') frameworks.push('Bootstrap');
            
            return frameworks;
            """
            
            frameworks = await self.client._mcp_evaluate(script)
            return frameworks or []
            
        except Exception as e:
            print(f"❌ 檢測框架時發生錯誤: {str(e)}")
            return []
    
    async def _analyze_layout(self) -> Dict[str, Any]:
        """分析頁面佈局"""
        try:
            print("📐 分析頁面佈局...")
            
            script = """
            const layout = {
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                scroll: {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight
                },
                sections: []
            };
            
            // 分析主要區塊
            const sections = document.querySelectorAll('header, nav, main, section, aside, footer, .container, .wrapper');
            sections.forEach(section => {
                const rect = section.getBoundingClientRect();
                layout.sections.push({
                    tag: section.tagName.toLowerCase(),
                    id: section.id || null,
                    className: section.className || null,
                    position: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                });
            });
            
            return layout;
            """
            
            layout = await self.client._mcp_evaluate(script)
            return layout or {}
            
        except Exception as e:
            print(f"❌ 分析頁面佈局時發生錯誤: {str(e)}")
            return {}
    
    async def _analyze_navigation(self) -> Dict[str, Any]:
        """分析導航結構"""
        try:
            print("🧭 分析導航結構...")
            
            page_content = await self.client.get_page_content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            navigation = {
                "nav_elements": [],
                "menu_items": [],
                "breadcrumbs": [],
                "links": []
            }
            
            # 分析nav元素
            nav_elements = soup.find_all('nav')
            for nav in nav_elements:
                navigation["nav_elements"].append({
                    "id": nav.get('id'),
                    "class": nav.get('class'),
                    "links_count": len(nav.find_all('a'))
                })
            
            # 分析選單項目
            menu_selectors = ['ul.menu', '.navigation', '.nav-menu', '.main-menu']
            for selector in menu_selectors:
                menus = soup.select(selector)
                for menu in menus:
                    items = menu.find_all('li')
                    navigation["menu_items"].extend([
                        item.get_text().strip() for item in items if item.get_text().strip()
                    ])
            
            # 分析麵包屑
            breadcrumb_selectors = ['.breadcrumb', '.breadcrumbs', '[aria-label*="breadcrumb"]']
            for selector in breadcrumb_selectors:
                breadcrumbs = soup.select(selector)
                for breadcrumb in breadcrumbs:
                    items = breadcrumb.find_all(['li', 'a', 'span'])
                    navigation["breadcrumbs"].extend([
                        item.get_text().strip() for item in items if item.get_text().strip()
                    ])
            
            # 收集所有連結
            links = soup.find_all('a', href=True)
            navigation["links"] = [
                {
                    "text": link.get_text().strip(),
                    "href": link.get('href'),
                    "title": link.get('title')
                }
                for link in links[:20]  # 限制數量
            ]
            
            return navigation
            
        except Exception as e:
            print(f"❌ 分析導航結構時發生錯誤: {str(e)}")
            return {}
    
    async def _analyze_forms(self) -> Dict[str, Any]:
        """分析表單元素"""
        try:
            print("📝 分析表單元素...")
            
            page_content = await self.client.get_page_content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            forms_analysis = {
                "forms_count": 0,
                "forms": [],
                "input_types": {},
                "validation": []
            }
            
            forms = soup.find_all('form')
            forms_analysis["forms_count"] = len(forms)
            
            for form in forms:
                form_data = {
                    "id": form.get('id'),
                    "class": form.get('class'),
                    "method": form.get('method', 'GET'),
                    "action": form.get('action'),
                    "inputs": []
                }
                
                # 分析輸入欄位
                inputs = form.find_all(['input', 'textarea', 'select'])
                for inp in inputs:
                    input_type = inp.get('type', 'text')
                    
                    # 統計輸入類型
                    if input_type not in forms_analysis["input_types"]:
                        forms_analysis["input_types"][input_type] = 0
                    forms_analysis["input_types"][input_type] += 1
                    
                    form_data["inputs"].append({
                        "tag": inp.name,
                        "type": input_type,
                        "name": inp.get('name'),
                        "id": inp.get('id'),
                        "required": inp.has_attr('required'),
                        "placeholder": inp.get('placeholder')
                    })
                
                forms_analysis["forms"].append(form_data)
            
            return forms_analysis
            
        except Exception as e:
            print(f"❌ 分析表單元素時發生錯誤: {str(e)}")
            return {}
    
    async def _analyze_interactive_elements(self) -> Dict[str, Any]:
        """分析互動元素"""
        try:
            print("🖱️ 分析互動元素...")
            
            script = """
            const interactive = {
                buttons: 0,
                clickable_elements: 0,
                hover_effects: 0,
                modals: 0,
                dropdowns: 0
            };
            
            // 統計按鈕
            interactive.buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]').length;
            
            // 統計可點擊元素
            const clickable = document.querySelectorAll('[onclick], [data-toggle], [data-target], .clickable, .btn');
            interactive.clickable_elements = clickable.length;
            
            // 檢查模態框
            interactive.modals = document.querySelectorAll('.modal, .popup, [data-modal]').length;
            
            // 檢查下拉選單
            interactive.dropdowns = document.querySelectorAll('.dropdown, .select, select').length;
            
            return interactive;
            """
            
            interactive = await self.client._mcp_evaluate(script)
            return interactive or {}
            
        except Exception as e:
            print(f"❌ 分析互動元素時發生錯誤: {str(e)}")
            return {} 