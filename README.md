# Gas Sense Web Platform

面向光伏自供电气体传感器的现代 Web 监测平台。当前版本把原 Flutter/Flask 原型中的核心闭环迁移为 FastAPI + SQLite + Vue 3 + TypeScript，并保留旧 demo 作为迁移对照。

## 已实现

- 普通用户与管理员双工作台；
- 设备选择、可复现模拟检测和响应曲线；
- SQLite 检测历史、趋势摘要与 CSV 导出；
- 后端统一阈值判定、预警创建和人工确认；
- 管理员设备、用户授权与阈值配置；
- 角色可见范围、输入校验、错误/空/加载状态；
- 响应式桌面侧栏与移动端底部导航；
- 基于当前可见数据的受控助手回答。

## 快速启动

后端：

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.application:app --host 127.0.0.1 --port 8000
```

前端（另开终端）：

```powershell
cd web
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`，接口文档位于 `http://127.0.0.1:8000/docs`。前端兼容 Node.js 18+，不需要全局安装 pnpm。

## 验证

```powershell
python -m pytest backend/tests -q
cd web
npm run typecheck
npm run build
```

## 目录

- `backend/app/`：FastAPI HTTP adapter、平台模块和 SQLite adapter；
- `backend/tests/`：公共 HTTP interface 行为测试；
- `web/`：Vue 3 + TypeScript 前端；
- `contracts/`：检测结果契约；
- `docs/REFACTOR_ASSESSMENT.md`：功能、布局、优先级与架构评估；
- `frontend/`、`backend/server.py`：原始单文件 demo，仅作为迁移对照。

当前曲线与浓度为演示数据，不代表真实安全检测结论。真实信号算法应作为 adapter 接入并继续满足 `contracts/detection-result.v1.json`。
