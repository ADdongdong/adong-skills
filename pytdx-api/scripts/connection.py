#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytdx 连接管理模块
提供智能连接池、服务器选择、错误恢复等功能
"""

import time
import threading
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

try:
    from pytdx.hq import TdxHq_API
    from pytdx.config.hosts import hq_hosts
    PYTDX_AVAILABLE = True
except ImportError:
    PYTDX_AVAILABLE = False
    print("警告: pytdx 库未安装，相关功能不可用")


class ConnectionMode(Enum):
    """连接模式"""
    SHORT = "short"      # 短连接（按需连接，用完即关）
    LONG = "long"        # 长连接（保持连接，适合监控）
    POOL = "pool"        # 连接池（连接复用）
    ADAPTIVE = "adaptive" # 自适应（根据使用频率决策）


@dataclass
class ServerInfo:
    """服务器信息"""
    ip: str
    port: int
    weight: float = 1.0
    last_connect_time: float = 0.0
    connect_success_count: int = 0
    connect_fail_count: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        total = self.connect_success_count + self.connect_fail_count
        return self.connect_success_count / total if total > 0 else 0.0
    
    @property
    def score(self) -> float:
        """计算服务器综合评分"""
        if self.connect_fail_count > 3:
            return 0.0
        
        # 基础分 = 权重 * 成功率（无历史记录时使用权重作为初始分数）
        if self.connect_success_count + self.connect_fail_count == 0:
            base_score = self.weight  # 没有历史记录时，直接使用权重
        else:
            base_score = self.weight * self.success_rate
        
        # 响应时间惩罚（时间越短越好）
        time_penalty = 1.0 / (1.0 + self.avg_response_time) if self.avg_response_time > 0 else 1.0
        
        # 新鲜度奖励（最近使用过的服务器）
        time_since_last = time.time() - self.last_connect_time
        freshness = 1.0 / (1.0 + time_since_last / 3600)  # 1小时内使用过有奖励
        
        return base_score * time_penalty * freshness


class PyTdxConnection:
    """pytdx 连接包装器"""
    
    def __init__(self, api: TdxHq_API, server_ip: str, server_port: int):
        self.api = api
        self.server_ip = server_ip
        self.server_port = server_port
        self.create_time = time.time()
        self.last_used = time.time()
        self.use_count = 0
        self.error_count = 0
        self.mode = "pool"  # 连接模式: short/long/pool
        self._lock = threading.RLock()
    
    def is_valid(self) -> bool:
        """检查连接是否仍然有效"""
        try:
            # 简单检查：尝试获取一个简单数据
            with self._lock:
                self.api.do_heartbeat()
            return True
        except:
            return False
    
    def update_usage(self):
        """更新使用时间"""
        with self._lock:
            self.last_used = time.time()
            self.use_count += 1
    
    def record_error(self):
        """记录错误"""
        with self._lock:
            self.error_count += 1


class ConnectionPool:
    """智能连接池"""
    
    def __init__(self, mode: ConnectionMode = ConnectionMode.ADAPTIVE):
        self.mode = mode
        self._pool: Dict[str, PyTdxConnection] = {}  # key: "ip:port" -> connection
        self._server_list: List[ServerInfo] = self._init_server_list()
        self._lock = threading.RLock()
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "connection_errors": 0,
            "avg_connection_time_ms": 0.0,
        }
    
    def _init_server_list(self) -> List[ServerInfo]:
        """初始化服务器列表"""
        servers = []
        
        # 从pytdx配置获取服务器列表
        if PYTDX_AVAILABLE and hasattr(hq_hosts, '__iter__'):
            for host in hq_hosts:
                if isinstance(host, (list, tuple)) and len(host) >= 2:
                    ip, port = host[0], host[1]
                    servers.append(ServerInfo(ip=ip, port=port, weight=0.8))
        
        # 添加我们测试的最优服务器（优先级最高）
        optimal_servers = [
            ('115.238.56.198', 7709, 1.0),  # 测试最优
            ('119.147.212.81', 7709, 0.9),
            ('218.75.126.9', 7709, 0.8),
        ]
        
        for ip, port, weight in optimal_servers:
            # 避免重复
            if not any(s.ip == ip and s.port == port for s in servers):
                servers.append(ServerInfo(ip=ip, port=port, weight=weight))
        
        # 如果没有找到服务器，使用默认值
        if not servers:
            servers.append(ServerInfo(ip='115.238.56.198', port=7709, weight=1.0))
        
        return servers
    
    def _select_best_server(self) -> Optional[Tuple[str, int]]:
        """选择最佳服务器"""
        if not self._server_list:
            return None
        
        # 计算每个服务器的评分
        scored_servers = [(server.score, server) for server in self._server_list]
        scored_servers.sort(reverse=True, key=lambda x: x[0])
        
        # 选择评分最高的服务器
        best_score, best_server = scored_servers[0]
        
        if best_score <= 0:
            return None
        
        return best_server.ip, best_server.port
    
    def _update_server_stats(self, server_ip: str, server_port: int, 
                            success: bool, response_time_ms: float = 0.0):
        """更新服务器统计信息"""
        for server in self._server_list:
            if server.ip == server_ip and server.port == server_port:
                server.last_connect_time = time.time()
                if success:
                    server.connect_success_count += 1
                    # 更新平均响应时间（移动平均）
                    if server.avg_response_time == 0:
                        server.avg_response_time = response_time_ms
                    else:
                        server.avg_response_time = 0.7 * server.avg_response_time + 0.3 * response_time_ms
                else:
                    server.connect_fail_count += 1
                break
    
    def _create_connection(self, server_ip: str, server_port: int) -> Optional[PyTdxConnection]:
        """创建新连接"""
        if not PYTDX_AVAILABLE:
            return None
        
        start_time = time.time()
        try:
            api = TdxHq_API(multithread=True, heartbeat=False, auto_retry=True, raise_exception=False)
            
            # 连接服务器
            success = api.connect(server_ip, server_port, time_out=5.0)
            connect_time = (time.time() - start_time) * 1000
            
            if success:
                conn = PyTdxConnection(api, server_ip, server_port)
                key = f"{server_ip}:{server_port}"
                
                with self._lock:
                    self._pool[key] = conn
                    self._stats["total_connections"] += 1
                    self._stats["active_connections"] += 1
                    self._stats["avg_connection_time_ms"] = (
                        0.7 * self._stats["avg_connection_time_ms"] + 0.3 * connect_time
                    )
                
                # 更新服务器统计
                self._update_server_stats(server_ip, server_port, True, connect_time)
                return conn
            else:
                self._update_server_stats(server_ip, server_port, False)
                return None
                
        except Exception as e:
            connect_time = (time.time() - start_time) * 1000
            self._update_server_stats(server_ip, server_port, False, connect_time)
            with self._lock:
                self._stats["connection_errors"] += 1
            return None
    
    def _get_from_pool(self, server_ip: str, server_port: int) -> Optional[PyTdxConnection]:
        """从连接池获取连接"""
        key = f"{server_ip}:{server_port}"
        
        with self._lock:
            conn = self._pool.get(key)
            
            if conn and conn.is_valid():
                conn.update_usage()
                return conn
        
        return None
    
    def get_connection(self, preferred_server: Optional[Tuple[str, int]] = None,
                      mode: Optional[ConnectionMode] = None) -> Optional[PyTdxConnection]:
        """
        获取连接
        
        Args:
            preferred_server: 首选服务器 (ip, port)，为None时自动选择
            mode: 连接模式，为None时使用实例默认模式
        
        Returns:
            PyTdxConnection 对象，或 None（失败）
        """
        if mode is None:
            mode = self.mode
        
        # 选择服务器
        if preferred_server:
            server_ip, server_port = preferred_server
        else:
            server = self._select_best_server()
            if not server:
                return None
            server_ip, server_port = server
        
        # 根据模式处理
        if mode == ConnectionMode.SHORT:
            # 短连接模式：每次都创建新连接，不放入池中
            conn = self._create_connection(server_ip, server_port)
            if conn:
                conn.mode = "short"  # 标记为短连接
            return conn
        
        elif mode == ConnectionMode.LONG:
            # 长连接模式：使用心跳保持连接
            # 这里实际实现与POOL类似，但会设置heartbeat=True
            # 简化实现：使用POOL模式，但在创建连接时设置heartbeat
            conn = self._get_from_pool(server_ip, server_port)
            if conn:
                return conn
            
            # 创建新连接（带心跳）
            if not PYTDX_AVAILABLE:
                return None
            
            start_time = time.time()
            try:
                api = TdxHq_API(multithread=True, heartbeat=True, auto_retry=True, raise_exception=False)
                success = api.connect(server_ip, server_port, time_out=5.0)
                connect_time = (time.time() - start_time) * 1000
                
                if success:
                    conn = PyTdxConnection(api, server_ip, server_port)
                    key = f"{server_ip}:{server_port}"
                    
                    with self._lock:
                        self._pool[key] = conn
                        self._stats["total_connections"] += 1
                        self._stats["active_connections"] += 1
                    
                    self._update_server_stats(server_ip, server_port, True, connect_time)
                    return conn
                else:
                    self._update_server_stats(server_ip, server_port, False)
                    return None
                    
            except Exception as e:
                connect_time = (time.time() - start_time) * 1000
                self._update_server_stats(server_ip, server_port, False, connect_time)
                with self._lock:
                    self._stats["connection_errors"] += 1
                return None
        
        elif mode in (ConnectionMode.POOL, ConnectionMode.ADAPTIVE):
            # 连接池模式：优先复用现有连接
            conn = self._get_from_pool(server_ip, server_port)
            if conn:
                return conn
            
            # 创建新连接
            return self._create_connection(server_ip, server_port)
        
        else:
            return None
    
    def release_connection(self, conn: PyTdxConnection, close: bool = False):
        """
        释放连接
        
        Args:
            conn: 连接对象
            close: 是否关闭连接（True则关闭并从池中移除）
        """
        if not conn:
            return
        
        key = f"{conn.server_ip}:{conn.server_port}"
        
        with self._lock:
            if close or conn.mode == "short":
                # 关闭连接并从池中移除
                if key in self._pool:
                    try:
                        conn.api.disconnect()
                    except:
                        pass
                    del self._pool[key]
                    self._stats["active_connections"] -= 1
            else:
                # 只是放回池中，更新使用时间
                conn.last_used = time.time()
    
    def cleanup(self, max_idle_seconds: int = 300):
        """清理空闲连接"""
        with self._lock:
            current_time = time.time()
            to_remove = []
            
            for key, conn in self._pool.items():
                idle_time = current_time - conn.last_used
                if idle_time > max_idle_seconds:
                    to_remove.append((key, conn))
            
            for key, conn in to_remove:
                try:
                    conn.api.disconnect()
                except:
                    pass
                del self._pool[key]
                self._stats["active_connections"] -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats["pool_size"] = len(self._pool)
            stats["server_count"] = len(self._server_list)
            stats["mode"] = self.mode.value
            
            # 服务器状态
            server_stats = []
            for server in self._server_list[:5]:  # 只显示前5个
                server_stats.append({
                    "ip": server.ip,
                    "port": server.port,
                    "success_rate": f"{server.success_rate:.1%}",
                    "avg_response_ms": f"{server.avg_response_time:.1f}",
                    "score": f"{server.score:.3f}"
                })
            stats["top_servers"] = server_stats
            
            return stats


# 全局连接池实例（单例模式）
_global_pool: Optional[ConnectionPool] = None

def get_global_pool() -> ConnectionPool:
    """获取全局连接池实例"""
    global _global_pool
    if _global_pool is None:
        _global_pool = ConnectionPool(mode=ConnectionMode.ADAPTIVE)
    return _global_pool


def get_connection(server_ip: Optional[str] = None, server_port: Optional[int] = None,
                  mode: Optional[ConnectionMode] = None) -> Optional[PyTdxConnection]:
    """
    快速获取连接（使用全局连接池）
    
    Args:
        server_ip: 服务器IP，None则自动选择
        server_port: 服务器端口，None则自动选择
        mode: 连接模式，None则使用默认
        
    Returns:
        连接对象或None
    """
    pool = get_global_pool()
    
    preferred_server = None
    if server_ip and server_port:
        preferred_server = (server_ip, server_port)
    
    return pool.get_connection(preferred_server, mode)


def release_connection(conn: PyTdxConnection, close: bool = False):
    """快速释放连接"""
    if conn:
        pool = get_global_pool()
        pool.release_connection(conn, close)


def cleanup_connections():
    """清理空闲连接"""
    pool = get_global_pool()
    pool.cleanup()


def get_connection_stats() -> Dict[str, Any]:
    """获取连接统计信息"""
    pool = get_global_pool()
    return pool.get_stats()


# 测试函数
if __name__ == "__main__":
    # 测试连接
    print("测试pytdx连接管理...")
    
    if not PYTDX_AVAILABLE:
        print("错误: pytdx库未安装")
        exit(1)
    
    # 获取连接
    conn = get_connection()
    if conn:
        print(f"连接成功: {conn.server_ip}:{conn.server_port}")
        
        # 测试简单查询
        try:
            data = conn.api.get_security_quotes([(0, '000001')])
            if data:
                print(f"查询成功: 获取到{len(data)}条数据")
            else:
                print("查询失败: 无数据返回")
        except Exception as e:
            print(f"查询异常: {e}")
        
        # 释放连接
        release_connection(conn, close=True)
        
        # 显示统计
        stats = get_connection_stats()
        print(f"\n连接统计:")
        for key, value in stats.items():
            if key != "top_servers":
                print(f"  {key}: {value}")
        
        if "top_servers" in stats:
            print(f"\n最佳服务器:")
            for server in stats["top_servers"]:
                print(f"  {server['ip']}:{server['port']} - "
                      f"成功率{server['success_rate']}, "
                      f"响应{server['avg_response_ms']}ms, "
                      f"评分{server['score']}")
    else:
        print("连接失败")