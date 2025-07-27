#!/usr/bin/env python3
"""
Agent间调用模块 - 实现agent之间的数据流向和调用逻辑
支持数据流向：Input/API → DMP → Reporter
"""

import asyncio
import subprocess
import json
import tempfile
import os
import logging
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class AgentCallingError(Exception):
    """Agent调用错误"""
    pass


class AgentCaller:
    """Agent间调用管理器"""
    
    def __init__(self):
        self.timeout = config.AGENT_CALLING_DEFAULT_TIMEOUT
        self.max_retries = config.AGENT_CALLING_MAX_RETRIES
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'call_history': []
        }
    
    def _find_latest_dmp_output_file(self, platform: str = None) -> Optional[str]:
        """
        查找最新生成的DMP輸出文件
        
        Args:
            platform: 平台名稱，用於匹配文件名模式
            
        Returns:
            最新文件的路徑，如果沒有找到則返回None
        """
        try:
            output_dir = "output"
            if not os.path.exists(output_dir):
                return None
            
            # 構建搜索模式
            if platform:
                pattern = f"{output_dir}/DMP_temp_{platform}_*.xlsx"
            else:
                pattern = f"{output_dir}/DMP_temp_*.xlsx"
            
            # 查找匹配的文件
            matching_files = glob.glob(pattern)
            
            if not matching_files:
                logger.warning(f"⚠️ 沒有找到匹配的DMP輸出文件: {pattern}")
                return None
            
            # 按修改時間排序，取最新的
            latest_file = max(matching_files, key=os.path.getmtime)
            
            logger.info(f"🔍 找到最新DMP輸出文件: {latest_file}")
            return latest_file
            
        except Exception as e:
            logger.error(f"❌ 查找DMP輸出文件失敗: {e}")
            return None
    
    async def call_dmp_agent(self, 
                           platform: str, 
                           days_ago: int = 1,
                           passthrough: bool = False,
                           additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        调用DMP Agent处理数据
        
        Args:
            platform: 平台名称
            days_ago: 天数
            passthrough: 是否启用passthrough模式
            additional_args: 额外的命令行参数
            
        Returns:
            DMP Agent的执行结果
        """
        if not config.ENABLE_AGENT_INTER_CALLING:
            raise AgentCallingError("Agent间调用功能已禁用")
        
        logger.info(f"🔗 调用DMP Agent: platform={platform}, days_ago={days_ago}, passthrough={passthrough}")
        
        # 构建命令
        cmd = [
            'python', 'agents/data_dmp_agent/main.py',
            '--days-ago', str(days_ago)
        ]
        
        # 只在platform不为None时添加platform参数
        if platform:
            cmd.extend(['--platform', platform])
        else:
            # 如果没有platform参数，说明是Data Input Agent调用，使用file数据源
            cmd.extend(['--data-source', 'file'])
        
        if passthrough:
            cmd.append('--passthrough')
        
        if additional_args:
            cmd.extend(additional_args)
        
        # 執行DMP Agent
        result = await self._execute_agent_command('DMP', cmd)
        
        # 🔍 如果是passthrough模式，直接查找最新生成的輸出文件
        if passthrough and result.get('success'):
            output_file_path = self._find_latest_dmp_output_file(platform)
            if output_file_path:
                result['output_file_path'] = output_file_path
                logger.info(f"✅ 成功獲取DMP輸出文件路徑: {output_file_path}")
            else:
                logger.warning("⚠️ 未找到DMP輸出文件")
        
        return result
    
    async def call_reporter_agent(self,
                                platform: str,
                                days_ago: int = 1,
                                output_format: str = None,
                                import_file: str = None,
                                additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        调用Reporter Agent生成报告
        
        Args:
            platform: 平台名称  
            days_ago: 天数
            output_format: 输出格式
            import_file: 从DMP Agent输出的文件导入数据
            additional_args: 额外的命令行参数
            
        Returns:
            Reporter Agent的执行结果
        """
        if not config.ENABLE_REPORTER_AGENT_CALLING:
            raise AgentCallingError("Reporter Agent调用功能已禁用")
        
        logger.info(f"📊 调用Reporter Agent: platform={platform}, days_ago={days_ago}")
        
        # 构建命令 - 修正为正确的子命令格式
        cmd = [
            'python', 'agents/reporter_agent/main.py',
            'generate',  # 使用generate子命令
            '--days-ago', str(days_ago)
        ]
        
        # 只在明确指定时添加partner参数，避免重复
        if platform and platform != 'ALL':  # 避免重复默认的ALL
            cmd.extend(['--partner', platform])
        
        # 添加import文件参数（如果提供）
        if import_file:
            cmd.extend(['--import', import_file])
        
        if additional_args:
            cmd.extend(additional_args)
        
        return await self._execute_agent_command('Reporter', cmd)
    
    async def call_api_agent(self,
                           platform: str,
                           days_ago: int = 1,
                           passthrough: bool = False,
                           reporter_agent: bool = False,
                           additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        调用API Agent获取数据
        
        Args:
            platform: 平台名称
            days_ago: 天数
            passthrough: 是否启用passthrough模式
            reporter_agent: 是否调用Reporter Agent
            additional_args: 额外的命令行参数
            
        Returns:
            API Agent的执行结果
        """
        if not config.ENABLE_AGENT_INTER_CALLING:
            raise AgentCallingError("Agent间调用功能已禁用")
        
        logger.info(f"🚀 调用API Agent: platform={platform}, days_ago={days_ago}")
        
        # 构建命令
        cmd = [
            'python', 'agents/api_agent/main.py',
            '--platform', platform,
            '--days-ago', str(days_ago)
        ]
        
        if passthrough:
            cmd.append('--passthrough')
        
        if reporter_agent:
            cmd.append('--reporter-agent')
        
        if additional_args:
            cmd.extend(additional_args)
        
        return await self._execute_agent_command('API', cmd)
    
    async def execute_data_flow_pipeline(self,
                                       platform: str,
                                       days_ago: int = 1,
                                       use_passthrough: bool = False) -> Dict[str, Any]:
        """
        执行完整的数据流向管道: Input/API → DMP → Reporter
        
        Args:
            platform: 平台名称
            days_ago: 天数
            use_passthrough: 是否使用passthrough模式
            
        Returns:
            整个管道的执行结果
        """
        logger.info("🔄 开始执行数据流向管道")
        logger.info(f"   流向: API Agent → DMP Agent → Reporter Agent")
        logger.info(f"   平台: {platform}, 天数: {days_ago}, Passthrough: {use_passthrough}")
        
        pipeline_result = {
            'success': False,
            'pipeline_start_time': datetime.now().isoformat(),
            'steps': {},
            'errors': []
        }
        
        try:
            # 步骤1: API Agent获取数据
            logger.info("📥 步骤1: API Agent数据获取")
            api_result = await self.call_api_agent(
                platform=platform,
                days_ago=days_ago,
                passthrough=use_passthrough,
                reporter_agent=False  # 在管道中手动控制Reporter调用
            )
            pipeline_result['steps']['api_agent'] = api_result
            
            if not api_result.get('success', False):
                raise AgentCallingError(f"API Agent执行失败: {api_result.get('error', 'Unknown error')}")
            
            # 步骤2: DMP Agent处理数据  
            logger.info("🔄 步骤2: DMP Agent数据处理")
            dmp_result = await self.call_dmp_agent(
                platform=platform,
                days_ago=days_ago,
                passthrough=use_passthrough
            )
            pipeline_result['steps']['dmp_agent'] = dmp_result
            
            if not dmp_result.get('success', False):
                raise AgentCallingError(f"DMP Agent执行失败: {dmp_result.get('error', 'Unknown error')}")
            
            # 步骤3: Reporter Agent生成报告
            logger.info("📊 步骤3: Reporter Agent报告生成")
            reporter_result = await self.call_reporter_agent(
                platform=platform,
                days_ago=days_ago,
                output_format='json'
            )
            pipeline_result['steps']['reporter_agent'] = reporter_result
            
            if not reporter_result.get('success', False):
                logger.warning(f"Reporter Agent执行失败，但管道继续: {reporter_result.get('error', 'Unknown error')}")
            
            pipeline_result['success'] = True
            pipeline_result['pipeline_end_time'] = datetime.now().isoformat()
            
            logger.info("✅ 数据流向管道执行完成")
            logger.info(f"   API记录: {api_result.get('total_records', 0)}")
            logger.info(f"   DMP处理: {dmp_result.get('fetched_count', 0)} 获取, {dmp_result.get('stored_count', 0)} 存储")
            
        except Exception as e:
            error_msg = f"数据流向管道执行失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            pipeline_result['errors'].append(error_msg)
            pipeline_result['pipeline_end_time'] = datetime.now().isoformat()
        
        return pipeline_result
    
    async def _execute_agent_command(self, agent_name: str, cmd: List[str]) -> Dict[str, Any]:
        """
        执行agent命令
        
        Args:
            agent_name: Agent名称
            cmd: 命令列表
            
        Returns:
            执行结果
        """
        self.stats['total_calls'] += 1
        
        call_record = {
            'agent': agent_name,
            'command': ' '.join(cmd),
            'start_time': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            logger.info(f"🔄 执行{agent_name} Agent命令: {' '.join(cmd)}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # 等待执行完成
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            call_record['end_time'] = datetime.now().isoformat()
            call_record['return_code'] = process.returncode
            call_record['stdout'] = stdout.decode('utf-8') if stdout else ""
            call_record['stderr'] = stderr.decode('utf-8') if stderr else ""
            
            if process.returncode == 0:
                call_record['success'] = True
                self.stats['successful_calls'] += 1
                logger.info(f"✅ {agent_name} Agent执行成功")
                
                return {
                    'success': True,
                    'agent': agent_name,
                    'return_code': process.returncode,
                    'stdout': call_record['stdout'],
                    'stderr': call_record['stderr']
                }
            else:
                self.stats['failed_calls'] += 1
                error_msg = f"{agent_name} Agent执行失败 (退出码: {process.returncode})"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   错误输出: {call_record['stderr']}")
                
                return {
                    'success': False,
                    'agent': agent_name,
                    'error': error_msg,
                    'return_code': process.returncode,
                    'stdout': call_record['stdout'],
                    'stderr': call_record['stderr']
                }
                
        except asyncio.TimeoutError:
            error_msg = f"{agent_name} Agent执行超时 ({self.timeout}秒)"
            logger.error(f"❌ {error_msg}")
            call_record['error'] = error_msg
            self.stats['failed_calls'] += 1
            
            return {
                'success': False,
                'agent': agent_name,
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"{agent_name} Agent执行异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            call_record['error'] = error_msg
            self.stats['failed_calls'] += 1
            
            return {
                'success': False,
                'agent': agent_name,
                'error': error_msg
            }
        finally:
            self.stats['call_history'].append(call_record)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取调用统计信息"""
        return {
            'stats': self.stats,
            'success_rate': (self.stats['successful_calls'] / self.stats['total_calls'] * 100) 
                           if self.stats['total_calls'] > 0 else 0
        }
    
    def print_statistics(self):
        """打印调用统计信息"""
        stats = self.get_statistics()
        logger.info("=" * 60)
        logger.info("🔗 Agent调用统计")
        logger.info("=" * 60)
        logger.info(f"总调用次数: {stats['stats']['total_calls']}")
        logger.info(f"成功调用: {stats['stats']['successful_calls']}")
        logger.info(f"失败调用: {stats['stats']['failed_calls']}")
        logger.info(f"成功率: {stats['success_rate']:.1f}%")
        logger.info("=" * 60)


# 全局实例
agent_caller = AgentCaller()


# 便捷函数
async def call_dmp_agent(platform: str, days_ago: int = 1, passthrough: bool = False, **kwargs) -> Dict[str, Any]:
    """便捷函数：调用DMP Agent"""
    return await agent_caller.call_dmp_agent(platform, days_ago, passthrough, **kwargs)


async def call_reporter_agent(platform: str, days_ago: int = 1, **kwargs) -> Dict[str, Any]:
    """便捷函数：调用Reporter Agent"""
    return await agent_caller.call_reporter_agent(platform, days_ago, **kwargs)


async def call_api_agent(platform: str, days_ago: int = 1, passthrough: bool = False, **kwargs) -> Dict[str, Any]:
    """便捷函数：调用API Agent"""
    return await agent_caller.call_api_agent(platform, days_ago, passthrough, **kwargs)


async def execute_data_flow_pipeline(platform: str, days_ago: int = 1, use_passthrough: bool = False) -> Dict[str, Any]:
    """便捷函数：执行完整数据流向管道"""
    return await agent_caller.execute_data_flow_pipeline(platform, days_ago, use_passthrough) 