# DeepSeek Harness

一个简单、零第三方依赖的 DeepSeek Chat API 命令行 harness。它提供两种模式：

- `ask`：发送一次提示词并直接打印回答。
- `run`：读取 JSONL 用例，逐条调用 API，并把结果写成 JSONL，包含状态、耗时和 token 用量。

## 快速开始

需要 Python 3.10 或更高版本。

```powershell
cd deepseek-harness
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API Key"
python harness.py ask "用一句话解释什么是递归。"
```

也可以复制 `.env.example` 作为配置参考。项目不会自动读取 `.env`，这样可以避免引入 dotenv 依赖；在 shell、CI 或 GitHub Actions 中注入环境变量即可。

## 运行评测用例

默认读取 `cases.jsonl`，结果写到 `results/results.jsonl`：

```powershell
python harness.py run
```

自定义文件、模型和参数：

```powershell
python harness.py run `
  --cases cases.jsonl `
  --output results/my-run.jsonl `
  --model deepseek-chat `
  --temperature 0.2 `
  --max-tokens 512
```

用例是一行一个 JSON 对象，`input` 必填，`id`、`system`、`expected` 可选：

```json
{"id":"case-1","input":"解释 HTTP 304。","expected":"提到缓存验证和 Not Modified。"}
```

`expected` 目前只作为结果中的人工评审参考，不会自动判分。每条结果包含 `status`、`output` 或 `error`、`latency_ms` 和 API 返回的 `usage`。

## API 兼容性

默认请求地址是 `https://api.deepseek.com/chat/completions`。可以通过 `DEEPSEEK_BASE_URL` 或 `--base-url` 指向兼容 OpenAI Chat Completions 的网关。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试不需要 API Key，也不会发起网络请求。
