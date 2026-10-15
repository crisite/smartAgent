"""CLI 和 API 共用的配置读取入口。"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_document_dir(config_path: Path = CONFIG_PATH) -> Path:
    """只读取资料目录；本地解析不需要模型密钥。"""
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError("config.yaml 必须包含配置字段")
    directory = config.get("tmp_dir", "docs")
    if not isinstance(directory, str) or not directory.strip():
        raise ValueError("tmp_dir 必须是非空字符串")
    path = Path(directory)
    return path if path.is_absolute() else config_path.parent / path


@dataclass(frozen=True)
class Settings:
    """应用运行所需的配置；frozen 表示加载后不再修改。"""
    api_key: str = field(repr=False)
    model: str
    base_url: str
    timeout: float
    max_retries: int
    tmp_dir: str


@dataclass(frozen=True)
class EmbeddingSettings:
    """Embedding 服务配置，与聊天模型配置分开。"""

    api_key: str = field(repr=False)
    model: str
    max_retries: int
    max_batch_size: int


def load_settings(config_path: Path = CONFIG_PATH) -> Settings:
    """从 YAML 读非敏感配置，再从环境变量读密钥。"""
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("config.yaml 必须包含配置字段")

    model = config.get("model")
    key_name = config.get("api_key_name", "DEEPSEEK_API_KEY")
    base_url = config.get("base_url", "https://api.deepseek.com")
    tmp_dir = config.get("tmp_dir", "D:\\project\\Smart-agent\\docs\\")
    for name, value in (("model", model), ("api_key_name", key_name), ("base_url", base_url)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"配置 {name} 必须是非空字符串")

    api_key = os.getenv(key_name.strip())
    if not api_key or not api_key.strip():
        raise ValueError(f"未配置环境变量 {key_name.strip()}")

    timeout = config.get("timeout", 60)
    retries = config.get("max_retries", 1)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("timeout 必须是正数")
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise ValueError("max_retries 必须是非负整数")

    return Settings(
        api_key=api_key.strip(),
        model=model.strip(),
        base_url=base_url.strip(),
        timeout=float(timeout),
        max_retries=retries,
        tmp_dir=tmp_dir
    )

def load_embedding_settings(config_path: Path = CONFIG_PATH) -> EmbeddingSettings:
    """读取 Embedding 配置，并从环境变量读取百炼密钥。"""
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("config.yaml 必须包含配置字段")

    embedding = config.get("embedding")
    if not isinstance(embedding, dict):
        raise ValueError("embedding 必须是一个配置对象")

    model = embedding.get("model")
    key_name = embedding.get("api_key_name", "ALI_API_KEY")
    for name, value in (("model", model), ("api_key_name", key_name)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"配置 {name} 必须是非空字符串")

    api_key = os.getenv(key_name.strip())
    if not api_key or not api_key.strip():
        raise ValueError(f"未配置环境变量 {key_name.strip()}")

    retries = embedding.get("max_retries", 2)
    batch_size = embedding.get("max_batch_size", 20)
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 1:
        raise ValueError("embedding.max_retries 必须是正整数")
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or not 1 <= batch_size <= 20:
        raise ValueError("embedding.max_batch_size 必须是 1 到 20 的整数")

    return EmbeddingSettings(
        api_key=api_key.strip(),
        model=model.strip(),
        max_retries=retries,
        max_batch_size=batch_size,
    )

