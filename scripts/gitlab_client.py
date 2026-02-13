#!/usr/bin/env python3
"""
GitLab API 客户端
"""
import re
import requests
import base64
from urllib.parse import quote


class GitLabReleaseClient:
    """GitLab Release 客户端"""
    
    def __init__(self, gitlab_url, token, project_id):
        """
        初始化客户端
        
        Args:
            gitlab_url: GitLab 实例地址，如 https://gitlab.daocloud.cn
            token: Personal Access Token
            project_id: 项目 ID 或路径，如 865 或 "ndx/ghippo"
        """
        self.gitlab_url = gitlab_url.rstrip('/')
        self.token = token
        self.project_id = project_id
        self.headers = {
            "PRIVATE-TOKEN": token
        }
    
    def _encode_project_id(self):
        """URL 编码项目 ID（如果是路径格式）"""
        if isinstance(self.project_id, str) and '/' in self.project_id:
            return self.project_id.replace('/', '%2F')
        return self.project_id
    
    def list_tags(self, per_page=20):
        """
        列出所有 tags
        
        Args:
            per_page: 每页返回数量
            
        Returns:
            list: tag 对象列表
        """
        project_id_encoded = self._encode_project_id()
        url = f"{self.gitlab_url}/api/v4/projects/{project_id_encoded}/repository/tags"
        params = {"per_page": per_page, "order_by": "updated", "sort": "desc"}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_file_content(self, file_path, ref="master"):
        """
        获取仓库文件内容
        
        Args:
            file_path: 文件路径，如 "releasenotes/v0.44/releasenotes-v0.44.0.md"
            ref: 分支或 tag 名，默认 master
            
        Returns:
            str: 文件内容
        """
        project_id_encoded = self._encode_project_id()
        file_path_encoded = quote(file_path, safe='')
        url = f"{self.gitlab_url}/api/v4/projects/{project_id_encoded}/repository/files/{file_path_encoded}"
        params = {"ref": ref}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        # 文件内容是 base64 编码的
        content = base64.b64decode(data['content']).decode('utf-8')
        return content
    
    def get_release_notes_from_file(self, tag_name, releasenotes_base="releasenotes"):
        """
        从仓库文件获取 release notes
        
        Args:
            tag_name: tag 名称，如 "v0.44.0"
            releasenotes_base: release notes 文件夹基础路径
            
        Returns:
            dict: 包含 tag_name, content, file_path
        """
        # 解析版本号：v0.44.0 -> 0.44
        match = re.match(r'v(\d+)\.(\d+)\.(\d+)', tag_name)
        if not match:
            raise ValueError(f"无法解析 tag 名称: {tag_name}，期望格式如 v0.44.0")
        
        major, minor, patch = match.groups()
        version_dir = f"v{major}.{minor}"
        
        # 构建文件路径：releasenotes/v0.44/releasenotes-v0.44.0.md
        file_path = f"{releasenotes_base}/{version_dir}/releasenotes-{tag_name}.md"
        
        try:
            content = self.get_file_content(file_path, ref="master")
            return {
                "tag_name": tag_name,
                "content": content,
                "file_path": file_path,
                "source": "repository_file"
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"找不到 release notes 文件: {file_path}")
            raise
    
    def get_tag_info(self, tag_name):
        """
        获取指定 tag 的信息
        
        Args:
            tag_name: tag 名称
            
        Returns:
            dict: tag 对象
        """
        project_id_encoded = self._encode_project_id()
        url = f"{self.gitlab_url}/api/v4/projects/{project_id_encoded}/repository/tags/{tag_name}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def list_release_tags(self, per_page=20):
        """
        列出所有正式 release 的 tags（排除 -dev, -rc 等）
        
        Args:
            per_page: 每页返回数量
            
        Returns:
            list: 正式版本的 tag 列表
        """
        all_tags = self.list_tags(per_page=100)  # 拿多一点，方便筛选
        
        # 只保留正式版本：v0.44.0, v0.43.0 等，排除 v0.44.0-rc1, v0.44.0-dev1
        release_tags = []
        for tag in all_tags:
            tag_name = tag['name']
            # 匹配 vX.Y.Z 格式（不带后缀）
            if re.match(r'^v\d+\.\d+\.\d+$', tag_name):
                release_tags.append(tag)
                if len(release_tags) >= per_page:
                    break
        
        return release_tags
    
    def get_latest_release_tag(self):
        """
        获取最新的正式 release tag
        
        Returns:
            str: tag 名称
        """
        release_tags = self.list_release_tags(per_page=1)
        if not release_tags:
            raise Exception("没有找到任何正式版本的 tag")
        return release_tags[0]['name']
