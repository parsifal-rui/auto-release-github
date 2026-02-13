#!/usr/bin/env python3
"""
主脚本：从 GitLab 获取 release notes → DeepSeek 处理 → 推送到 GitHub
"""
import os
import sys
import re
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# 导入 GitLab 客户端
from gitlab_client import GitLabReleaseClient
import openai
import requests


def log(message):
    """打印日志"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    # 同时写入日志文件
    with open("sync_result.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def process_with_deepseek(original_text, api_key, release_date=None):
    """
    使用 DeepSeek 处理 release notes
    
    Args:
        original_text: 原始文本
        api_key: DeepSeek API key
        release_date: 发布日期（YYYY-MM-DD）
    
    Returns:
        str: 处理后的文本
    """
    openai.api_key = api_key
    openai.api_base = "https://chat.d.run/v1"
    
    if release_date is None:
        release_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""请将以下release notes内容整理为文档站使用的Markdown格式，具体要求：
1. 日期处理：
   - 如果原文中已有日期（如 ## 2025-11-30），请保留原文日期
   - 如果原文中没有日期，使用：{release_date}
2. 版本结构为：
   ## YYYY-MM-DD
   ### vX.X.X
   - **新增** [功能描述]
   - **优化** [优化描述]
   - **修复** [修复描述]
3. 所有功能点按"新增"、"优化"、"修复"三类归并
4. 保持原始内容中的(CSP)等前缀标识

示例输出格式：
## 2025-11-30
### v0.45.0

- **新增** (CSP) 支持用户邀请注册身份绑定功能 API
- **新增** 支持 GProduct 对接 Webhook 功能 API
- **新增** 支持增删改查事件通知API
- **优化** 优化短信通道的配置方式
- **修复** 修复忘记密码短时间发送失败问题

以下是原始release notes内容：

{original_text}
"""
    
    response = openai.ChatCompletion.create(
        model="public/deepseek-v3",
        messages=[{"role": "user", "content": prompt}],
    )
    
    return response.choices[0].message["content"]


def run_command(cmd, cwd=None):
    """执行命令"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=True
    )
    
    if result.returncode != 0:
        raise Exception(f"命令执行失败: {cmd}\n错误: {result.stderr}")
    
    return result.stdout


def insert_release_notes(file_path, new_content):
    """
    在 release notes 文件开头插入新内容
    
    Args:
        file_path: release-notes.md 文件路径
        new_content: 新的 release notes
    """
    with open(file_path, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    lines = original_content.split('\n')
    
    # 找到第一个 ## 的位置
    insert_index = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('## ') and re.match(r'## \d{4}-\d{2}-\d{2}', line.strip()):
            insert_index = i
            break
    
    if insert_index == 0:
        # 没找到，追加到末尾
        new_lines = lines + ['', new_content.strip()]
    else:
        # 在第一个版本前插入
        new_lines = lines[:insert_index] + [new_content.strip(), ''] + lines[insert_index:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))


def push_to_github(processed_content, github_token, target_repo, file_path, create_pr=True):
    """
    推送到 GitHub（创建 PR 或直接推送）
    
    Args:
        processed_content: 处理后的 release notes
        github_token: GitHub token
        target_repo: 目标仓库（如 "DaoCloud/DaoCloud-docs"）
        file_path: 目标文件路径（如 "docs/zh/docs/ghippo/intro/release-notes.md"）
        create_pr: 是否创建 PR
    """
    log(f"准备推送到 {target_repo}...")
    log(f"目标文件: {file_path}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="github_docs_")
    log(f"临时目录: {temp_dir}")
    
    try:
        # Clone 目标仓库
        repo_url = f"https://{github_token}@github.com/{target_repo}.git"
        log("正在克隆目标仓库...")
        run_command(f'git clone --depth 1 "{repo_url}" "{temp_dir}"')
        
        # 配置 git
        run_command('git config user.name "Release Bot"', cwd=temp_dir)
        run_command('git config user.email "bot@daocloud.io"', cwd=temp_dir)
        
        # 创建新分支（如果要 PR）
        if create_pr:
            branch_name = f"auto-update-release-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            log(f"创建分支: {branch_name}")
            run_command(f'git checkout -b {branch_name}', cwd=temp_dir)
        
        # 更新文件
        release_notes_file = os.path.join(temp_dir, file_path)
        
        if not os.path.exists(release_notes_file):
            raise FileNotFoundError(f"目标文件不存在: {release_notes_file}")
        
        log("更新 release notes 文件...")
        insert_release_notes(release_notes_file, processed_content)
        
        # Commit
        run_command(f'git add "{file_path}"', cwd=temp_dir)
        
        # 检查是否有变更
        status = run_command('git status --porcelain', cwd=temp_dir)
        if not status.strip():
            log("⚠ 没有检测到文件变更，可能内容已存在")
            return False
        
        # 从内容提取版本号
        commit_msg = "docs: update ghippo release notes"
        lines = processed_content.split('\n')
        for line in lines:
            if line.strip().startswith('###'):
                version = line.strip().replace('###', '').strip()
                commit_msg = f"docs: add ghippo {version} release notes"
                break
        
        log(f"提交更改: {commit_msg}")
        run_command(f'git commit -m "{commit_msg}"', cwd=temp_dir)
        
        # Push
        if create_pr:
            log(f"推送分支: {branch_name}")
            run_command(f'git push origin {branch_name}', cwd=temp_dir)
            
            # 创建 PR
            log("创建 Pull Request...")
            create_github_pr(github_token, target_repo, branch_name, commit_msg, processed_content)
        else:
            log("推送到 main 分支...")
            run_command('git push origin main', cwd=temp_dir)
        
        log("✓ 推送成功！")
        return True
        
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def create_github_pr(token, repo, branch, title, body_content):
    """
    使用 GitHub API 创建 Pull Request
    
    Args:
        token: GitHub token
        repo: 仓库名（如 "DaoCloud/DaoCloud-docs"）
        branch: 分支名
        title: PR 标题
        body_content: PR 内容
    """
    url = f"https://api.github.com/repos/{repo}/pulls"
    
    # 构建 PR body
    pr_body = f"""## 自动更新 Release Notes

