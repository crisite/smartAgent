# smart-agent 项目续接说明

本文档用于在新的 Codex/开发会话中恢复项目背景、当前进度和后续路线。开始新会话时，先阅读本文档，再检查代码，不要从最初的聊天功能重新开始。

## 1. 项目定位

项目名称已经确定为 `smart-agent`，正式目录是：

```text
D:\project\Smart-agent
```

这是一个面向个人学习资料的智能阅读与问答助手，目标不是绑定订单、售后或某个业务系统，而是通过真实资料逐步练习完整的 Agent/RAG 开发流程。

首批资料来源：

```text
D:\books\AI-Agents-in-Depth-zh-CN.pdf
C:\Users\pu\Documents\notes\饶升-Java后端开发工程师-精简结构版.md
D:\books\斗破苍穹.txt
```

首批验收问题：

1. AI Agent 资料：怎样在上下文长度、回答质量和调用成本之间取舍？
2. Java 学习笔记：简单介绍通用离线导出与报表组件。
3. 《斗破苍穹》前 100 章：云韵是谁？

小说 TXT 文件是 GB18030 编码；Markdown 学习笔记是 UTF-8。PDF 后续使用页码作为来源定位，TXT 后续使用章节作为来源定位。

用户情况：有 Java 后端开发经验，能看懂工程代码，但 Python 和 Agent 相关内容还需要通过项目逐步练习。每天可以投入约 8 小时。普通工程封装、配置整理、接口规范等内容可以由助手直接完成；Agent、RAG、Embedding、检索、工具调用、状态管理等核心内容要由助手主导解释，并安排用户理解和验证。

## 2. 已确定的技术方向

### 模型分工

- 聊天模型：DeepSeek，当前配置模型名为 `deepseek-v4-pro`。
- Embedding 模型：阿里百炼 `qwen3.7-text-embedding-flash`。
- 聊天模型和 Embedding 模型必须独立配置、独立服务，不能混用。

最初考虑过 `text-embedding-v4`，但用户在百炼控制台实际可见的是 `qwen3.7-text-embedding-flash`，因此以账号当前可用模型为准，不再围绕 `text-embedding-v4` 改配置。

### 基础设施

- 向量数据库计划使用 Docker 部署 Qdrant。
- 当前还没有正式接入 Qdrant；必须先完成 Embedding 和相似度验证，再建立 collection 和写入数据。
- 前端计划使用 React + Vite，后端继续使用 FastAPI。网页接入会在后端检索链路稳定后进行。

### 目标能力

项目按阶段建设：

```text
资料读取
  -> 结构化分片
  -> Embedding
  -> Qdrant 向量存储
  -> Top-K 向量检索
  -> 带来源的 RAG 问答
  -> 多轮会话和上下文控制
  -> 混合检索、精排、评测
  -> 工具调用和 Agent 决策
  -> React + Vite 网页
```

微调不是第一阶段必需能力。先把可解释、可评测的检索链路做稳定，再根据数据量和实际问题判断是否需要微调。混合检索、精排、查询改写等能力可以在基础 RAG 跑通后逐步加入。

## 3. 当前目录结构

```text
D:\project\Smart-agent
├── api/
│   ├── __init__.py
│   └── chat_api.py
├── docs/
│   ├── current-architecture.md
│   ├── project-handoff.md       # 本文档
│   ├── task-06-markdown-parser.md
│   ├── task-07-embedding-similarity.md
│   └── 资料文件...
├── loader/
│   ├── base_loader.py
│   └── markdown_loader.py
├── schemas/
│   ├── __init__.py
│   ├── chat.py
│   └── info_source.py
├── services/
│   ├── chat_service.py
│   ├── embedding_service.py
│   └── vector_store_service.py
├── tests/
│   ├── test_api.py
│   └── test_embedding_service.py
├── qdrant/
│   └── docker-compose.yml
├── qdrant_demo.py
├── cli.py
├── config.yaml
├── embedding_demo.py
├── prompt.py
├── settings.py
├── README.md
├── requirements.txt
└── requirements-dev.txt
```

