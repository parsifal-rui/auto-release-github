# Auto Release Notes Sync

自动从 GitLab 获取 release notes，经 DeepSeek 处理后，推送到 GitHub 文档仓库。

## 架构概述

```
GitLab (ndx/ghippo)
    ↓ 读取 release notes
GitHub Actions (本仓库)
    ↓ DeepSeek 处理
GitHub (DaoCloud/DaoCloud-docs)
    ↓ 创建 PR 或直接推送
```

---

## 📋 前置准备

### 1. 准备 Token

#### GitLab Personal Access Token
1. 登录内网 GitLab：https://gitlab.daocloud.cn
2. 右上角头像 → `Preferences` → `Access Tokens`
3. 创建 token，勾选权限：`api`, `read_api`, `read_repository`
4. **复制并保存 token**

#### d.run API Key
1. 登录 d.run 控制台
2. 创建 API Key
3. **复制并保存 key**

#### GitHub Personal Access Token
1. 登录 GitHub → 右上角头像 → `Settings`
2. 左侧 `Developer settings` → `Personal access tokens` → `Tokens (classic)`
3. `Generate new token (classic)`
4. 勾选权限：`repo`（完整仓库权限）
5. **复制并保存 token**

---

## 🚀 配置步骤

### 步骤 1：初始化仓库

在本地克隆并初始化：

```bash
# 如果还没克隆
git clone https://github.com/你的用户名/auto-release-github.git
cd auto-release-github

# 初始化结构（如果目录不存在）
mkdir -p .github/workflows scripts

# 复制文件（如果本地有）
cp -r 本地路径/auto-release-github/.github ./
cp -r 本地路径/auto-release-github/scripts ./
cp 本地路径/auto-release-github/README.md ./

# 提交到仓库
git add .
git commit -m "feat: initial setup for auto release notes sync"
git push origin main
```

### 步骤 2：配置 GitHub Secrets

在你的 GitHub 仓库（`auto-release-github`）：

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`，添加以下 Secrets：

| Name | Value | 说明 |
|------|-------|------|
| `GITLAB_TOKEN` | `你的 GitLab token` | 用于读取 GitLab release notes |
| `DRUN_API_KEY` | `你的 d.run API key` | 用于调用 DeepSeek |
| `GH_PAT` | `你的 GitHub token` | 用于推送到目标仓库 |

**注意**：
- Secret 名称必须完全一致（区分大小写）
- 添加后无法查看，只能重新生成

### 步骤 3：初始化测试仓库

创建测试用的文档仓库（用于验证）：

```bash
# 在 GitHub 上创建新仓库：test-doc
# 然后在本地初始化

cd 你的工作目录
mkdir test-doc
cd test-doc

# 创建测试文件
mkdir -p docs/zh/docs/ghippo/intro
cat > docs/zh/docs/ghippo/intro/release-notes.md << 'EOF'
# 全局管理 Release Notes

本页列出全局管理各版本的 Release Notes，便于您了解各版本的演进路径和特性变化。

EOF

# 初始化 git 并推送
git init
git add .
git commit -m "init: test doc repo"
git branch -M main
git remote add origin https://github.com/你的用户名/test-doc.git
git push -u origin main
```

---

## 🧪 测试流程

### 测试 1：先推送到自己的测试仓库

#### 1. 修改目标仓库

在 `update_release_notes.py` 中修改（第 270 行左右）：

```python
target_github_repo = os.environ.get("TARGET_REPO", "你的用户名/test-doc")
```

或者在 workflow 里添加环境变量：

```yaml
env:
  TARGET_REPO: "你的用户名/test-doc"
