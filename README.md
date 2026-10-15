# smart-agent

个人资料阅读与学习助手。当前实现 DeepSeek 单轮问答、token 用量展示和 HTTP 接口。
资料检索、多轮记忆与 Agent 工具将逐步加入。

## 运行

在项目根目录使用项目虚拟环境，安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

设置 `DEEPSEEK_API_KEY` 环境变量。也可以在 IDE 的运行配置中提供。
`config.yaml` 保存模型、API 地址、超时、重试次数和密钥环境变量名，密钥不写入 YAML。
当前不会自动读取 `.env` 文件。

命令行：

```powershell
.\.venv\Scripts\python.exe .\cli.py
```

HTTP 服务：

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.chat_api:app --reload
```

访问 http://127.0.0.1:8000/docs，通过 `POST /api/chat` 提交 `{"question": "什么是 RAG？"}`。

成功返回 `answer`、`usage`、`model`。接口未返回完整 token 用量时 `usage` 为 `null`。
空白问题返回 400，缺失字段或错误类型返回 422，模型调用失败返回 500。
缺少密钥或配置错误时启动失败，并提示配置问题。

## 文件职责

| 文件 | 职责 |
| --- | --- |
| `api/chat_api.py` | HTTP 请求、错误响应与应用启动 |
| `schemas/chat.py` | 请求与响应模型 |
| `chat_service.py` | Prompt、模型调用、结果封装 |
| `settings.py` | CLI 与 API 共用的配置读取 |
| `config.yaml` | 非敏感运行配置 |
| `prompt.py` | 系统提示词 |
| `cli.py` | 命令行输入与显示 |

当前连续提问是独立调用，还未携带会话历史。

## 本地验证

测试使用模拟模型与服务，不调用 DeepSeek，也不需要真实密钥：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试客户端需要 `httpx`，通过 `requirements-dev.txt` 安装。
