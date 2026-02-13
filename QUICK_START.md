# 🚀 快速开始（解决内网访问问题）

## 核心问题

GitHub Actions 公共 Runner 在公网，无法访问内网 GitLab。

**解决方案**：使用 Self-hosted Runner（在内网机器上运行）

---

## ✅ 完整配置流程（30 分钟）

### 1️⃣ 配置 GitHub Secrets（2 分钟）

访问：`https://github.com/parsifal-rui/auto-release-github/settings/secrets/actions`

添加 3 个 Secrets：
- `GITLAB_TOKEN`：`7rPWYaQBQ2hqwickYyYS`
- `DRUN_API_KEY`：（从 `auto-release-note/apiKey.txt` 复制）
- `GH_PAT`：（从 `auto-release-note/github_token.txt` 复制）

---

### 2️⃣ 推送代码到 GitHub（2 分钟）

```bash
cd D:\桌面\codes\2026winter\DaoCloud\auto-release-github

git add .
git commit -m "feat: complete setup with self-hosted runner support"
git push origin main
```

---

### 3️⃣ 在内网机器上配置 Self-hosted Runner（10 分钟）

#### A. 获取注册信息

1. 访问：`https://github.com/parsifal-rui/auto-release-github/settings/actions/runners`
2. 点击 `New self-hosted runner`
3. 选择机器类型（Linux 或 Windows）
4. **记下页面上的命令和 token**

#### B. 在内网机器执行（以 Linux 为例）

```bash
# 1. 创建目录
mkdir ~/actions-runner && cd ~/actions-runner

# 2. 下载（复制 GitHub 页面的命令）
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# 3. 解压
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# 4. 配置（复制 GitHub 页面的命令，包含 token）
./config.sh --url https://github.com/parsifal-rui/auto-release-github --token YOUR_TOKEN

# 5. 测试运行（先不安装服务，确认能跑）
./run.sh
```

#### C. 验证 Runner 状态

- 在 GitHub 页面应该看到 Runner 显示为 **Idle**（绿色圆点）
- 终端显示 "Listening for Jobs"

---

### 4️⃣ 测试手动触发（5 分钟）

1. 访问：`https://github.com/parsifal-rui/auto-release-github/actions`
2. 选择 `Sync Release Notes from GitLab`
3. 点击 `Run workflow`
4. 参数：
   - `tag`：留空
   - `create_pr`：`true`
5. 点击 `Run workflow`

---

### 5️⃣ 查看结果（2 分钟）

- [ ] Actions 显示绿色 ✓
- [ ] 内网机器终端显示执行日志
- [ ] 访问 `https://github.com/parsifal-rui/test-docs/pulls`
- [ ] 看到自动创建的 PR

---

## 📋 文件路径配置

已配置好，无需手动修改代码：

**当前配置**（在 workflow 中）：
```yaml
TARGET_REPO: "parsifal-rui/test-docs"
TARGET_FILE_PATH: "release-notes.md"
```

**切换到正式环境时**，只需修改 workflow：
```yaml
TARGET_REPO: "DaoCloud/DaoCloud-docs"
TARGET_FILE_PATH: "docs/zh/docs/ghippo/intro/release-notes.md"
```

---

## 🎯 测试成功的标志

- ✅ Self-hosted Runner 显示 Idle（绿色）
- ✅ Workflow 成功执行（绿色 ✓）
- ✅ 能访问内网 GitLab（没有 timeout 错误）
- ✅ 能调用 DeepSeek API
- ✅ 能推送到 GitHub test-docs
- ✅ test-docs 仓库有新的 PR

---

## ⚠️ 重要提醒

1. **Runner 机器要一直开着**（或至少在需要时开机）
2. **建议安装为系统服务**（systemd/Windows Service），这样重启后自动运行
3. **测试成功后再切换到正式环境**

---

**按顺序完成以上 5 步，就能完整跑通整个流程！** 🎉

有问题随时问。
