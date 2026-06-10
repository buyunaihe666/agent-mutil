# M10 — 系统监控 (`monitor_service`)

> 模块职责：采集系统硬件资源和 Docker 容器的运行数据，通过 WebSocket 推送到前端。

---

## 子任务

### 1. 硬件资源采集

- [ ] 1.1 实现 `get_hardware_stats()` — 采集系统内存使用情况（通过 psutil）
- [ ] 1.2 实现 GPU 监控（预留）：通过 NVIDIA Container Toolkit / nvidia-smi 采集 GPU 显存 + 利用率 + 温度
- [ ] 1.3 无 GPU 环境优雅降级：GPU 字段返回 null / "不可用"
- [ ] 1.4 返回 HardwareStats 结构：memory_total, memory_used, memory_pct, gpu_memory_total, gpu_memory_used, gpu_utilization, gpu_temp

### 2. Docker 容器监控

- [ ] 2.1 实现 `get_container_stats()` — 通过 docker-py 采集运行中容器列表
- [ ] 2.2 采集每个容器的：名称、CPU 使用率、内存使用、网络 IO
- [ ] 2.3 区分沙箱临时容器和普通容器
- [ ] 2.4 异常容器检测：CPU/内存超阈值标记为警告

### 3. 定时采集与推送

- [ ] 3.1 启动后台定时采集任务（asyncio.create_task）：每 5 秒采集一次
- [ ] 3.2 采集结果通过 WebSocket Hub 推送到 `/ws/monitor`（`hardware_stats` 消息类型）
- [ ] 3.3 实现 `start_collection_loop()` / `stop_collection()` 控制采集启停

### 4. API 端点

- [ ] 4.1 `GET /api/monitor/hardware` — 获取当前硬件资源使用情况
- [ ] 4.2 `GET /api/monitor/containers` — 获取 Docker 容器状态
- [ ] 4.3 `GET /api/health` — 健康检查（DB连接 + Redis连接 + Docker daemon 可达性）

### 5. 测试

- [ ] 5.1 Mock psutil + docker-py，测试采集逻辑
- [ ] 5.2 测试 GPU 优雅降级逻辑
- [ ] 5.3 测试定时采集循环
