# Digital Workforce — 数字员工平台

> **产品定位**：招募 → 培训 → 上岗 → 执行任务。数字员工是任务的执行载体（执行器），执行层对接 [Tactile](https://foxrouter.com)。

## 与旧 Spider雷达 的关系

本目录为 **全新 greenfield 实现**，替代原「账号市场 / 购号养号」形态。以下概念已废弃：

- 账号市场、购号、tier 定价
- 「我的账号」与市场双轨
- spider-radar 业务 UI

以下能力 **内化** 到数字员工模型：

- 每员工一个 Tactile Agent
- Skill 绑定在员工上
- `dispatch_env_json` 注入凭证
- 试跑 / 任务派发

产品设计详见 [`docs/digital-employee-platform.md`](../docs/digital-employee-platform.md)。

## 目录结构

```text
digital-workforce/
├── backend/          # FastAPI + SQLAlchemy
│   └── app/
│       ├── routers/  # 招募、培训、上岗、任务 API
│       └── tactile/  # Tactile 执行适配层
└── frontend/         # Vue 3 + Vite
```

## 快速启动（本地）

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 开发可用 SQLite（无需 Postgres）：
echo 'SQLITE_PATH=./digital_workforce.db' >> .env
uvicorn app.main:app --reload --port 8000
```

默认账号（见 `.env.example`）：

| 角色 | 邮箱 | 密码 |
|------|------|------|
| Admin | admin@spreadx.ai | Dw@Admin2026 |
| QA | qa@spreadx.ai | Dw@Test2026 |

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 ，API 经 Vite 代理到 `:8000`。

## Tactile 配置

在 `backend/.env` 中设置：

```env
TACTILE_API_BASE=https://foxrouter.com/api
TACTILE_API_KEY=<your-key>
TACTILE_WORKSPACE_ID=6
TACTILE_AGENT_ID=5
```

- **招募/培训**：可不配置 Tactile（档案与 Skill 绑定仅存平台）
- **上岗 / 试跑 / 任务**：需要有效 API Key；上岗时 provision Agent，派发时注入 `dispatch_env_json`

## API 概览

| 路径 | 说明 |
|------|------|
| `POST /api/auth/login` | 登录 |
| `GET /api/dashboard/stats` | 总览统计 |
| `GET/POST /api/employees` | 员工名册 / 招募 |
| `PATCH /api/employees/{id}` | 培训配置 |
| `POST /api/employees/{id}/stage` | 阶段流转 |
| `POST /api/employees/{id}/trial-run` | 试跑 |
| `POST /api/tasks` | 派发任务（仅 active 员工） |
| `GET /api/skills/catalog` | Skill Plaza 代理 |

## 员工生命周期

```text
recruiting → training → ready → active ⇄ suspended
```

| 阶段 | 导航入口 |
|------|----------|
| 招募 | 招募中心 |
| 培训 | 培训中心 / 员工详情 |
| 上岗 | 员工详情 → 确认上岗 |
| 执行任务 | 任务中心 |

## 建议远程仓库

`SpreadXAI/digital-workforce` 或独立子代理 `zero-digital-workforce-agent`。
