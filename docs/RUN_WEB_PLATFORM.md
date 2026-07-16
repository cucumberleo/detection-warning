# 运行重构后的 Web 平台

## 后端

在项目根目录执行：

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.application:app --host 127.0.0.1 --port 8000
```

接口文档位于 `http://127.0.0.1:8000/docs`。除健康检查和演示登录外，接口要求前端登录后得到的 `Bearer demo-user` 或 `Bearer demo-admin`；权限由服务端令牌推导，不读取客户端角色参数。

## 前端

新开一个终端：

```powershell
cd web
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。Vite 会把 `/api` 代理到 FastAPI。前端支持 Node.js 18 及以上版本，不要求安装 pnpm。

## 验证

```powershell
python -m pytest backend/tests -q
cd web
npm run typecheck
npm test
npm run build
```
