# Gas Monitor Web Demo

用户端 + 管理员端的气体传感器平台协作基座。当前版本使用内存中的演示数据，目的是固定页面、接口和协作边界；不要将其作为生产系统。

## 启动

```powershell
cd gas-monitor-web-demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\server.py
```

浏览器访问 `http://127.0.0.1:8000`。

## 演示范围

- 普通用户：个性化推荐、模拟检测、历史记录、预警确认、AI 助手；
- 管理员：全局仪表盘、用户、设备、预警阈值与全局检测记录；
- 后端：稳定的 Demo API，后续替换内存数据为数据库与真实模型。

详细分工、分支与 PR 规则见 [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md)。
