# smart-agent 项目续接说明

新会话开始时先阅读本文档并检查代码状态。不要重复已经完成的向量化、Qdrant 入库和 Top-K 验证；优先完成 metadata 检索过滤与最小 RAG。

## 1. 项目目标与已确认选择

`smart-agent` 是个人学习资料阅读与问答助手，使用真实资料逐步练习 RAG 和 Agent 工程。

技术方向：

- 聊天模型：DeepSeek，配置在 `config.yaml`。
- Embedding：阿里百炼 `qwen3.7-text-embedding-flash`，与聊天模型独立配置。
- 向量数据库：Docker Qdrant。
- API：FastAPI；前端 React + Vite 放到后端 RAG 契约稳定之后。
- 当前不做微调、复杂 Agent、混合检索或精排；先完成可解释、能引用来源的基础 RAG。

用户已确认：Embedding 向量化、写入 Qdrant、Top-K 向量检索都已实际验证通过。不要再把这些阶段描述成未验证或要求从头重做。相似度分数只用于排序，不是百分比或正确率。

首批目标资料和问题：

1. AI Agent PDF：怎样在上下文长度、回答质量和调用成本之间取舍？
2. Java Markdown 笔记：简单介绍通用离线导出与报表组件。
3. 《斗破苍穹》TXT 前 100 章：云韵是谁？

TXT 小说为 GB18030，Markdown 为 UTF-8。PDF 引用页码，TXT 引用章节，Markdown 引用文件名和标题路径。

## 2. 当前架构

数据链路目标：

```text
MarkdownLoader / PdfLoader / TxtLoader
  -> list[DocumentChunk]
  -> IndexingService
  -> EmbeddingService.embed_documents()
  -> VectorStoreService.upsert_documents()
  -> Qdrant

用户问题
  -> EmbeddingService.embed_query()
  -> VectorStoreService.search()
  -> 带来源的上下文
  -> DeepSeek
  -> answer + sources + usage
```

模块职责：

- Loader 只负责读取、解析、分块和来源 metadata，不连接 Embedding/Qdrant。
- `DocumentChunk` 是 loader 到索引层的统一结构，并能转换成 LangChain `Document`。
- `EmbeddingService` 负责文档和问题向量化，文档批次上限为 20。
- `VectorStoreService` 负责 collection、upsert 和向量检索。
- `IndexingService` 编排分块转换、Embedding、维度校验与 upsert；它不是 HTTP 微服务。
- `ChatService` 当前实现独立的单轮 DeepSeek 问答；后续要在不破坏现有 API 测试的前提下增加基于检索上下文的回答能力。

## 3. 当前代码状态

### 已实现

- `services/chat_service.py`：DeepSeek 单轮问答、usage 和模型错误处理。
- `api/chat_api.py`、`schemas/chat.py`：`POST /api/chat` 单轮问答 API。
- `services/embedding_service.py`：文档分批与 query embedding。
- `services/vector_store_service.py`：Qdrant collection 校验、稳定 point ID、upsert、Top-K 检索。
- `schemas/document.py`：统一 `DocumentChunk` 与 `SourceType`。
- `loader/markdown_loader.py`：UTF-8、Markdown 标题层级、递归切分，返回 `DocumentChunk`。
- `loader/pdf_loader.py`：PDF 页解析和页内切分，返回 `DocumentChunk`，含来源和页码。
- `loader/custom_txt_loader.py`：`TxtLoader` 默认按 GB18030 读取并识别常见中文章节格式；`CustomTextLoader` 保留兼容别名。
- `services/indexing_service.py`：统一 `index_chunks()` 及 `index_markdown/pdf/txt()` 入口；默认组装配置和服务，也支持依赖注入。
- `settings.py` 与 `config.yaml`：有 Qdrant URL、collection 名、向量维度配置。
- `tests/test_indexing_service.py`：验证公共编排逻辑、空输入和 Embedding 返回数量。

### 重要边界和待核对项

- `config.yaml` 当前 collection 名仍叫 `smart_agent_pdf_demo`，但索引服务计划把多种来源写入同一 collection。建议下一步改为中性名，如 `smart_agent_knowledge`，并确认向量维度 `1024` 与实际模型一致。
- 多来源共用 collection 不会自动限制检索范围。当前 `VectorStoreService.search()` 尚无 metadata filter 参数；写入 payload 已把来源信息放在 `metadata` 中。下一步应加可选过滤，例如 `source_type=txt` 或指定 `source`，并在检索测试中验证过滤确实生效。
- 当前三种 `index_*()` 都共用一个 collection。不要为每个文件建 collection。若不同资料将来使用不同 embedding 模型或维度，再按向量兼容性决定是否拆 collection。
- `IndexingService` 的 `vector_store` 可注入，但实际服务仍按设置中的 vector size 检查 Embedding 输出。若调整该接口，需保持配置与 collection 校验一致。
- 当前已提交到工作区但尚未提交 Git 的改动需要保留；开始新会话先看 `git status`，不要重置或覆盖。
- 本仓库工作区可能带有未跟踪的 `docs/Python廖雪峰.pdf`，这是用户资料，勿删除。
- TXT loader 目前用通用章节正则，真实《斗破苍穹.txt》不在当前 `docs` 文件夹内，需在文件可用时抽样核对章节格式与 GB18030 解码；不要假定临时样本文本等同于真实小说验收。

