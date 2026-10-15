# 任务 06：解析 Markdown 并保留来源

> 状态：已完成。以下旧任务说明仅作历史记录，以本段为准：正式实现位于 `loader/markdown_loader.py`，使用 `TextLoader`、`MarkdownHeaderTextSplitter` 和递归字符切分，返回 `list[Document]`。当前验收只要求 `source` 文件名与 h1–h6 标题 metadata，不要求 `location` 或原始行号，也不要求手写 Markdown 解析。实测当前学习资料返回 495 个片段，全部带标题 metadata，最大片段 500 字符；本地解析无需 DeepSeek 密钥。下一步为独立 Embedding 模型接入。

这一步开始进入 RAG 的文档处理部分。先处理 Markdown，因为它编码稳定、标题结构清晰、内容短，便于检查结果。

## 目标

把 Markdown 文件解析成带来源信息的文档片段。暂时不调用模型、不生成向量、不连接 Qdrant。

## 目标数据结构

每个章节先使用一个普通字典表示：

```python
{
    "content": "该标题下的正文",
    "source": "饶升-Java后端开发工程师-精简结构版.md",
    "title": "通用离线导出与报表组件",
    "location": "第 56 行附近",
}
```

## 需要你实现的文件

```text
document/
├── __init__.py
└── markdown_loader.py
```

实现：

```python
def load_markdown(path: str) -> list[dict]:
    ...
```

## 行为要求

1. 使用 UTF-8 读取 Markdown。
2. 识别 ATX 标题，例如 `#`、`##`、`###` 开头的行。
3. 一个标题与下一个同级或更高层级标题之间的内容归到当前章节。
4. 没有标题的开头内容可以忽略，或归入标题为空的章节，但行为要固定并写在注释中。
5. 过滤空章节，不返回只有标题没有正文的项。
6. `source` 使用文件名，不把完整本机路径暴露给回答层。
7. `location` 至少记录起始行号，例如 `第 56 行附近`。
8. 标题中去掉 Markdown 的 `#` 和首尾空格。

本次先按每个标题切分，不要一次把所有正文合并成一个片段。后面的 chunk 切分会作为单独任务处理。

## 验收问题

使用：

```text
C:\Users\pu\Documents\notes\饶升-Java后端开发工程师-精简结构版.md
```

运行一个临时脚本打印：

- 返回章节总数；
- 找到标题 `通用离线导出与报表组件` 的章节；
- 打印它的 `source`、`title`、`location` 和正文；
- 检查正文包含“异步导出”“流式写出”等原文词语。

预期该章节的起始位置在文件第 56 行附近，不能把整份简历的内容放进这个章节。

## 你需要理解的 Agent/RAG 关键点

- Loader 解决“如何把文件转换成程序可处理的数据”。
- Metadata 解决“这段内容来自哪里”。
- 回答中的引用必须来自 metadata，不能让模型自己猜页码、章节或文件名。
- 解析阶段保存结构，后面的切分、Embedding 和检索阶段才能继续使用这些来源信息。

## 完成后提交

发回 `document/markdown_loader.py`，以及运行脚本的输出。下一步我会审查章节边界，再安排统一的 `DocumentChunk` 结构和 PDF/TXT Loader。
