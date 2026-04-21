# SAGT Agent Dockerfile 注释说明文档

## 概述

本 Dockerfile 用于构建 SAGT Agent 智能体服务的 Docker 镜像。该镜像基于 LangGraph API 官方基础镜像，集成了 SAGT Agent 的核心代码和依赖，提供完整的销售智能体服务能力。

---

## Dockerfile 逐行注释说明

```dockerfile
# 基于 LangGraph API 官方基础镜像构建
# 使用 Python 3.12 + Wolfi Linux 发行版，标签为 d18f703 的特定版本
FROM langchain/langgraph-api:3.12-wolfi-d18f703


# ==================== 本地代码包添加阶段 ====================

# -- Adding local package . --
# 将当前目录（sagt_agent 项目根目录）的所有文件复制到容器内的 /deps/sagt_agent 目录
# 这包含了项目的核心配置文件（pyproject.toml、requirements.txt、langgraph.json 等）
ADD . /deps/sagt_agent
# -- End of local package . --

# -- Adding non-package dependency src --
# 将项目的 src 目录复制到容器内的 /deps/outer-src/src 目录
# src 目录包含智能体的核心源代码，由于它不是一个标准的 Python 包（缺少 pyproject.toml），
# 需要单独处理
ADD ./src /deps/outer-src/src

# 生成 src 目录对应的 pyproject.toml 文件
# 通过循环逐行写入配置内容，将 src 目录转换为可安装的 Python 包
RUN set -ex && \
    for line in '[project]' \
                'name = "src"' \
                'version = "0.1"' \
                '[tool.setuptools.package-data]' \
                '"*" = ["**/*"]' \
                '[build-system]' \
                'requires = ["setuptools>=61"]' \
                'build-backend = "setuptools.build_meta"'; do \
        echo "$line" >> /deps/outer-src/pyproject.toml; \
    done
# -- End of non-package dependency src --

# ==================== 依赖安装阶段 ====================

# -- Installing all local dependencies --
# 遍历 /deps 目录下的所有依赖包并安装
# - 对每个子目录执行安装操作
# - 使用 uv pip install 以开发模式（-e）安装
# - 使用 --system 参数将包安装到系统 Python 环境
# - 使用 --no-cache-dir 避免缓存，减小镜像体积
# - 使用 -c /api/constraints.txt 应用 LangGraph API 的依赖版本约束
RUN for dep in /deps/*; do \
        echo "Installing $dep"; \
        if [ -d "$dep" ]; then \
            echo "Installing $dep"; \
            (cd "$dep" && PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e .); \
        fi; \
    done
# -- End of local dependencies install --

# ==================== 环境变量配置阶段 ====================

# 免费版 Smith 账号不需要 auth 认证，因此注释掉认证配置
# ENV LANGGRAPH_AUTH='{"path": "/deps/outer-src/src/auth/auth.py:auth"}'

# 配置自定义 HTTP 应用
# 指定 FastAPI 应用的路径，用于提供额外的 API 端点（如健康检查、令牌获取等）
ENV LANGGRAPH_HTTP='{"app": "/deps/sagt_agent/src/webapp/webapp.py:app"}'

# 配置 LangServe 图服务
# 指定 SAGT Agent 的主图定义路径，使 LangGraph API 能够加载和服务该图
ENV LANGSERVE_GRAPHS='{"sagt": "/deps/sagt_agent/src/graphs/sagt_graph/sagt_graph.py:graph"}'


# ==================== 镜像优化阶段 ====================

# -- Ensure user deps didn't inadvertently overwrite langgraph-api --
# 创建 LangGraph API 的空模块文件，确保用户依赖不会意外覆盖系统安装的 langgraph-api 包
# 这是一个安全措施，防止依赖冲突
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license && \
    touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py

# 重新安装 /api 目录下的包（包含 langgraph-api），确保其不会被用户依赖覆盖
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --

# -- Removing build deps from the final image ~<:===~~~ --
# 清理构建依赖，减小镜像体积
# 卸载 pip、setuptools、wheel 等构建工具
RUN pip uninstall -y pip setuptools wheel

# 删除 Python site-packages 中残留的 pip、setuptools、wheel 文件
RUN rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* && \
    find /usr/local/bin -name "pip*" -delete || true

# 进一步清理系统级的 pip、setuptools、wheel
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* && \
    find /usr/bin -name "pip*" -delete || true

# 使用 uv 卸载系统级的 pip、setuptools、wheel，并删除 uv 命令本身
RUN uv pip uninstall --system pip setuptools wheel && rm /usr/bin/uv /usr/bin/uvx
# -- End of removing build deps from the final image --

# 设置工作目录为项目根目录
WORKDIR /deps/sagt_agent
```

---

## 构建流程总结

| 阶段 | 操作 | 目的 |
|------|------|------|
| **基础镜像** | 使用 langchain/langgraph-api:3.12-wolfi-d18f703 | 提供 LangGraph API 运行环境 |
| **代码复制** | ADD . /deps/sagt_agent | 复制项目配置文件 |
| **代码复制** | ADD ./src /deps/outer-src/src | 复制源代码目录 |
| **包配置** | 生成 pyproject.toml | 将 src 转换为可安装包 |
| **依赖安装** | uv pip install | 安装所有项目依赖 |
| **环境配置** | ENV LANGGRAPH_HTTP/LANGSERVE_GRAPHS | 配置服务运行参数 |
| **冲突防护** | 创建空模块文件 | 防止用户依赖覆盖 langgraph-api |
| **镜像优化** | 卸载构建工具 | 减小镜像体积 |
| **工作目录** | WORKDIR /deps/sagt_agent | 设置默认工作路径 |

---

## 关键配置说明

### 环境变量

| 环境变量 | 值 | 说明 |
|----------|-----|------|
| `LANGGRAPH_HTTP` | `{"app": "/deps/sagt_agent/src/webapp/webapp.py:app"}` | 自定义 FastAPI 应用入口，提供健康检查、令牌获取等额外 API |
| `LANGSERVE_GRAPHS` | `{"sagt": "/deps/sagt_agent/src/graphs/sagt_graph/sagt_graph.py:graph"}` | 注册 SAGT Agent 主图，使其可通过 LangServe 访问 |

### 目录结构

```
/deps/
├── sagt_agent/          # 项目根目录（包含配置文件）
│   ├── src/             # 源代码（通过 ADD ./src 复制）
│   ├── pyproject.toml
│   ├── langgraph.json
│   └── ...
└── outer-src/           # 额外依赖目录
    ├── src/             # 实际源代码目录
    └── pyproject.toml   # 自动生成的配置文件
```

---

## 运行方式

### 构建镜像

```bash
docker build -f sagt.dockerfile -t sagt-agent .
```

### 运行容器

```bash
docker run -p 8000:8000 sagt-agent
```

### 访问服务

- **API 端点**: `http://localhost:8000`
- **健康检查**: `http://localhost:8000/sagt/health`
- **Graph UI**: `http://localhost:8000/sagt/playground`
- **API Docs**: `http://localhost:8000/docs`
