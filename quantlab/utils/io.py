"""
文件操作工具

提供文件读写、路径处理等工具函数。
"""

import os
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_save_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    backup: bool = True
) -> None:
    """
    安全保存 CSV 文件，支持备份
    
    Args:
        df: 要保存的 DataFrame
        file_path: 文件路径
        backup: 是否备份现有文件
    """
    file_path = Path(file_path)
    
    # 确保目录存在
    ensure_dir(file_path.parent)
    
    # 备份现有文件
    if backup and file_path.exists():
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        file_path.rename(backup_path)
        logger.info(f"Backed up existing file to {backup_path}")
    
    # 保存文件
    df.to_csv(file_path)
    logger.info(f"Saved DataFrame to {file_path}")


def safe_load_csv(
    file_path: Union[str, Path],
    **kwargs
) -> pd.DataFrame:
    """
    安全加载 CSV 文件
    
    Args:
        file_path: 文件路径
        **kwargs: 传递给 pd.read_csv 的参数
        
    Returns:
        pd.DataFrame: 加载的数据
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path, **kwargs)
        logger.info(f"Loaded DataFrame from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {e}")
        raise


def save_json(
    data: Any,
    file_path: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    保存 JSON 文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: 缩进空格数
        ensure_ascii: 是否确保 ASCII 编码
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    
    logger.info(f"Saved JSON data to {file_path}")


def load_json(file_path: Union[str, Path]) -> Any:
    """
    加载 JSON 文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Any: 加载的数据
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded JSON data from {file_path}")
    return data


def save_pickle(
    data: Any,
    file_path: Union[str, Path]
) -> None:
    """
    保存 Pickle 文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)
    
    logger.info(f"Saved pickle data to {file_path}")


def load_pickle(file_path: Union[str, Path]) -> Any:
    """
    加载 Pickle 文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Any: 加载的数据
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    logger.info(f"Loaded pickle data from {file_path}")
    return data


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return 0
    
    return file_path.stat().st_size


def get_file_info(file_path: Union[str, Path]) -> Dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict: 文件信息
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            'exists': False,
            'path': str(file_path),
            'size': 0,
            'modified': None
        }
    
    stat = file_path.stat()
    
    return {
        'exists': True,
        'path': str(file_path),
        'size': stat.st_size,
        'modified': pd.Timestamp(stat.st_mtime, unit='s'),
        'extension': file_path.suffix,
        'name': file_path.name,
        'parent': str(file_path.parent)
    }


def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式
        recursive: 是否递归搜索
        
    Returns:
        List[Path]: 文件路径列表
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def clean_old_files(
    directory: Union[str, Path],
    pattern: str = "*",
    days_old: int = 30,
    dry_run: bool = True
) -> List[Path]:
    """
    清理旧文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式
        days_old: 文件天数阈值
        dry_run: 是否只是预览，不实际删除
        
    Returns:
        List[Path]: 被删除的文件列表
    """
    directory = Path(directory)
    files = list_files(directory, pattern, recursive=True)
    
    cutoff_time = pd.Timestamp.now() - pd.Timedelta(days=days_old)
    old_files = []
    
    for file_path in files:
        if file_path.is_file():
            file_info = get_file_info(file_path)
            if file_info['modified'] < cutoff_time:
                old_files.append(file_path)
    
    if not dry_run:
        for file_path in old_files:
            try:
                file_path.unlink()
                logger.info(f"Deleted old file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
    
    return old_files


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录
    """
    # 查找包含 pyproject.toml 的目录
    current = Path(__file__).parent
    
    while current != current.parent:
        if (current / 'pyproject.toml').exists():
            return current
        current = current.parent
    
    # 如果没找到，返回当前文件所在目录的上级
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    获取数据目录
    
    Returns:
        Path: 数据目录
    """
    project_root = get_project_root()
    data_dir = project_root / 'data'
    ensure_dir(data_dir)
    return data_dir


def get_plots_dir() -> Path:
    """
    获取图表目录
    
    Returns:
        Path: 图表目录
    """
    project_root = get_project_root()
    plots_dir = project_root / 'plots'
    ensure_dir(plots_dir)
    return plots_dir


def get_reports_dir() -> Path:
    """
    获取报告目录
    
    Returns:
        Path: 报告目录
    """
    project_root = get_project_root()
    reports_dir = project_root / 'reports'
    ensure_dir(reports_dir)
    return reports_dir


if __name__ == "__main__":
    # 测试文件操作工具
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # 测试目录创建
    data_dir = get_data_dir()
    plots_dir = get_plots_dir()
    reports_dir = get_reports_dir()
    
    print(f"Data dir: {data_dir}")
    print(f"Plots dir: {plots_dir}")
    print(f"Reports dir: {reports_dir}")
    
    # 测试文件信息
    test_file = project_root / 'README.md'
    if test_file.exists():
        info = get_file_info(test_file)
        print(f"\nFile info for {test_file.name}:")
        print(f"Size: {info['size']} bytes")
        print(f"Modified: {info['modified']}")
    
    # 测试文件列表
    files = list_files(project_root, "*.py")
    print(f"\nFound {len(files)} Python files in project root")
