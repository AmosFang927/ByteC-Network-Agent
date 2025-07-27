import streamlit as st
import requests
import json
import time
from typing import List, Dict, Any

# 页面配置
st.set_page_config(
    page_title="Ollama 管理界面",
    page_icon="🤖",
    layout="wide"
)

# 初始化会话状态
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_model' not in st.session_state:
    st.session_state.current_model = ""

def get_ollama_models() -> List[Dict]:
    """获取已安装的模型列表"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            return response.json().get("models", [])
        return []
    except Exception as e:
        st.error(f"无法连接到 Ollama: {e}")
        return []

def download_model(model_name: str):
    """下载模型"""
    try:
        with st.spinner(f"正在下载模型 {model_name}..."):
            response = requests.post(
                "http://localhost:11434/api/pull",
                json={"name": model_name}
            )
            if response.status_code == 200:
                st.success(f"模型 {model_name} 下载成功！")
            else:
                st.error(f"下载失败: {response.text}")
    except Exception as e:
        st.error(f"下载出错: {e}")

def chat_with_model(model: str, message: str) -> str:
    """与模型对话"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": message,
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json().get("response", "无响应")
        else:
            return f"错误: {response.text}"
    except Exception as e:
        return f"连接错误: {e}"

def main():
    st.title("🤖 Ollama 管理界面")
    st.markdown("---")
    
    # 侧边栏 - 模型管理
    with st.sidebar:
        st.header("📚 模型管理")
        
        # 获取已安装模型
        models = get_ollama_models()
        
        if models:
            st.subheader("已安装的模型:")
            for model in models:
                st.write(f"• {model['name']}")
            
            # 选择当前模型
            model_names = [model['name'] for model in models]
            selected_model = st.selectbox(
                "选择要使用的模型:",
                model_names,
                index=0 if model_names else None
            )
            st.session_state.current_model = selected_model
        else:
            st.warning("没有找到已安装的模型")
        
        st.markdown("---")
        
        # 下载新模型
        st.subheader("下载新模型")
        new_model = st.text_input("输入模型名称 (例如: deepseek-coder:6.7b)")
        if st.button("下载模型") and new_model:
            download_model(new_model)
            st.rerun()
    
    # 主界面 - 聊天
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 聊天界面")
        
        if not st.session_state.current_model:
            st.warning("请先在侧边栏选择一个模型")
        else:
            st.info(f"当前使用模型: {st.session_state.current_model}")
            
            # 聊天输入
            user_message = st.text_area("输入您的问题:", height=100)
            
            if st.button("发送", type="primary") and user_message:
                with st.spinner("正在生成回答..."):
                    response = chat_with_model(st.session_state.current_model, user_message)
                    
                    # 添加到聊天历史
                    st.session_state.chat_history.append({
                        "user": user_message,
                        "assistant": response,
                        "timestamp": time.strftime("%H:%M:%S")
                    })
                
                st.rerun()
    
    with col2:
        st.header("📝 聊天历史")
        
        if st.session_state.chat_history:
            for i, chat in enumerate(st.session_state.chat_history):
                with st.expander(f"对话 {i+1} ({chat['timestamp']})"):
                    st.write(f"**用户:** {chat['user']}")
                    st.write(f"**助手:** {chat['assistant']}")
        else:
            st.info("还没有聊天记录")
    
    # 底部 - 系统信息
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("已安装模型", len(models))
    
    with col2:
        if st.session_state.current_model:
            st.metric("当前模型", st.session_state.current_model)
        else:
            st.metric("当前模型", "未选择")
    
    with col3:
        st.metric("聊天记录", len(st.session_state.chat_history))

if __name__ == "__main__":
    main() 