"""
任务调度模块
管理任务队列和执行
"""

import uuid
import threading
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import get_config, get_logger
from utils.exceptions import TaskError

logger = get_logger()


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class TaskType(Enum):
    """任务类型"""
    IMAGE = auto()
    VIDEO = auto()
    BATCH = auto()


@dataclass
class Task:
    """任务数据类"""
    id: str
    type: TaskType
    input_path: str
    output_path: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class TaskScheduler:
    """任务调度器"""
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        queue_size: Optional[int] = None
    ):
        """
        初始化任务调度器
        
        Args:
            max_workers: 最大工作线程数
            queue_size: 任务队列大小
        """
        self.max_workers = max_workers or self._get_max_workers()
        self.queue_size = queue_size or get_config('processing.threading.queue_size', 10)

        # 任务存储
        self._tasks: Dict[str, Task] = {}
        self._task_queue: List[str] = []

        # 线程池
        self._executor: Optional[ThreadPoolExecutor] = None

        # 回调函数
        self._on_task_started: Optional[Callable[[Task], None]] = None
        self._on_task_completed: Optional[Callable[[Task], None]] = None
        self._on_task_failed: Optional[Callable[[Task], None]] = None
        self._on_progress_update: Optional[Callable[[Task], None]] = None

        # 线程锁，保护共享状态
        self._lock = threading.Lock()

        self._running = False

        logger.debug(f"初始化 TaskScheduler: max_workers={self.max_workers}")
    
    def _get_max_workers(self) -> int:
        """获取最大工作线程数"""
        import os
        
        config_value = get_config('processing.threading.max_workers', 'auto')
        
        if config_value == 'auto':
            return os.cpu_count() or 4
        
        try:
            return int(config_value)
        except (TypeError, ValueError):
            return os.cpu_count() or 4
    
    def set_callbacks(
        self,
        on_started: Optional[Callable[[Task], None]] = None,
        on_completed: Optional[Callable[[Task], None]] = None,
        on_failed: Optional[Callable[[Task], None]] = None,
        on_progress: Optional[Callable[[Task], None]] = None
    ):
        """
        设置回调函数
        
        Args:
            on_started: 任务开始回调
            on_completed: 任务完成回调
            on_failed: 任务失败回调
            on_progress: 进度更新回调
        """
        self._on_task_started = on_started
        self._on_task_completed = on_completed
        self._on_task_failed = on_failed
        self._on_progress_update = on_progress
    
    def add_task(
        self,
        task_type: TaskType,
        input_path: str,
        output_path: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加任务
        
        Args:
            task_type: 任务类型
            input_path: 输入路径
            output_path: 输出路径
            params: 任务参数
            
        Returns:
            任务ID
        """
        with self._lock:
            if len(self._task_queue) >= self.queue_size:
                raise TaskError(f"任务队列已满 (最大 {self.queue_size})")

            task_id = str(uuid.uuid4())

            task = Task(
                id=task_id,
                type=task_type,
                input_path=input_path,
                output_path=output_path,
                params=params or {}
            )

            self._tasks[task_id] = task
            self._task_queue.append(task_id)

            logger.debug(f"添加任务: {task_id}, type={task_type.name}")

            return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象或 None
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        with self._lock:
            return list(self._tasks.values())
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待处理任务"""
        with self._lock:
            return [
                self._tasks[tid]
                for tid in self._task_queue
                if self._tasks[tid].status == TaskStatus.PENDING
            ]
    
    def get_running_tasks(self) -> List[Task]:
        """获取运行中任务"""
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == TaskStatus.RUNNING
            ]
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成任务"""
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == TaskStatus.COMPLETED
            ]

    def get_failed_tasks(self) -> List[Task]:
        """获取失败任务"""
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == TaskStatus.FAILED
            ]
    
    def update_progress(self, task_id: str, progress: int, message: str = ""):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度 (0-100)
            message: 进度消息
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.progress = min(100, max(0, progress))
                if message:
                    task.message = message

                if self._on_progress_update:
                    self._on_progress_update(task)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        with self._lock:
            task = self._tasks.get(task_id)

            if not task:
                return False

            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                if task_id in self._task_queue:
                    self._task_queue.remove(task_id)
                logger.debug(f"取消任务: {task_id}")
                return True

            return False
    
    def remove_task(self, task_id: str):
        """
        移除任务

        Args:
            task_id: 任务ID
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                if task_id in self._task_queue:
                    self._task_queue.remove(task_id)

    def clear_completed(self):
        """清除已完成的任务"""
        with self._lock:
            completed_ids = [
                task.id for task in self._tasks.values()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]

            for task_id in completed_ids:
                if task_id in self._tasks:
                    del self._tasks[task_id]
                if task_id in self._task_queue:
                    self._task_queue.remove(task_id)
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._running = True
        
        logger.info("任务调度器已启动")
    
    def stop(self, wait: bool = True):
        """
        停止调度器
        
        Args:
            wait: 是否等待任务完成
        """
        if not self._running:
            return
        
        self._running = False
        
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
        
        logger.info("任务调度器已停止")
    
    def execute_task(
        self,
        task_id: str,
        process_func: Callable[[Task], None]
    ):
        """
        执行任务

        Args:
            task_id: 任务ID
            process_func: 处理函数
        """
        with self._lock:
            task = self._tasks.get(task_id)

            if not task or task.status != TaskStatus.PENDING:
                return

            # 更新状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            if self._on_task_started:
                self._on_task_started(task)

        logger.debug(f"开始执行任务: {task_id}")

        try:
            # 执行任务（不持有锁，避免阻塞其他操作）
            process_func(task)

            # 更新成功状态
            with self._lock:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.completed_at = datetime.now()

            if self._on_task_completed:
                self._on_task_completed(task)

            logger.debug(f"任务完成: {task_id}")

        except Exception as e:
            # 更新失败状态
            with self._lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()

            if self._on_task_failed:
                self._on_task_failed(task)

            logger.error(f"任务失败: {task_id} - {e}")
    
    def submit_task(
        self,
        task_id: str,
        process_func: Callable[[Task], None]
    ):
        """
        提交任务到线程池
        
        Args:
            task_id: 任务ID
            process_func: 处理函数
        """
        if not self._executor:
            raise TaskError("调度器未启动")
        
        self._executor.submit(self.execute_task, task_id, process_func)
