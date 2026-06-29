# digital-workforce — 指挥手册

> 本文件是 **数字员工平台** 仓库 AI 协作的权威来源。执行 Tactile 对接、派活、部署相关任务前请先阅读本文。

## 项目定位

招募数字员工 → 绑定 Twitter Cookie → 批量派活。执行层对接 **CloudAgentLab Gateway（Tactile）**。

- 站点（生产）：http://43.98.185.179/
- 仓库：https://github.com/SpreadXAI/digital-workforce
- 云端验收账号：见 [`Cloud.md`](./Cloud.md)

## Tactile 对接（测试环境）

### 连接信息

| 项 | 值 |
|----|-----|
| **REST Base URL** | `https://test.foxrouter.com/api` |
| **WebSocket Base URL** | `wss://test.foxrouter.com/ws/agent/{session_id}?access_token=...` |
| **API Key** | `tkt_ofcI3pjjFnqH3E8mkGxDfxr-g6RwuWtK` |
| **认证头** | `X-API-Key: <key>`（与 `Authorization: Bearer <JWT>` 二选一，**API Key 优先**） |
| **固定 Agent ID** | 环境变量 `TACTILE_AGENT_ID`（写死，不按员工动态创建） |
| **工作空间** | 环境变量 `TACTILE_WORKSPACE_ID` |

> **安全**：API Key 仅用于开发与测试环境配置；生产部署通过 `backend/.env` 或 ECS 环境变量注入，禁止写入公开日志或提交到其他仓库。

### 环境变量

```bash
TACTILE_API_BASE=https://test.foxrouter.com/api
TACTILE_API_KEY=tkt_ofcI3pjjFnqH3E8mkGxDfxr-g6RwuWtK
TACTILE_WORKSPACE_ID=<workspace_id>
TACTILE_AGENT_ID=<固定 agent_id>
```

生产环境（新加坡 ECS）当前仍指向 `https://foxrouter.com/api`，`TACTILE_AGENT_ID=5`，`TACTILE_WORKSPACE_ID=6`；迁移到 test 环境时改上述变量即可。

### 任务映射（核心契约）

**本平台每条派活任务 ↔ Tactile 一条 Work Item（任务）**

| digital-workforce | Tactile Gateway |
|-------------------|-----------------|
| `work_tasks` 表一行 | `POST /api/work` 创建的任务 |
| `work_tasks.id` | 本地主键 |
| `task_executions.tactile_work_id` | Tactile 返回的 `work.id` |
| `task_executions.tactile_session_id` | Tactile 返回的 `session_id`（WebSocket 对话用） |
| `digital_employees.tactile_last_work_id` | 该员工最近一次 Tactile 任务 ID |
| 派活指令 `instruction` | `POST /api/work` 的 `content` |

派活流程（目标）：

1. 使用 **固定 `TACTILE_AGENT_ID`** + **`TACTILE_WORKSPACE_ID`**
2. `POST /api/work` 创建任务，传入 `content`（员工指令）及运行时环境变量（`TWITTER_COOKIE`、`DW_EMPLOYEE_ID`、`TWITTER_HANDLE` 等）
3. 将返回的 `id`、`session_id` 写回 `task_executions` / `work_tasks` 状态
4. 需要流式对话时，连接 `wss://test.foxrouter.com/ws/agent/{session_id}?access_token=...`

> 当前代码 `backend/app/tactile/` 仍使用旧版 `/api/v1/*` 路径及部分「每员工一个 Agent」逻辑；后续迭代应切换到本文档的 Gateway API，并统一使用固定 Agent ID。

---

## CloudAgentLab Gateway API 参考

文档来源：CloudAgentLab Gateway 全量 REST / WebSocket 说明（测试环境 `test.foxrouter.com`）。

### 通用

- 所有 REST 路径前缀：`/api`
- 公开接口（无需登录）：`/api/health`、`/api/public/skills` 等标注「公开」的端点
- 登录用户接口：`Authorization: Bearer <JWT>` 或 `X-API-Key: <key>`

### 健康检查

| Method | Path | 权限 |
|--------|------|------|
| GET | `/api/health` | 公开 |

### 认证

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户 |
| PATCH | `/api/auth/me` | 更新昵称 |
| POST | `/api/auth/avatar` | 上传头像 |
| DELETE | `/api/auth/avatar` | 删除头像 |

