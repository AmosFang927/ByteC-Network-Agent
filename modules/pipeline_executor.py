#!/usr/bin/env python3
"""
Pipeline Executor - 分階段執行器
支持斷點續傳、並行處理和狀態持久化
"""

import os
import json
import time
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from utils.logger import print_step
import config

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageResult:
    """階段執行結果"""
    stage_name: str
    status: StageStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PipelineConfig:
    """管道配置"""
    pipeline_id: str
    stages: List[str]
    max_parallel_stages: int = 3
    enable_checkpoint: bool = True
    checkpoint_dir: str = "checkpoints"
    timeout_per_stage: int = 1800  # 30分鐘每階段
    retry_failed_stages: bool = True
    max_retries: int = 2

class PipelineExecutor:
    """分階段管道執行器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results: Dict[str, StageResult] = {}
        self.stage_functions: Dict[str, Callable] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.checkpoint_file = os.path.join(config.checkpoint_dir, f"{config.pipeline_id}_checkpoint.json")
        
        # 創建檢查點目錄
        os.makedirs(config.checkpoint_dir, exist_ok=True)
        
        # 加載之前的檢查點
        self._load_checkpoint()
    
    def register_stage(self, stage_name: str, func: Callable, dependencies: List[str] = None):
        """註冊階段函數"""
        self.stage_functions[stage_name] = func
        self.dependencies[stage_name] = dependencies or []
        
        # 初始化階段結果
        if stage_name not in self.results:
            self.results[stage_name] = StageResult(
                stage_name=stage_name,
                status=StageStatus.PENDING
            )
    
    def _load_checkpoint(self):
        """加載檢查點"""
        if not self.config.enable_checkpoint or not os.path.exists(self.checkpoint_file):
            return
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # 恢復階段結果
            for stage_name, stage_data in checkpoint_data.get('results', {}).items():
                # 轉換時間字符串回datetime對象
                if stage_data.get('start_time'):
                    stage_data['start_time'] = datetime.fromisoformat(stage_data['start_time'])
                if stage_data.get('end_time'):
                    stage_data['end_time'] = datetime.fromisoformat(stage_data['end_time'])
                
                # 轉換狀態
                stage_data['status'] = StageStatus(stage_data['status'])
                
                self.results[stage_name] = StageResult(**stage_data)
            
            print_step("檢查點恢復", f"已恢復 {len(self.results)} 個階段的狀態")
            
        except Exception as e:
            print_step("檢查點錯誤", f"加載檢查點失敗: {str(e)}")
            self.results = {}
    
    def _save_checkpoint(self):
        """保存檢查點"""
        if not self.config.enable_checkpoint:
            return
        
        try:
            # 準備序列化數據
            checkpoint_data = {
                'pipeline_id': self.config.pipeline_id,
                'timestamp': datetime.now().isoformat(),
                'results': {}
            }
            
            for stage_name, result in self.results.items():
                stage_dict = asdict(result)
                
                # 轉換datetime對象為字符串
                if stage_dict['start_time']:
                    stage_dict['start_time'] = stage_dict['start_time'].isoformat()
                if stage_dict['end_time']:
                    stage_dict['end_time'] = stage_dict['end_time'].isoformat()
                
                # 轉換狀態為字符串
                stage_dict['status'] = stage_dict['status'].value
                
                checkpoint_data['results'][stage_name] = stage_dict
            
            # 寫入檢查點文件
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print_step("檢查點錯誤", f"保存檢查點失敗: {str(e)}")
    
    def _can_execute_stage(self, stage_name: str) -> bool:
        """檢查階段是否可以執行"""
        stage_result = self.results.get(stage_name)
        
        # 如果階段已完成，跳過
        if stage_result and stage_result.status == StageStatus.COMPLETED:
            return False
        
        # 檢查依賴是否完成
        for dep in self.dependencies.get(stage_name, []):
            dep_result = self.results.get(dep)
            if not dep_result or dep_result.status != StageStatus.COMPLETED:
                return False
        
        return True
    
    def _execute_stage(self, stage_name: str, context: Dict[str, Any]) -> StageResult:
        """執行單個階段"""
        stage_func = self.stage_functions.get(stage_name)
        if not stage_func:
            raise ValueError(f"未找到階段函數: {stage_name}")
        
        result = self.results[stage_name]
        result.status = StageStatus.RUNNING
        result.start_time = datetime.now()
        
        print_step(f"階段開始", f"🚀 開始執行階段: {stage_name}")
        
        try:
            # 執行階段函數
            stage_output = stage_func(context)
            
            # 更新結果
            result.status = StageStatus.COMPLETED
            result.output = stage_output
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            print_step(f"階段完成", f"✅ 階段 {stage_name} 完成，耗時 {result.duration:.2f}s")
            
            # 將輸出添加到上下文
            context[f"{stage_name}_output"] = stage_output
            
        except Exception as e:
            result.status = StageStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            print_step(f"階段失敗", f"❌ 階段 {stage_name} 失敗: {str(e)}")
        
        # 保存檢查點
        self._save_checkpoint()
        
        return result
    
    async def execute_async(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """異步執行管道"""
        context = initial_context or {}
        context['pipeline_id'] = self.config.pipeline_id
        context['start_time'] = datetime.now()
        
        print_step("管道開始", f"🚀 開始執行管道: {self.config.pipeline_id}")
        
        # 使用線程池執行階段
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_parallel_stages) as executor:
            
            # 執行階段直到所有階段完成
            while True:
                # 找到可執行的階段
                executable_stages = [
                    stage for stage in self.config.stages
                    if self._can_execute_stage(stage)
                ]
                
                if not executable_stages:
                    # 檢查是否所有階段都完成
                    remaining_stages = [
                        stage for stage in self.config.stages
                        if self.results[stage].status != StageStatus.COMPLETED
                    ]
                    
                    if not remaining_stages:
                        break  # 所有階段完成
                    
                    # 有階段未完成但無法執行，可能是依賴問題
                    print_step("管道等待", f"等待依賴完成，剩餘階段: {remaining_stages}")
                    await asyncio.sleep(1)
                    continue
                
                # 並行執行階段
                print_step("並行執行", f"並行執行階段: {executable_stages}")
                
                # 提交任務到線程池
                future_to_stage = {
                    executor.submit(self._execute_stage, stage, context): stage
                    for stage in executable_stages
                }
                
                # 等待任務完成
                for future in concurrent.futures.as_completed(future_to_stage):
                    stage_name = future_to_stage[future]
                    try:
                        result = future.result(timeout=self.config.timeout_per_stage)
                        print_step("階段結果", f"階段 {stage_name} 狀態: {result.status.value}")
                    except concurrent.futures.TimeoutError:
                        print_step("階段超時", f"階段 {stage_name} 執行超時")
                        self.results[stage_name].status = StageStatus.FAILED
                        self.results[stage_name].error = "執行超時"
                    except Exception as e:
                        print_step("階段異常", f"階段 {stage_name} 執行異常: {str(e)}")
        
        # 計算總執行時間
        context['end_time'] = datetime.now()
        context['total_duration'] = (context['end_time'] - context['start_time']).total_seconds()
        
        # 統計結果
        completed_stages = [s for s in self.results.values() if s.status == StageStatus.COMPLETED]
        failed_stages = [s for s in self.results.values() if s.status == StageStatus.FAILED]
        
        print_step("管道完成", f"✅ 管道執行完成，成功: {len(completed_stages)}, 失敗: {len(failed_stages)}")
        
        return context
    
    def execute(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """同步執行管道"""
        return asyncio.run(self.execute_async(initial_context))
    
    def get_status(self) -> Dict[str, Any]:
        """獲取管道狀態"""
        total_stages = len(self.config.stages)
        completed_stages = len([s for s in self.results.values() if s.status == StageStatus.COMPLETED])
        failed_stages = len([s for s in self.results.values() if s.status == StageStatus.FAILED])
        running_stages = len([s for s in self.results.values() if s.status == StageStatus.RUNNING])
        
        return {
            'pipeline_id': self.config.pipeline_id,
            'total_stages': total_stages,
            'completed_stages': completed_stages,
            'failed_stages': failed_stages,
            'running_stages': running_stages,
            'progress_percent': (completed_stages / total_stages * 100) if total_stages > 0 else 0,
            'stage_details': {name: result.status.value for name, result in self.results.items()}
        }
    
    def reset_failed_stages(self):
        """重置失敗的階段"""
        for result in self.results.values():
            if result.status == StageStatus.FAILED:
                result.status = StageStatus.PENDING
                result.error = None
                result.start_time = None
                result.end_time = None
                result.duration = None
        
        self._save_checkpoint()
        print_step("重置完成", "已重置所有失敗的階段")
    
    def cleanup_checkpoint(self):
        """清理檢查點文件"""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print_step("檢查點清理", "已清理檢查點文件") 