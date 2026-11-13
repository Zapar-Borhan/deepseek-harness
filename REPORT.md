# DeepSeek Harness 项目报告

## 一、项目说明

这是一个简单的 DeepSeek API 命令行工具，主要用于快速提问和批量测试提示词。项目使用 Python 标准库编写，不需要额外安装第三方依赖。

## 二、主要功能

- 通过 `ask` 命令发送单条问题并显示回答。
- 通过 `run` 命令读取 JSONL 测试用例。
- 保存每条用例的回答、执行状态、耗时和 token 用量。
- 支持自定义模型、温度、最大输出长度和 API 地址。
- 提供基础单元测试和 GitHub Actions 自动测试配置。

## 三、使用方法

先设置环境变量：

```powershell
$env:DEEPSEEK_API_KEY = "你的 API Key"
```

单次提问：

```powershell
python harness.py ask "请解释什么是递归"
```

批量运行：

```powershell
python harness.py run
```

测试：

```powershell
python -m unittest discover -s tests -v
```

## 四、测试情况

项目已完成本地离线测试，共 3 个测试用例，全部通过。测试不需要真实 API Key，也不会产生 API 调用费用。

## 五、项目地址

https://github.com/Zapar-Borhan/deepseek-harness

## 六、后续可以改进的地方

目前 `expected` 字段只用于人工对照，还没有自动评分功能。后续可以增加关键词匹配、规则评分或人工评审结果汇总。