```

#### 2. 手动触发测试

1. 进入 GitHub 仓库 → `Actions` 标签
2. 左侧选择 `Sync Release Notes from GitLab`
3. 点击右侧 `Run workflow` 下拉按钮
4. 填写参数：
   - `tag`：留空（使用最新版本）或填 `v0.44.0`
   - `create_pr`：填 `true`（创建 PR，而不是直接推送）
5. 点击 `Run workflow`

#### 3. 查看执行结果

1. 等待几分钟，workflow 会显示运行状态
2. 点击运行记录，查看详细日志
3. 检查是否有错误（红色 ✗）或成功（绿色 ✓）

#### 4. 验证结果

- 如果选择了 `create_pr: true`：
  - 去你的 `test-doc` 仓库查看 Pull Requests
  - 应该有一个自动创建的 PR
  - 查看 PR 内容，确认 release notes 已正确插入

- 如果选择了 `create_pr: false`：
  - 直接查看 `test-doc` 仓库的 `docs/zh/docs/ghippo/intro/release-notes.md`
  - 确认新内容已插入到文件开头

---

### 测试 2：定时任务测试

#### 查看定时配置

在 `.github/workflows/sync-release-notes.yml` 中：

```yaml
schedule:
  - cron: '0 16 * * *'  # UTC 16:00 = 北京时间 00:00（凌晨12点）
```

**注意**：
- GitHub Actions 使用 UTC 时间
- 北京时间 = UTC + 8
- 所以凌晨 12:00 对应 UTC 16:00

#### 启用定时任务

1. 确认测试 1 成功后
2. 定时任务会自动每天执行
3. 可以在 Actions 页面查看历史记录

---

## 🔄 切换到正式仓库

测试成功后，切换到正式仓库：

### 方法 1：修改代码（推荐）

在 `scripts/update_release_notes.py` 中修改：

```python
target_github_repo = os.environ.get("TARGET_REPO", "DaoCloud/DaoCloud-docs")
```

提交并推送。

### 方法 2：使用环境变量

在 `.github/workflows/sync-release-notes.yml` 中添加：

```yaml
env:
  TARGET_REPO: "DaoCloud/DaoCloud-docs"
```

---

## 📝 手动触发参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `tag` | 指定要同步的 GitLab tag<br>留空则使用最新正式版本 | `v0.44.0` 或留空 |
| `create_pr` | 是否创建 PR<br>`true`: 创建 PR（推荐）<br>`false`: 直接推送到 main | `true` 或 `false` |

---

## 🐛 常见问题

### 1. Workflow 不触发

**检查**：
- Secrets 是否配置正确（名称区分大小写）
- Workflow 文件是否在 `main` 分支
- 手动触发是否有错误提示

### 2. GitLab 连接失败

**检查**：
- `GITLAB_TOKEN` 是否有效
- 是否有网络问题（Actions 能否访问内网 GitLab）
- Token 权限是否包含 `api`, `read_repository`

### 3. DeepSeek 调用失败

**检查**：
- `DRUN_API_KEY` 是否有效
- API quota 是否充足
- 网络是否能访问 `https://chat.d.run`

### 4. GitHub 推送失败

**检查**：
- `GH_PAT` 是否有效
- Token 是否有目标仓库的 `repo` 权限
- 目标仓库路径是否正确

### 5. 没有检测到文件变更

**原因**：
- 该版本的 release notes 可能已经存在
- 或者处理后的内容与现有内容完全相同

**解决**：
- 正常现象，不影响功能
- 可以手动指定不同的 tag 测试

---

## 📂 文件结构

```
auto-release-github/
├── .github/
│   └── workflows/
│       └── sync-release-notes.yml    # GitHub Actions 配置
├── scripts/
│   ├── gitlab_client.py              # GitLab API 客户端
│   ├── update_release_notes.py       # 主脚本
│   └── requirements.txt              # Python 依赖
├── README.md                          # 本文件
└── sync_result.log                    # 运行日志（Actions 生成）
```

---

## 🔐 安全说明

- 所有敏感信息（Token、API Key）存储在 GitHub Secrets
- 不会出现在代码、日志中
- Secrets 只在 Actions 运行时作为环境变量传递

---

## 📞 支持

如有问题，请：
1. 查看 Actions 运行日志
2. 检查 Secrets 配置
3. 联系维护者
