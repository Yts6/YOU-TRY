# Step 12 · Prompt 工程 + 模板库

> 目标：手上有 10+ 个可复用的 Prompt 模板。
> 验收：随便给一段文本，10 分钟内写出"稳定输出 JSON"的 Prompt。

## 交付物

```
agent-learning/
├── prompts/
│   ├── __init__.py
│   └── templates.py          # 10 个模板 + 使用接口
└── step12_prompt_demo.py     # 演示 + 真实对比实验
```

## 10 个模板

| # | 模板名 | 用途 | 输出格式 |
|---|---|---|---|
| 1 | `qa_with_citation` | 带引用的问答（RAG 生成） | 自然语言 + [来源N] |
| 2 | `extract_json` | 结构化信息抽取 | 纯 JSON |
| 3 | `summarize` | 可控摘要 | 一段文字 |
| 4 | `score_with_reason` | 打分 + 理由（评估） | JSON |
| 5 | `query_rewrite` | 查询改写（多路召回） | 3 行文本 |
| 6 | `think_step_by_step` | CoT 分步推理 | 分步 + 答案 |
| 7 | `refuse_out_of_scope` | 越界拒答 | 自然语言 |
| 8 | `agent_system_prompt` | Agent 系统提示骨架 | 工具调用/总结 |
| 9 | `compare_two` | 两方案对比 | 分维度对比 |
| 10 | `few_shot_classify` | 少样本分类 | 单个类别名 |

## 怎么用

```python
from prompts.templates import get_prompt, list_templates

# 列出所有模板
for t in list_templates():
    print(t["name"], t["title"])

# 渲染模板
prompt = get_prompt(
    "qa_with_citation",
    context="[来源1] RAG 全称 Retrieval-Augmented Generation……",
    question="什么是 RAG？",
)
print(prompt)

# 查看模板详细信息
info = get_template_info("extract_json")
print(info["notes"])   # 注意事项
```

## 核心设计：模板即数据结构

每个模板不是一段裸文本，而是**带元数据的结构**：

```python
{
    "name": "带引用的问答",
    "purpose": "基于给定材料回答问题，并标注来源，避免幻觉",
    "scenario": "RAG 系统的生成环节",
    "required_vars": ["question", "context"],   # 缺了会报错
    "template": "...",                           # 正文
    "output_format": "自然语言 + [来源N] 标注",
    "notes": ["规则2是防幻觉的关键"],             # 使用注意事项
}
```

**好处**：
- `required_vars` 自动校验，不会漏传变量（实测缺变量会明确报错）
- 元数据能自动生成文档、在 UI 里展示
- 后续可以加版本管理、A/B 测试

## Prompt 工程核心技巧

### 1. 结构化（用 Markdown 标题分段）

```
## 参考资料
xxx
## 用户问题
xxx
## 回答
```

比一大段平铺的文字清晰得多，模型更容易抓住结构。

### 2. 约束输出格式

```
- 只输出 JSON，不要任何解释文字、不要 markdown 代码块标记
```

不说这句，模型就爱加 ```json 围栏和"好的，以下是……"。**配合 Pydantic 校验 + 失败重试**才是最稳的。

### 3. Few-shot 示例

纯规则描述不如给例子。例子要**覆盖边界情况**，否则模型遇到边界会乱猜。

### 4. 明确"不知道"的出口

```
- 如果参考资料中找不到答案，必须回答"根据现有资料无法回答该问题"，禁止猜测
```

**这是防幻觉最关键的一句**。实测证明：给了材料且允许说"不知道"，模型就真的会拒答（见下方实验）。

### 5. 角色设定帮模型选对知识域

```
你是一个严谨的知识库助手 / 你是 AI 领域专家
```

因为 token/RAG/MCP 这些词有多义（token 也是加密货币，MCP 也像工业协议），角色设定能帮模型选对领域。

## 真实对比实验（脚本自动跑）

运行 `python step12_prompt_demo.py`，同一个问题「什么是 MCP 协议？」：

| 策略 | 实测结果 |
|---|---|
| A. 无约束 | "MCP 通常指的是 **Modbus Control Protocol**，1979 年 Modicon 公司开发" ❌ |
| B. 给材料 + 只基于材料 | 正确回答 + `[来源1][来源2][来源3]` ✅ |
| C. 给无关材料 + 没答案就拒答 | "根据现有资料无法回答该问题。" ✅ |

**同一个问题无约束问三次，得到三个不同的错误答案。** 这是 RAG 价值的最有力证明。

详见 [`step7/模型幻觉实测记录.md`](../step7/模型幻觉实测记录.md)

## 常见坑

| 坑 | 表现 | 解法 |
|---|---|---|
| 无输出格式约束 | 想解析 JSON，拿到一堆解释文字 | 明确"只输出 JSON"+ Pydantic 校验重试 |
| 无"不知道"出口 | 模型硬编答案 | 加"找不到就说无法回答" |
| Prompt 太长无结构 | 模型忽略中间内容 | 用 Markdown 分段，关键约束放开头/结尾 |
| 变量忘记传 | KeyError 或留下 `{xxx}` | 用 `required_vars` 校验 |
| 一次改太多变量 | 出问题不知道哪个改动导致 | 每次只改一个点，对比效果 |

## 练习

1. 给 `extract_json` 写一个"失败自动重试"的调用封装（模型返回不合法 JSON 时重试 2 次）
2. 加一个模板 `translate_terms`：把中文术语翻译成英文，并保持术语表一致
3. 给模板库加版本字段 `version`，支持同一模板有 v1/v2 两个版本做 A/B
4. 用 `score_with_reason` 搭一个简易评估脚本：给 10 个 RAG 回答打分，算出平均分
