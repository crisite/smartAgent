# 当前代码怎么工作

这份说明只解释目前已经出现、但你可能还没用过的工程写法。它们不是 Agent 核心；真正的 Agent 能力会在后面的检索、工具和状态任务中加入。

## 一次 HTTP 请求

```text
浏览器或接口客户端
        ↓ JSON
api/chat_api.py
        ↓ ChatRequest 校验
ChatService.ask()
        ↓
Prompt + DeepSeek
        ↓
ChatResponse
```

## 为什么有 settings.py

CLI 和 API 都需要模型名、API 地址、超时和密钥。如果两个入口分别读取配置，日后很容易出现“命令行使用一个模型、网页使用另一个模型”的情况。

`settings.py` 只做配置读取：

1. 从 `config.yaml` 读取模型、地址、超时和重试次数。
2. 从环境变量读取密钥。
3. 组装成一个 `Settings` 对象返回。

密钥不写进 YAML，也不写进代码。

## `@dataclass(frozen=True)` 是什么

`Settings` 是一个只装配置数据的类。`@dataclass` 自动生成构造函数和字段；`frozen=True` 表示创建后不能随意修改，避免运行中配置被某处悄悄改变。

它不是数据库模型，也不是 Agent 状态，只是配置对象。

## `lifespan` 和 `app.state`

在 `api/chat_api.py` 中：

```python
@asynccontextmanager
async def lifespan(app):
    app.state.chat_service = service_factory()
    yield
```

`lifespan` 是 FastAPI 的应用生命周期钩子。服务启动时执行 `yield` 之前的代码，关闭时执行之后的代码。本项目目前只利用启动部分，在启动时创建一次 `ChatService`。

`app.state` 是 FastAPI 应用对象上的共享存储。我们把服务放进去，接口函数通过 `request.app.state.chat_service` 取出它。这样每个请求都复用同一个模型客户端，不会每次请求重复初始化。

`async` 出现在这里是因为 FastAPI 生命周期接口采用异步形式；当前模型调用本身仍然是同步的 `invoke()`。

## `create_app` 和 `service_factory` 为什么存在

`create_app()` 是一个“创建 FastAPI 应用的函数”。正式入口最后执行：

```python
app = create_app()
```

参数 `service_factory` 默认是 `create_chat_service`。正式运行时，它会读取真实配置并创建 DeepSeek 服务。

测试时可以传入一个返回假服务的函数，让 HTTP 请求验证、400 响应和字段结构，而不调用真实模型。它是测试隔离手段，不是 Agent 的决策逻辑。

## Pydantic 请求和响应模型

`schemas/chat.py` 中的类描述 HTTP 数据结构：

- `ChatRequest`：客户端必须提交的 JSON。
- `TokenUsage`：token 统计字段。
- `ChatResponse`：服务返回的 JSON。

FastAPI 根据它们自动校验请求并生成 `/docs` 文档。模型返回的 `usage` 可能暂时没有，因此类型写成 `TokenUsage | None`；`null` 表示接口没有提供统计，不表示消耗为零。

## 为什么模型服务抛出 `ModelCallError`

用户输入错误和模型服务错误需要不同的 HTTP 状态码：

- 空问题：400，说明请求本身不合适。
- DeepSeek 调用失败：500，说明服务端处理失败。

`ModelCallError` 是一个专门的异常类型，让 API 层可以区分这两类错误。它不会改变模型能力，也不会自动重试业务流程。

## 当前刻意没有做的事

当前连续提问是彼此独立的调用；还没有会话历史、资料解析、向量检索、工具调用或 Agent 状态。下一阶段从 Markdown 文档解析开始，逐步把资料证据接入模型。
