# 快速配置清单 ✅

按顺序完成以下步骤：

## 📦 第 1 步：准备 Token（5 分钟）

- [ ] GitLab Token
  - 访问：https://gitlab.daocloud.cn/-/profile/personal_access_tokens
  - 权限：`api`, `read_api`, `read_repository`
  - 复制 token：`_____________________`

- [ ] d.run API Key
  - 访问：d.run 控制台
  - 创建 API Key
  - 复制 key：`_____________________`

- [ ] GitHub Token
  - 访问：https://github.com/settings/tokens
  - 权限：`repo`
  - 复制 token：`_____________________`

---

## 🚀 第 2 步：初始化 GitHub 仓库（3 分钟）

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/auto-release-github.git
cd auto-release-github

# 2. 确认文件结构
ls -la
# 应该看到：.github/, scripts/, README.md

# 3. 推送到 GitHub（如果还没推）
git add .
git commit -m "feat: initial setup"
git push origin main
```

---

## 🔐 第 3 步：配置 Secrets（2 分钟）

访问：https://github.com/你的用户名/auto-release-github/settings/secrets/actions

添加 3 个 Secrets：

- [ ] `GITLAB_TOKEN` = `你的 GitLab token`
- [ ] `DRUN_API_KEY` = `你的 d.run key`
- [ ] `GH_PAT` = `你的 GitHub token`

---

## 🧪 第 4 步：创建测试仓库（2 分钟）

```bash
# 1. 在 GitHub 网页上创建新仓库：test-doc

# 2. 在本地初始化
mkdir test-doc
cd test-doc
mkdir -p docs/zh/docs/ghippo/intro

# 3. 创建测试文件
cat > docs/zh/docs/ghippo/intro/release-notes.md << 'EOF'
# 全局管理 Release Notes

本页列出全局管理各版本的 Release Notes。

EOF

# 4. 推送到 GitHub
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/你的用户名/test-doc.git
git push -u origin main
```

---

## ⚙️ 第 5 步：配置 Self-hosted Runner（10 分钟）⭐

**重要**：因为内网 GitLab 无法从公网访问，必须配置 Self-hosted Runner。

详细步骤请查看：[RUNNER_SETUP.md](./RUNNER_SETUP.md)

**快速步骤**：
1. 在 GitHub 仓库 `Settings` → `Actions` → `Runners` → `New self-hosted runner`
2. 按页面提示，在内网机器上下载并注册 Runner
3. 启动 Runner（或安装为服务）
4. 在 workflow 中改成 `runs-on: self-hosted`

验证：
- [ ] GitHub 页面显示 Runner 为 Idle（绿色）
- [ ] Runner 终端显示 "Listening for Jobs"

---

## 🎯 第 6 步：手动触发测试（2 分钟）

1. 访问：https://github.com/你的用户名/auto-release-github/actions
2. 左侧选择：`Sync Release Notes from GitLab`
3. 点击：`Run workflow` ▼
4. 参数设置：
   - `tag`: 留空
   - `create_pr`: `true`
5. 点击：绿色的 `Run workflow` 按钮
6. 等待 1-2 分钟

---

## ✅ 第 7 步：验证结果（1 分钟）

- [ ] Actions 显示绿色 ✓
- [ ] 查看运行日志，确认没有错误
- [ ] 访问：https://github.com/你的用户名/test-doc/pulls
- [ ] 应该有一个新的 PR
- [ ] 查看 PR 内容，确认 release notes 已插入

---

## 🔄 第 8 步：切换到正式仓库（可选）

测试成功后，改回正式仓库：

在 `scripts/update_release_notes.py` 中改回：
```python
target_github_repo = os.environ.get("TARGET_REPO", "DaoCloud/DaoCloud-docs")
```

提交并推送：
```bash
git add scripts/update_release_notes.py
git commit -m "config: switch to production repo"
git push
```

---

## 📅 定时任务说明

配置完成后，每天北京时间凌晨 12:00 会自动执行。

查看定时执行记录：
https://github.com/你的用户名/auto-release-github/actions

---

## ⚠️ 检查清单

如果测试失败，按顺序检查：

1. [ ] Secrets 名称是否完全正确（区分大小写）
2. [ ] Token 是否有效（未过期）
3. [ ] Token 权限是否足够
4. [ ] 目标仓库路径是否正确
5. [ ] 目标仓库文件路径是否存在
6. [ ] 查看 Actions 日志中的具体错误

---

**全部完成！** 🎉

如有问题，查看 [README.md](./README.md) 中的"常见问题"部分。