旧兼容文件已经按用户要求删除，不要恢复旧入口：

- `chat_services.py`
- `file_acquire.py`
- `api/user_api.py`
- `schemas/ChatRequest.py`

## 4. 已完成内容

### 4.1 DeepSeek 单轮问答

正式实现位于 [services/chat_service.py](../services/chat_service.py)。

`ChatService` 初始化一次 `ChatDeepSeek` 和 Prompt chain，`ask(question)` 返回：

```python
{
    "answer": "...",
    "usage": {
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
    } | None,
    "model": "...",
}
```

已处理：

- 空问题抛出 `ValueError`；
- 模型请求失败转换为 `ModelCallError`；
- API 返回的 token 用量缺失时使用 `None`，不把未知用量伪装成 0；
- CLI 会在回答后显示 token 使用情况；
- CLI 和 FastAPI 通过 `create_chat_service()` 使用同一套配置入口。

### 4.2 FastAPI 接口

正式接口为：

```text
POST /api/chat
```

请求：

```json
{
  "question": "什么是 RAG？"
}
```

响应模型在 [schemas/chat.py](../schemas/chat.py)，包含 `ChatRequest`、`TokenUsage` 和 `ChatResponse`。

`api/chat_api.py` 使用应用生命周期初始化共享服务，并在测试时允许注入假服务。此前 API 测试已经验证：正常响应和空问题 400 响应。

### 4.3 Markdown 解析和分片

正式实现位于 [loader/markdown_loader.py](../loader/markdown_loader.py)。当前流程是：

```text
TextLoader
  -> MarkdownHeaderTextSplitter
  -> RecursiveCharacterTextSplitter
  -> list[Document]
```

当前行为：

- UTF-8 读取 Markdown；
- 识别 h1 到 h6；
- 标题路径写入 `h1` 到 `h6` metadata；
- 写入 `source` 文件名，不暴露完整本机路径；
- 再按 `chunk_size=500`、`chunk_overlap=50` 进行长度切分；
- 当前学习资料实测得到 495 个片段，全部带标题 metadata，最大片段长度为 500 字符；
- 本地 Markdown 解析不需要 DeepSeek 或 Embedding API Key。

第一版不保存原始行号。原因是标题切分和递归切分会重新组织文本，切分后的 chunk 与原始行号没有简单可靠的映射。当前来源定位使用“文件名 + 标题路径”；后续 PDF 使用页码，TXT 使用章节。

### 4.4 Embedding 服务整理

正式实现位于 [services/embedding_service.py](../services/embedding_service.py)。配置位于 [config.yaml](../config.yaml)。

当前配置形态：

```yaml
embedding:
  api_key_name: ALI_API_KEY
  model: qwen3.7-text-embedding-flash
  max_retries: 2
  max_batch_size: 20
```

`EmbeddingService` 暴露：

```python
service.embed_documents(texts)
service.embed_query(question)
```

百炼该模型单批最多 20 条，服务内部会自动按不超过 20 条分批。文档向量使用 `text_type=document`，问题向量使用 `text_type=query`，由 LangChain 的 `DashScopeEmbeddings` 完成。

验证脚本位于 [embedding_demo.py](../embedding_demo.py)，它会：

1. 对两段示例文本生成文档向量；
2. 对一个问题生成查询向量；
3. 检查数量和向量维度；
4. 计算余弦相似度；
5. 只打印向量前 5 个值，不打印完整向量。

任务说明位于 [docs/task-07-embedding-similarity.md](task-07-embedding-similarity.md)。

### 4.5 Qdrant 向量存储（已实现，待 Docker 验证）

实现位于 [services/vector_store_service.py](../services/vector_store_service.py)，数据结构位于 [schemas/retrieval.py](../schemas/retrieval.py)。