### 工作空间

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/workspace` | 创建工作空间（`workspace_scope`: 1=个人, 2=团队） |
| GET | `/api/workspace` | 列出可访问空间 |
| GET | `/api/workspace/{workspace_id}` | 空间详情 |
| PUT | `/api/workspace/{workspace_id}` | 更新空间 |
| DELETE | `/api/workspace/{workspace_id}` | 删除空间 |
| GET | `/api/workspace/{workspace_id}/repos` | 绑定仓库列表 |
| PUT | `/api/workspace/{workspace_id}/repos` | 替换仓库绑定 |
| GET | `/api/workspace/{workspace_id}/members` | 成员列表 |
| POST | `/api/workspace/{workspace_id}/members` | 邀请成员 |
| DELETE | `/api/workspace/{workspace_id}/members/{user_id}` | 移除成员 |

### Agent

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/agent` | 创建 Agent（`runtime_type`: sandbox \| ecs \| ecs-ubuntu \| ecs-windows） |
| POST | `/api/agent/ensure-default` | 确保默认 Coder Agent（`?workspace_id=`） |
| GET | `/api/agent` | 列出空间下 Agent（`?workspace_id=`） |
| GET | `/api/agent/{agent_id}` | Agent 详情 |
| PUT | `/api/agent/{agent_id}` | 更新 Agent |
| DELETE | `/api/agent/{agent_id}` | 删除 Agent |
| GET | `/api/agent/{agent_id}/bindings` | Skills / MCP / Hooks 绑定 |
| PUT | `/api/agent/{agent_id}/bindings` | 更新绑定 |
| GET | `/api/agent/{agent_id}/env-vars` | 环境变量 |
| PUT | `/api/agent/{agent_id}/env-vars` | 更新环境变量 |

### 任务（Work Item）— **派活核心**

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/work` | **创建任务**（返回 `id`, `session_id`, `status` 等） |
| GET | `/api/work` | 列出空间任务（`?workspace_id=`） |
| GET | `/api/work/{work_id}` | 任务详情 |
| PUT | `/api/work/{work_id}` | 更新任务 |
| POST | `/api/work/{work_id}/rename` | 重命名 |
| POST | `/api/work/{work_id}/generate-title` | LLM 生成标题 |
| POST | `/api/work/{work_id}/phase` | 推进编码阶段 |
| GET | `/api/work/{work_id}/workspace/files` | 沙箱文件树 |
| GET | `/api/work/{work_id}/workspace/diff` | Git diff |
| POST | `/api/work/{work_id}/retry-sandbox` | 重试沙箱 |
| POST | `/api/work/{work_id}/destroy-sandbox` | 销毁沙箱 |
| POST | `/api/work/{work_id}/archive` | 归档 |

**创建任务 Request Body 示例：**

```json
{
  "workspace_id": 1,
  "agent_id": 2,
  "name": "修复登录 bug",
  "content": "请检查 auth 模块并修复...",
  "machine_type": "ubuntu",
  "repo_configs": "[{\"repo\":\"org/app\",\"sourceBranch\":\"main\"}]"
}
```

`machine_type`: `windows` | `ubuntu` | `sandbox`

### 对话

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/chat/{session_id}/send` | 发送消息 |
| GET | `/api/chat/{session_id}/history` | 聊天历史 |
| GET | `/api/chat/{session_id}/status` | 连接与处理状态 |
| POST | `/api/chat/{session_id}/cancel` | 取消生成 |

### WebSocket

| 协议 | Path | 说明 |
|------|------|------|
| WS | `/ws/agent/{session_id}` | 实时流式对话；query: `access_token=<JWT>&entry_index=0`；发送 `{"content":"..."}` 或 ping |