本 PR 由自动化脚本生成，包含以下更新：

{body_content[:500]}...

---
*由 GitHub Actions 自动创建*
"""
    
    data = {
        "title": title,
        "head": branch,
        "base": "main",
        "body": pr_body
    }
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    
    pr_url = response.json()["html_url"]
    log(f"✓ PR 创建成功: {pr_url}")
    
    return pr_url


def main():
    log("=" * 60)
    log("开始执行 Release Notes 同步任务")
    log("=" * 60)
    
    # 清空日志文件
    with open("sync_result.log", "w") as f:
        f.write("")
    
    # 读取配置
    gitlab_url = "https://gitlab.daocloud.cn"
    gitlab_project = "ndx/ghippo"
    
    # 目标仓库和文件路径配置
    # 测试环境：parsifal-rui/test-docs, release-notes.md
    # 正式环境：DaoCloud/DaoCloud-docs, docs/zh/docs/ghippo/intro/release-notes.md
    target_github_repo = os.environ.get("TARGET_REPO", "parsifal-rui/test-docs")
    target_file_path = os.environ.get("TARGET_FILE_PATH", "release-notes.md")
    
    # 读取环境变量
    gitlab_token = os.environ.get("GITLAB_TOKEN")
    drun_api_key = os.environ.get("DRUN_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    input_tag = os.environ.get("INPUT_TAG", "").strip()
    create_pr = os.environ.get("CREATE_PR", "true").lower() == "true"
    
    if not gitlab_token or not drun_api_key or not github_token:
        log("❌ 错误：缺少必要的环境变量")
        log(f"GITLAB_TOKEN: {'✓' if gitlab_token else '✗'}")
        log(f"DRUN_API_KEY: {'✓' if drun_api_key else '✗'}")
        log(f"GITHUB_TOKEN: {'✓' if github_token else '✗'}")
        sys.exit(1)
    
    try:
        # Step 1: 获取 GitLab release notes
        log("【步骤 1/3】从 GitLab 获取 release notes...")
        
        client = GitLabReleaseClient(gitlab_url, gitlab_token, gitlab_project)
        
        if input_tag:
            tag = input_tag
            log(f"使用指定版本: {tag}")
        else:
            tag = client.get_latest_release_tag()
            log(f"使用最新版本: {tag}")
        
        release_data = client.get_release_notes_from_file(tag)
        original_notes = release_data['content']
        log(f"✓ 获取成功（{len(original_notes)} 字符）")
        
        # 获取发布日期
        release_date = None
        try:
            tag_info = client.get_tag_info(tag)
            commit_date = tag_info['commit']['created_at']
            dt = datetime.fromisoformat(commit_date.replace('+08:00', '+00:00'))
            release_date = dt.strftime("%Y-%m-%d")
            log(f"发布日期: {release_date}")
        except:
            release_date = datetime.now().strftime("%Y-%m-%d")
            log(f"使用当前日期: {release_date}")
        
        # Step 2: DeepSeek 处理
        log("【步骤 2/3】使用 DeepSeek 处理...")
        processed_notes = process_with_deepseek(original_notes, drun_api_key, release_date)
        log(f"✓ 处理完成（{len(processed_notes)} 字符）")
        
        # Step 3: 推送到 GitHub
        log(f"【步骤 3/3】推送到 GitHub ({target_github_repo})...")
        log(f"目标文件: {target_file_path}")
        log(f"模式: {'创建 PR' if create_pr else '直接推送'}")
        
        success = push_to_github(processed_notes, github_token, target_github_repo, target_file_path, create_pr)
        
        if success:
            log("=" * 60)
            log("✓ 任务执行成功！")
            log("=" * 60)
        else:
            log("⚠ 任务完成，但没有更新（内容可能已存在）")
        
    except Exception as e:
        log(f"❌ 错误: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