- collection 使用运行时实际 Embedding 维度和 Cosine 距离；
- point payload 保存 `page_content` 与完整来源 metadata；
- point id 由内容和 metadata 稳定生成，重复索引会覆盖原 point；
- 检索返回内容、来源、标题路径、metadata 和相似度分数；
- [qdrant_demo.py](../qdrant_demo.py) 只索引学习资料前 8 个 Markdown chunk，并执行 Top-3 检索，不调用 DeepSeek；
- Docker Compose 文件为 [qdrant/docker-compose.yml](../qdrant/docker-compose.yml)，数据写入命名卷。

当前容器尚未实际启动，所以上述 Qdrant 写入与检索需要在 Docker daemon 可用后验证。

## 5. 当前待确认状态

Embedding 阶段已由助手实际验证通过，且本地测试通过。Qdrant 的配置和小样本验证脚本已准备好；当前机器已安装 Docker Compose，但 Docker Desktop Linux daemon 未运行，且项目虚拟环境尚未安装 `qdrant-client`。下一步是启动 Docker daemon、安装项目依赖，然后执行 Qdrant demo。

运行：

```powershell
cd D:\project\Smart-agent
$env:ALI_API_KEY = "你的阿里百炼 API Key"
.venv\Scripts\python.exe embedding_demo.py
```

预期观察：

- 文档数量为 2；
- 向量维度非空，通常为 1024；
- 问题向量维度和文档向量一致；
- “离线导出、分批处理”文本通常比 Markdown 文本获得更高相似度。

相似度只用于当前候选文本之间的排序，不能当作百分比或正确率。

`tests/test_embedding_service.py` 用于验证空问题校验和 20 条批量限制。本轮通过授权在项目虚拟环境运行完整测试集，4 项 API 与 Embedding 测试全部通过。沙箱内 Python 启动曾因权限限制失败；授权运行后解释器正常。

## 6. 后续开发路线

### 阶段 A：完成 Embedding 验证

用户需要理解：文本不是直接进入向量数据库的，必须先经过 Embedding 模型变成固定维度的浮点向量；问题也要使用同一模型转换，才能比较距离。

验收结果：已运行 `embedding_demo.py` 成功。文档数量为 2，文档与问题向量均为 1024 维；导出和分批处理文本相似度为 0.465514，Markdown 文本为 0.327054，排序符合预期。相似度只用于当前候选排序，不代表百分比或准确率。

### 阶段 B：Docker 部署 Qdrant

已新增：

```text
qdrant/
  docker-compose.yml
services/vector_store_service.py
schemas/retrieval.py
qdrant_demo.py
```

Compose 配置和操作说明位于 `qdrant/docker-compose.yml`、`docs/task-08-qdrant.md`。Docker 已安装，但本轮检查时 Linux daemon 不可用，Qdrant 集成测试尚未运行。

先用少量 Markdown chunk 验证，不要一开始导入全部 PDF 和小说。建立 collection 时：

- `size` 使用实际 Embedding 向量维度；
- `distance` 使用 Cosine；
- payload 保存 `page_content` 和来源 metadata；
- point id 使用稳定且可重复生成的标识。

先实现“写入 + Top-K 检索 + 打印结果”，暂时不要交给 DeepSeek。

### 阶段 C：建立统一索引流程

将 Markdown、PDF、TXT Loader 的输出统一为 LangChain `Document`：

```python
Document(
    page_content="...",
    metadata={
        "source": "文件名",
        "title": "标题或章节",
        "page": 3,          # PDF 可有
        "chapter": "第 12 章", # TXT 可有
    },
)
```

增加统一的 indexing service，负责加载、分片、批量 Embedding 和写入 Qdrant。索引命令应可重复执行，后续需要处理 collection 重建或文档版本问题。

建议顺序：Markdown -> PDF -> TXT 前 100 章。小说文本不要和学习资料混成一个无法区分的 collection，至少要保留 `source_type` 或 `source` metadata。

### 阶段 D：实现最小 RAG

流程：

```text
用户问题
  -> query embedding
  -> Qdrant Top-K
  -> 拼接检索片段和来源
  -> DeepSeek 生成回答
  -> 返回 answer + sources + usage
```

要求：