### 自动任务（Scheduled Tasks）

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/workspace/{workspace_id}/scheduled-tasks` | 创建（`trigger_type`: cron \| api） |
| GET | `/api/workspace/{workspace_id}/scheduled-tasks` | 列表 |
| GET | `.../queue-status` | 队列状态 |
| GET | `.../{task_id}` | 详情 |
| POST | `.../{task_id}/update` | 更新 |
| DELETE | `.../{task_id}` | 删除 |
| POST | `.../{task_id}/toggle` | 启用/禁用 |
| POST | `.../{task_id}/trigger` | 手动触发 → 返回 `work_item_id` |
| POST | `.../api-trigger` | 外部 API 触发（Bearer = 任务 `api_token`） |
| GET | `.../{task_id}/run-history` | 运行历史 |
| GET | `.../archived-runs` | 已归档运行 |
| POST | `.../runs/{work_item_id}/cancel` | 取消运行 |
| POST | `.../runs/{work_item_id}/archive` | 归档运行 |
| POST | `.../runs/{work_item_id}/label` | 重命名运行 |

### 技能广场

| Method | Path |
|--------|------|
| GET | `/api/skill-plaza/market` |
| GET | `/api/skill-plaza` |
| GET | `/api/skill-plaza/manage` |
| GET | `/api/skill-plaza/{skill_id}` |
| GET | `/api/skill-plaza/{skill_id}/download` |
| POST | `/api/skill-plaza/upload` |
| POST | `/api/skill-plaza/{skill_id}/versions` |
| GET | `/api/skill-plaza/{skill_id}/files/{file_path}` |
| POST | `/api/skill-plaza/{skill_id}/publish` |
| PATCH | `/api/skill-plaza/{skill_id}` |
| DELETE | `/api/skill-plaza/{skill_id}` |
| POST | `/api/skill-plaza/{skill_id}/install` |
| POST | `/api/skill-plaza/{skill_id}/rollback` |

### 公开技能（无需登录）

| Method | Path |
|--------|------|
| GET | `/api/public/skills` |
| GET | `/api/public/skills/{namespace}/{slug}` |
| GET | `/api/public/skills/{namespace}/{slug}/download` |
| GET | `/api/public/skills/{namespace}/{slug}/files/{file_path}` |
| GET | `/api/public/skills/{namespace}/{slug}/skill.md` |

### MCP / Hooks 广场

| 资源 | 市场列表 | 详情 | 创建 | 新版本 |
|------|----------|------|------|--------|
| MCP | `GET /api/mcp-plaza/market` | `GET /api/mcp-plaza/{mcp_id}` | `POST /api/mcp-plaza` | `POST .../versions` |
| Hooks | `GET /api/hooks-plaza/market` | `GET /api/hooks-plaza/{hooks_id}` | `POST /api/hooks-plaza` | `POST .../versions` |

### GitHub

| Method | Path |
|--------|------|
| GET | `/api/github/oauth/status` |
| GET | `/api/github/oauth/start` |
| GET | `/api/github/oauth/callback` |
| GET | `/api/github/connection` |
| DELETE | `/api/github/connection` |
| GET | `/api/github/repos` |

### 任务 Pin

| Method | Path |
|--------|------|
| GET | `/api/workspace/{workspace_id}/work-item-pins` |
| POST | `/api/workspace/{workspace_id}/work-item-pins/{work_item_id}/toggle` |

### 管理台（super_admin）

| Method | Path |
|--------|------|
| GET | `/api/admin/overview` |
| GET | `/api/admin/runtime-resources` |
| GET | `/api/admin/orphan-instances` |
| POST | `/api/admin/orphan-instances/terminate` |
| GET | `/api/admin/users` |
| GET | `/api/admin/workspaces` |
| GET | `/api/admin/system-skills` |
| GET | `/api/admin/system-agents` |
| GET | `/api/admin/workspace-approvals` |
| POST | `/api/admin/workspaces/{workspace_id}/approve` |
| POST | `/api/admin/workspaces/{workspace_id}/reject` |

---

## 本平台数据模型（摘要）

| 实体 | 说明 |
|------|------|
| `User` | 平台用户 |
| `Team` / `TeamMember` / `TeamInvitation` | 团队；每人有个人团队，可邀请成员 |
| `DigitalEmployee` | 数字员工；`team_id` 隔离；`tactile_agent_id` 预留 |
| `WorkTask` | 派活任务（对应 Tactile Work Item） |
| `TaskExecution` | 执行日志；含 `tactile_work_id`、`tactile_session_id` |

## 目录约定

```text
digital-workforce/
├── CLAUDE.md          # 本文件
├── Cloud.md           # 云端测试账号与部署
├── backend/app/tactile/   # Tactile 客户端与派活
├── frontend/          # Vue 3 管理台
└── scripts/deploy-singapore.py
```

## Git 规范

- 默认分支：`main`
- 提交信息：英文 Conventional Commits（`feat:` / `fix:` / `docs:`）

---

*最后更新：记录 Tactile Gateway 测试环境 API、固定 Agent ID 策略、WorkTask ↔ Work Item 映射。*
