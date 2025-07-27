import os
import logging
from typing import List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """初始化 RAG 系统"""
        self.persist_directory = persist_directory
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.llm = Ollama(model="deepseek-coder:6.7b", temperature=0.1)
        
        # 初始化向量数据库
        self.vectorstore = None
        self.qa_chain = None
        
        # 文档处理器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """初始化向量数据库"""
        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                client_settings=Settings(
                    anonymized_telemetry=False
                )
            )
            logger.info("✅ 向量数据库初始化成功")
        except Exception as e:
            logger.error(f"❌ 向量数据库初始化失败: {e}")
            raise
    
    def load_documents(self, file_paths: List[str]) -> List[Document]:
        """加载文档"""
        documents = []
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if not path.exists():
                    import traceback
                    tb = traceback.format_stack()
                    logger.warning(f"⚠️ 文件不存在: {file_path}\n调用栈:\n{''.join(tb)}")
                    continue
                
                # 根据文件类型选择加载器
                if path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(path))
                elif path.suffix.lower() in ['.docx', '.doc']:
                    loader = Docx2txtLoader(str(path))
                elif path.suffix.lower() == '.md':
                    loader = UnstructuredMarkdownLoader(str(path))
                elif path.suffix.lower() in ['.txt', '.text']:
                    loader = TextLoader(str(path))
                else:
                    logger.warning(f"⚠️ 不支持的文件类型: {path.suffix}")
                    continue
                
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"✅ 成功加载文档: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ 加载文档失败 {file_path}: {e}")
        
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """处理文档分割"""
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"✅ 文档分割完成，共 {len(split_docs)} 个片段")
            return split_docs
        except Exception as e:
            logger.error(f"❌ 文档分割失败: {e}")
            raise
    
    def add_documents(self, file_paths: List[str]):
        """添加文档到知识库"""
        try:
            # 加载文档
            documents = self.load_documents(file_paths)
            if not documents:
                logger.warning("⚠️ 没有可加载的文档")
                return
            
            # 处理文档
            split_docs = self.process_documents(documents)
            
            # 添加到向量数据库
            self.vectorstore.add_documents(split_docs)
            self.vectorstore.persist()
            
            logger.info(f"✅ 成功添加 {len(split_docs)} 个文档片段到知识库")
            
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {e}")
            raise
    
    def setup_qa_chain(self):
        """设置问答链"""
        try:
            # 自定义提示模板
            prompt_template = """你是一个专业的知识库助手。请基于以下上下文信息回答问题。

上下文信息:
{context}

问题: {question}

请提供准确、详细的回答。如果上下文中没有相关信息，请明确说明。

回答:"""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            # 创建检索问答链
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_kwargs={"k": 5}
                ),
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True
            )
            
            logger.info("✅ QA 链设置完成")
            
        except Exception as e:
            logger.error(f"❌ 设置 QA 链失败: {e}")
            raise
    
    def query(self, question: str) -> Dict[str, Any]:
        """查询知识库"""
        try:
            if not self.qa_chain:
                self.setup_qa_chain()
            
            # 执行查询
            result = self.qa_chain({"query": question})
            
            return {
                "answer": result["result"],
                "sources": [doc.metadata for doc in result["source_documents"]],
                "question": question
            }
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            return {
                "answer": f"查询失败: {str(e)}",
                "sources": [],
                "question": question
            }
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """获取知识库信息"""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "total_documents": count,
                "persist_directory": self.persist_directory,
                "embedding_model": "nomic-embed-text",
                "llm_model": "deepseek-coder:6.7b"
            }
        except Exception as e:
            logger.error(f"❌ 获取知识库信息失败: {e}")
            return {} 