## 4. 当前配置

`config.yaml` 包含：

```yaml
embedding:
  api_key_name: ALI_API_KEY
  model: qwen3.7-text-embedding-flash
  max_retries: 2
  max_batch_size: 20

qdrant:
  url: http://localhost:6333
  collection_name: smart_agent_pdf_demo # 应改成中性的共享 collection 名
  vector_size: 1024
```

API key 通过环境变量读取，不要写入配置或日志。

## 5. 最近验证情况

最近一次实现 `IndexingService` 后，本地测试结果：

- indexing service 测试：3 项通过；
- API 测试：2 项通过；
- Embedding service 测试：2 项通过；
- `compileall` 与 `git diff --check` 通过。

这些测试使用假 Embedding/Qdrant，验证编排逻辑，不代表最近刚执行了真实 Embedding 或 Qdrant 端到端流程。真实向量化、Qdrant 入库、Top-K 已由用户确认此前验证通过。

## 6. 下一阶段开发顺序

### 第 1 步：整理共享 collection 与 metadata 过滤

1. 把 `qdrant.collection_name` 改成中性共享名，例如 `smart_agent_knowledge`。切换名称会新建 collection；已有 demo collection 数据不会自动迁移或删除。
2. 给 `VectorStoreService.search()` 增加可选过滤参数，优先支持明确的 metadata 条件，例如 `source_type`、`source`。
3. 在 Qdrant payload 中确认过滤字段路径对应当前结构 `metadata.source_type` / `metadata.source`。
4. 加单元测试或本地 Qdrant 集成测试：有多个来源数据时，过滤结果只返回指定来源。
5. 由用户决定首次索引的范围；建议先索引 Markdown 目标资料和 PDF 小样本，不要未经检查就索引整本小说。

### 第 2 步：核对三个 Loader 的真实输出

1. 对 Markdown 检查总 chunk 数、最大长度、标题 metadata、稳定 ID。
2. 对 PDF 检查页码从 1 起、无 title metadata 时回退到文件名、空页处理。
3. 取得真实 TXT 后检查编码和章节正则，确认每段不会跨章节，chapter metadata 准确；首轮只索引前 100 章。
4. 如真实小说章节格式不匹配，只调整 `TxtLoader` 的章节识别规则，不让索引服务承担格式解析。

### 第 3 步：通过 IndexingService 分资料索引

1. 使用 `index_markdown()`、`index_pdf()`、`index_txt()`，不要重复写手工的 Embedding/upsert 流程。
2. 核对返回写入数、collection point 数、metadata 和重复运行幂等性。
3. 索引遇到失败时记录文件和错误，不把真实密钥、完整向量打印出来。

### 第 4 步：实现最小 RAG

1. 新增检索问答 service：问题校验 -> query embedding -> Top-K（可带过滤）-> 上下文和来源整理 -> DeepSeek 回答。
2. Prompt 要求只依据给定检索上下文回答；证据不足时明确说资料中没有找到。
3. 来源必须由检索结果 metadata 产生，不能依赖模型编造文件名、章节或页码。
4. 扩展响应 schema，返回 `answer`、`sources`（source/title/chapter/page/score 等）和 `usage`。
5. 保持现有 `POST /api/chat` 行为兼容；可以新增 RAG 路由，或明确升级契约并同步测试。
6. 用 fake embedding、fake vector store、fake chat model 写 API/service 测试；再用真实服务做少量端到端手工验收。

### 第 5 步：建立小型检索与回答评测

为三个首批问题记录期望来源、期望章节或页码、答案必须包含的事实。每次调整 Top-K、chunk size、过滤或 Prompt 后复跑，观察召回来源和回答依据。先修复基础召回问题，再考虑混合检索和 reranker。

### 后续阶段

基础 RAG 评测稳定后，再依序考虑多轮上下文管理、BM25 混合检索、reranker、Agent 工具调用、React + Vite 页面。当前不需要微调。

## 7. 新会话启动提示

```text
请先阅读 D:\project\Smart-agent\docs\project-handoff.md 并检查当前 git status 和代码。
我已经验证过 Embedding 向量化、Qdrant 入库和 Top-K 检索，不要重复这些阶段。
从“第 1 步：整理共享 collection 与 metadata 过滤”开始，先检查现有 VectorStoreService payload 结构，完成可选 metadata filter 和测试；然后继续按文档路线推进最小 RAG。保留工作区现有改动和未跟踪资料文件。
```

## 8. 不要重复或误解的事项

- 项目定位是个人学习资料助手，不是订单或售后业务系统。
- 聊天模型和 Embedding 模型分开配置、分开调用。
- TXT 可用独立 `TxtLoader`，因为编码和章节定位与 Markdown 不同；不要把小说仅当成 Markdown 处理。
- Loader 只负责读取、解析和来源 metadata；Embedding、Qdrant 编排放在索引层。
- 共用 collection 时必须通过 metadata filter 控制检索范围；同一个 collection 不等于只能全库无差别搜索。
- 不要按每个文件创建 collection；collection 拆分应基于向量配置或清晰隔离需求。
- 不要在没有评测集的情况下直接加入精排、混搜或微调。
- 来源由程序从检索 metadata 返回，不让模型猜测。
- 不要恢复旧兼容文件：`chat_services.py`、`file_acquire.py`、`api/user_api.py`、`schemas/ChatRequest.py`。
