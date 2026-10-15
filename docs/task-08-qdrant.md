# 任务 08：Qdrant 向量写入与 Top-K 检索

## 启动 Qdrant

在项目目录运行：

```powershell
docker compose -f qdrant/docker-compose.yml up -d
```

Qdrant HTTP API 使用 `http://localhost:6333`。数据保存在 Docker 命名卷 `qdrant_storage` 中。

## 运行小样本验证

在 `ALI_API_KEY` 已配置的终端运行：

```powershell
.venv\Scripts\python.exe qdrant_demo.py
```

脚本只读取首批 Markdown 学习资料的前 8 个 chunk。它先用 Embedding 服务生成文档向量，再用实际向量长度创建 Cosine collection，使用稳定 UUID 作为 point id，最后对问题向量执行 Top-3 检索。重复运行会覆盖相同 chunk 对应的 point。

## 检查结果

- 写入数量为 8（资料不足 8 段时按实际数量）；
- collection 向量维度与 Embedding 输出一致；
- 检索返回内容、来源、标题路径和相似度分数；
- 相关问题的学习资料通常排在不相关内容之前。

目前这个验证只检查写入和 Top-K 检索，还没有把检索结果交给 DeepSeek。