- Prompt 明确要求只依据检索上下文回答；
- 没有足够证据时明确说资料中没有找到；
- 来源由程序传入，不让模型自行猜文件名、页码或章节；
- 接口响应增加来源列表，例如 `source`、标题、相似度；
- 记录检索耗时和模型 token 用量，便于后续评估。

### 阶段 E：评测检索质量

先建立少量固定问题集，覆盖三个资料源。每个问题记录：期望来源、期望章节/页码、可接受答案要点。

至少观察：

- Top-K 是否召回正确资料；
- chunk_size 和 overlap 对召回的影响；
- 相似度阈值是否过滤了明显无关内容；
- 混合资料库中学习笔记和小说是否互相干扰。

这一步是后续精排、混搜和查询改写的依据。没有评测集时，加入更多模型或算法很难判断是否真的变好。

### 阶段 F：逐步加入高级检索

推荐顺序：

1. Metadata 过滤，例如只检索学习资料或只检索小说；
2. BM25/关键词检索与向量检索混合；
3. 查询改写或多查询召回；
4. Reranker 精排；
5. 结果去重、相邻 chunk 合并和上下文压缩。

精排和混搜有实际价值，但要在基础 RAG 和评测完成后加入。微调放在更后面，除非已经有足够高质量的问答数据和明确的模型行为问题。

### 阶段 G：引入 Agent 能力

RAG 问答稳定后再加入 Agent，而不是一开始把所有逻辑交给 Agent。可设计的工具包括：

- `search_knowledge`：检索资料；
- `get_source_detail`：查看命中文档的完整来源信息；
- `list_documents`：列出可用资料；
- `compare_sources`：对多个资料来源进行对比。

需要重点学习：工具 schema、工具选择、参数校验、调用结果回传、最大循环次数、失败处理和状态管理。Agent 的价值在于根据问题选择工具和组织步骤，向量检索本身仍然是独立能力。

### 阶段 H：React + Vite 网页

后端 API 契约稳定后再生成前端。第一版页面只需支持：

- 输入问题并提交；
- 展示回答；
- 展示 token 用量；
- 展示引用来源和相似度；
- 显示加载中、错误和无检索结果状态。

前端可以直接使用 AI 辅助生成，但 API 请求字段、响应模型和来源展示必须由后端契约驱动。不要先堆页面，再反过来迁就不稳定的服务层。

## 7. 新会话的推荐启动顺序

新会话开始时，直接告诉助手：

```text
请先阅读 D:\project\Smart-agent\docs\project-handoff.md，检查当前代码状态。
按照文档中“当前待确认状态”和“后续开发路线”继续，不要重复实现已经完成的 DeepSeek、FastAPI 和 Markdown Loader。
```

助手随后应按以下顺序工作：

1. 启动 Docker Desktop，安装 `requirements.txt` 中新增的 Qdrant 客户端依赖；
2. 使用 `docker compose -f qdrant/docker-compose.yml up -d` 启动 Qdrant；
3. 运行 `qdrant_demo.py`，验证少量 Markdown chunk 的幂等写入与 Top-K 检索；
4. 再进入 PDF/TXT、统一索引流程、最小 RAG 和来源返回。

每完成一个阶段，都要更新本文档中的“已完成内容”和“当前待确认状态”，这样后续会话不会丢失上下文。

## 8. 不要重复或误解的事项

- 不要把项目重新改回订单系统；资料型学习助手是正式定位。
- 不要因为 `text-embedding-v4` 在当前控制台不可见而反复更换模型；当前采用 `qwen3.7-text-embedding-flash`。
- 不要把聊天模型当作 Embedding 模型使用。
- 不要直接把 495 个 Markdown chunk 一次发送给 Embedding API；服务已经按 20 条分批。
- 不要在第一版为了显示行号而手写整个 Markdown 解析器；当前来源定位先使用文件名和标题路径。
- 不要在没有检索评测的情况下直接加入精排、混搜或微调。
- 不要让模型凭空生成来源；来源必须来自检索结果 metadata。
- 不要恢复已经删除的旧兼容文件。

