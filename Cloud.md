# Cloud.md — 数字员工平台 云端测试账号

> 供 Cloud Agent、手工验收使用。替代原 Spider雷达 站点。

## 环境

| 项 | 值 |
|----|-----|
| **站点** | http://43.98.185.179/ |
| **API** | http://43.98.185.179/api/ |
| **区域** | 新加坡 `ap-southeast-1` |
| **ECS** | `i-t4n571mpi11mkib9ubxj`（2 核 4G） |
| **数据库** | 新加坡 RDS / schema `dw` |
| **仓库** | https://github.com/SpreadXAI/digital-workforce |

## 普通测试账号

| 项 | 值 |
|----|-----|
| **邮箱** | `qa@spreadx.ai` |
| **密码** | `Dw@Test2026` |

### API 登录

```bash
curl -s -X POST "http://43.98.185.179/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"qa@spreadx.ai","password":"Dw@Test2026"}'
```

## 管理员账号

| 项 | 值 |
|----|-----|
| **邮箱** | `admin@spreadx.ai` |
| **密码** | `Dw@Admin2026` |

## 部署

```bash
cd scripts
pip install -r requirements-deploy.txt
export ALIYUN_ACCESS_KEY_ID=...
export ALIYUN_ACCESS_KEY_SECRET=...
python deploy-singapore.py
```

## Cloud Agent Lab 对接（生产）

| 项 | 值 |
|----|-----|
| **API** | `https://foxrouter.com/api` |
| **控制台** | `https://foxrouter.com/workbench` |
| **Workspace ID** | `6` |
| **Agent ID** | `5`（全员共用，在 **管理台** `/admin` 配置） |
| **配置 API** | `GET/PUT /api/admin/tactile`（仅 admin） |

测试环境见仓库 `CLAUDE.md`（`test.foxrouter.com`）。

## 用户流程

1. 登录 → **招募中心** 创建员工
2. **培训中心** 配置人设、凭证、Skill，试跑
3. 员工详情 → **确认上岗**（provision Agent）
4. **任务中心** 向在岗员工派发任务

## 已废弃

原 Spider雷达（账号市场 / 购号）已下线，由本站点替代。
