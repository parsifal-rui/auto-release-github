# Self-hosted Runner 配置指南

因为 GitLab 在内网，GitHub Actions 的公共 Runner 无法访问，需要在内网机器上配置 Self-hosted Runner。

---

## 📋 前提条件

- ✅ 一台可以访问内网 GitLab 的机器（Linux/Windows/macOS）
- ✅ 这台机器能访问外网（至少能访问 github.com、chat.d.run）
- ✅ 有 sudo/管理员权限（用于安装 Runner）
- ✅ 建议：机器能长期运行（或至少在需要时开机）

---

## 🚀 配置步骤

### 步骤 1：在 GitHub 获取 Runner 注册信息

1. 进入你的 GitHub 仓库：`https://github.com/你的用户名/auto-release-github`
2. `Settings` → `Actions` → `Runners`
3. 点击 `New self-hosted runner` 绿色按钮
4. 选择你的机器类型（Linux/Windows/macOS）
5. **不要关闭这个页面**，后面会用到上面的命令和 token

---

### 步骤 2：在内网机器上安装 Runner（Linux 示例）

#### 如果是 Linux/WSL：

```bash
# 1. 创建工作目录
mkdir -p ~/actions-runner
cd ~/actions-runner

# 2. 下载 Runner（从 GitHub 页面复制最新版本的命令）
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# 3. 解压
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# 4. 注册 Runner（从 GitHub 页面复制配置命令，包含你的 token）
./config.sh --url https://github.com/你的用户名/auto-release-github --token YOUR_TOKEN

# 按提示输入：
# - Runner name: 随便写，如 "internal-runner"
# - Labels: 留空或写 "self-hosted,linux"
# - Work folder: 直接回车（默认 _work）

# 5. 启动 Runner
./run.sh
```

#### 如果是 Windows：

```powershell
# 1. 创建工作目录
mkdir C:\actions-runner
cd C:\actions-runner

# 2. 下载 Runner（从 GitHub 页面复制命令）
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip -OutFile actions-runner-win-x64-2.311.0.zip

# 3. 解压
Expand-Archive -Path .\actions-runner-win-x64-2.311.0.zip -DestinationPath .

# 4. 注册 Runner
.\config.cmd --url https://github.com/你的用户名/auto-release-github --token YOUR_TOKEN

# 5. 启动 Runner
.\run.cmd
```

---

### 步骤 3：验证 Runner 状态

注册成功后，在 GitHub 页面：
- `Settings` → `Actions` → `Runners`
- 应该看到你的 Runner，状态显示为 **Idle**（绿色圆点）

---

### 步骤 4：修改 Workflow 使用 Self-hosted Runner

在 `.github/workflows/sync-release-notes.yml` 中：

找到：
```yaml
jobs:
  sync:
    runs-on: ubuntu-latest
```

改成：
```yaml
jobs:
  sync:
    runs-on: self-hosted
```

提交并推送：
```bash
git add .github/workflows/sync-release-notes.yml
git commit -m "ci: use self-hosted runner"
git push
```

---

### 步骤 5：测试运行

1. 进入 `Actions` 页面
2. 手动触发 workflow
3. 这次应该会在你的内网机器上执行
4. 可以在内网机器的终端看到实时输出

---

## 🔄 让 Runner 持续运行

### Linux/WSL（推荐用 systemd）

```bash
# 1. 安装为服务
cd ~/actions-runner
sudo ./svc.sh install

# 2. 启动服务
sudo ./svc.sh start

# 3. 查看状态
sudo ./svc.sh status

# 4. 停止服务（需要时）
sudo ./svc.sh stop
```

### Windows（安装为服务）

```powershell
# 以管理员身份运行 PowerShell
cd C:\actions-runner

# 安装服务
.\svc.cmd install

# 启动服务
.\svc.cmd start

# 查看状态
.\svc.cmd status
```

---

## ✅ 验证成功的标志

- [ ] GitHub 页面显示 Runner 状态为 Idle（绿色）
- [ ] 手动触发 workflow 能成功运行
- [ ] 日志显示在你的 Runner 上执行
- [ ] 能成功连接内网 GitLab
- [ ] 能成功推送到 GitHub

---

## 🐛 常见问题

### 1. Runner 注册后立刻离线

**检查**：
- 是否关闭了运行 `./run.sh` 的终端
- 建议安装为服务（systemd/Windows Service）

### 2. Workflow 还是用公共 Runner

**检查**：
- workflow 文件是否改成 `runs-on: self-hosted`
- 是否提交并推送了修改

### 3. Runner 能访问 GitLab 但不能访问外网

**检查**：
- 机器的网络配置
- 代理设置（如果公司有代理）
- 防火墙规则

---

## 📝 配置总结

**测试环境**：
```yaml
TARGET_REPO: "parsifal-rui/test-docs"
TARGET_FILE_PATH: "release-notes.md"
```

**正式环境**（切换时修改 workflow）：
```yaml
TARGET_REPO: "DaoCloud/DaoCloud-docs"
TARGET_FILE_PATH: "docs/zh/docs/ghippo/intro/release-notes.md"
```

---

完成后，你的架构就是：

```
内网机器（Self-hosted Runner）
    ↓ 能访问内网 GitLab
    ↓ 执行 GitHub Actions
    ↓ 调用外网 DeepSeek
    ↓ 推送到外网 GitHub
```

这样就解决了内网访问的问题！
