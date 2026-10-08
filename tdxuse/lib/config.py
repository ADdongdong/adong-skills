"""
TDX DLL 路径配置文件
支持动态配置和自动检测
"""

import json
import os
from pathlib import Path

# 默认DLL路径
DEFAULT_DLL_PATH = "C:/new_tdx64/PYPlugins/TPythClient.dll"

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "tdx_config.json"

# 常见通达信安装路径
COMMON_PATHS = [
    "C:/new_tdx64/PYPlugins/TPythClient.dll",
    "C:/new_tdx/PYPlugins/TPythClient.dll",
    "D:/new_tdx64/PYPlugins/TPythClient.dll",
    "D:/new_tdx/PYPlugins/TPythClient.dll",
    "E:/new_tdx64/PYPlugins/TPythClient.dll",
    "E:/new_tdx/PYPlugins/TPythClient.dll",
]


def find_dll():
    """自动查找DLL文件"""
    # 先检查已配置的路径
    config = load_config()
    if config.get("dll_path"):
        if Path(config["dll_path"]).exists():
            return config["dll_path"]
    
    # 检查常见路径
    for path in COMMON_PATHS:
        if Path(path).exists():
            return path
    
    return None


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def set_dll_path(path):
    """设置DLL路径"""
    config = load_config()
    config["dll_path"] = path
    save_config(config)


def get_dll_path():
    """获取DLL路径，如果不存在则返回None"""
    dll_path = find_dll()
    if dll_path:
        return dll_path
    return None


def validate_dll_path(path):
    """验证DLL路径是否有效"""
    path_obj = Path(path)
    if not path_obj.exists():
        return False, f"文件不存在: {path}"
    if not path_obj.is_file():
        return False, f"路径不是文件: {path}"
    if path_obj.name != "TPythClient.dll":
        return False, f"文件名不正确，应为 TPythClient.dll: {path_obj.name}"
    return True, "验证通过"


def prompt_for_dll_path():
    """
    提示用户输入DLL路径
    返回验证通过的路径，或None
    """
    print("=" * 60)
    print("未找到通达信 DLL 文件 (TPythClient.dll)")
    print("=" * 60)
    print("\n请提供通达信金融终端的安装路径。")
    print("DLL 文件通常位于: <通达信安装目录>/PYPlugins/TPythClient.dll")
    print("\n常见路径示例:")
    for i, path in enumerate(COMMON_PATHS[:3], 1):
        print(f"  {i}. {path}")
    print("\n请输入完整的 DLL 文件路径:")
    return None
