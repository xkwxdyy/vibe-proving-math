![vibe_proving](assets/banner.svg)

<p align="center">
面向数学研究者的 AI 平台
</p>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python"></a>
</p>

<p align="center">
中文 | <a href="README.md">English</a>
</p>

---

## 概述

**vibe_proving** 是面向数学研究者的 AI 平台。结合语言模型与定理检索，提供学习、求解、审查、检索等交互式工作流。

### 核心能力

- **学习模式** — 生成包含前置知识、证明、例子和扩展的结构化讲解，可调节本科或研究生难度
- **求解模式** — 自动证明生成，包含引用验证、置信度评分和反例检测
- **审查模式** — 对数学写作（LaTeX/PDF/图片）进行结构化分析，检查逻辑缺口、引用准确性和符号一致性
- **检索模式** — 在 900 万+ 定理中进行语义搜索，覆盖 arXiv、Stacks Project 等数学数据库

### 功能展示

> **说明**：视频演示将在后续更新中添加至 `app/视频效果展示/`。

![界面](assets/screenshot.png)

---

## 主要特性

### 1. 交互式学习

将任意数学陈述转化为全面的学习资源：
- 背景与动机
- 前置知识与定义
- 逐步证明演示
- 具体例子与反例
- 扩展与相关主题

**目标用户**：遇到陌生定理的学生、探索新领域的研究者。

### 2. 智能求解

生成–验证–修订流水线，包含质量控制：
- 直接检索：检查定理数据库中是否已有解答
- 证明生成：创建包含推理步骤的初始草案
- 独立验证：在不依赖生成器偏差的情况下验证逻辑
- 引用检查：通过 [TheoremSearch](https://www.theoremsearch.com) 验证定理引用
- 反例测试：在接受声明前尝试证伪
- 置信度评分：透明评估，明确表达不确定性

**输出格式**：结构化证明，包含置信度评分、已验证引用、失败路径和推理障碍。

### 3. 证明审查

数学写作的自动化分析：
- **逻辑一致性**：检测缺失步骤、循环论证、不合理跳跃
- **引用准确性**：验证引用定理的存在性和正确陈述
- **符号一致性**：跟踪变量作用域、假设依赖关系

**支持格式**：文本、LaTeX、图片（通过视觉模型）、PDF（通过 OCR）。

### 4. 定理发现

数学文献的语义搜索：
- 来自 arXiv、Stacks Project 等专业数据库的 900 万+ 定理索引
- 自然语言查询（无需公式语法）
- 相似度评分与排序
- 原始论文直链

---

## 安装

```bash
git clone https://github.com/ml1301215/vibe-proving-math.git
cd vibe-proving-math/app
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.toml config.toml
```

编辑 `config.toml`，至少设置：

```toml
[llm]
api_key = "your-api-key"
base_url = "https://api.deepseek.com/v1"  # 或其他 OpenAI 兼容端点
model = "deepseek-chat"
```

**推荐 LLM 提供商**：

| 提供商 | 优势 | Base URL | 获取密钥 |
|----------|-----------|----------|---------|
| DeepSeek | 高性价比推理 | `https://api.deepseek.com/v1` | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| Gemini | 强数学推理 | `https://generativelanguage.googleapis.com/v1beta/openai` | [aistudio.google.com](https://aistudio.google.com/apikey) |
| OpenAI | 通用可靠性 | `https://api.openai.com/v1` | [platform.openai.com](https://platform.openai.com/api-keys) |

启动服务器：

```bash
python -m uvicorn api.server:app --host 127.0.0.1 --port 8080
```

访问 Web 界面：`http://127.0.0.1:8080/ui/` 或 API 文档：`http://127.0.0.1:8080/docs`。

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 界面                             │
│         (Markdown + KaTeX + SSE 流式)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   FastAPI 服务器        │
          │  /learn  /solve  /review│
          │  /search  /formalize    │
          └────────────┬────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
┌────▼────┐    ┌──────▼──────┐   ┌─────▼─────┐
│学习流水 │    │   求解流水  │   │  审查流水 │
│  线     │    │     线      │   │    线     │
└────┬────┘    └──────┬──────┘   └─────┬─────┘
     │                │                 │
     └────────────────┼─────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
┌────▼──────┐  ┌─────▼──────┐  ┌─────▼────┐
│ LLM 核心  │  │  定理检索  │  │ Nanonets │
│ (OpenAI)  │  │           │  │   OCR    │
└───────────┘  └────────────┘  └──────────┘
```

### 质量控制机制

1. **引用验证**：外部数据库查找防止虚假引用
2. **独立验证**：在不访问生成器推理的情况下验证证明步骤
3. **反例生成**：在声称真理前主动尝试证伪
4. **LaTeX 清洗**：为前端渲染自动清理控制序列
5. **置信度报告**：系统在不确定时拒绝回答而非编造

---

## API 参考

完整文档见 `/docs`。核心端点：

| 端点 | 方法 | 用途 |
|----------|--------|---------|
| `/learn` | POST | 生成结构化讲解 |
| `/solve` | POST | 带验证的证明生成 |
| `/review_stream` | POST | 流式证明审查（文本/图片）|
| `/review_pdf_stream` | POST | PDF 上传与结构化分析 |
| `/search` | GET | 定理语义搜索 |
| `/formalize` | POST | 自然语言 → Lean 4（Beta）|

**示例**（求解模式）：

```bash
curl -X POST http://127.0.0.1:8080/solve \
  -H "Content-Type: application/json" \
  -d '{
    "statement": "证明：对所有素数 p > 2，p ≡ 1 或 3 (mod 4)",
    "stream": false
  }'
```

返回：

```json
{
  "verdict": "proved",
  "confidence": 0.89,
  "blueprint": "## 证明\n\n设 p 为素数且 p > 2...",
  "references": [
    {
      "name": "二次剩余模素数",
      "status": "verified",
      "similarity": 0.83,
      "link": "https://..."
    }
  ],
  "verification": {
    "overall": "passed",
    "goal_reached": true
  }
}
```

---

## 使用场景

### 学生

- **概念探索**：输入陌生定理获取前置知识分解
- **证明理解**：逐步演示包含推理注释
- **考试准备**：生成练习题和详细解答

### 研究者

- **文献综述**：定理数据库的语义搜索
- **证明起草**：生成包含引用建议的初始草稿
- **稿件审查**：提交前的自动一致性检查

### 教育工作者

- **教学材料**：自动生成多难度讲解
- **作业检查**：检测学生提交中的逻辑缺口
- **课程设计**：识别课程规划的前置链

---

## 测试

```bash
cd app
pytest tests -m "not slow"  # 快速回归（无外部 API 调用）
pytest tests                # 完整套件（需要 API 密钥）
```

测试覆盖：
- 配置解析与验证
- LLM 客户端集成（流式与非流式）
- 所有五种操作模式
- 引用验证流水线
- LaTeX 清洗
- 错误处理与边界情况

---

## 技术栈

- **后端**：FastAPI，支持 Server-Sent Events 渐进式流式输出
- **前端**：原生 HTML/CSS/JS，包含 KaTeX 和 Markdown 渲染（无构建工具链）
- **LLM 集成**：OpenAI 兼容接口（模型无关）
- **定理数据库**：[TheoremSearch](https://www.theoremsearch.com) API 集成
- **PDF 处理**：[Nanonets OCR](https://nanonets.com) 保留公式的提取
- **形式化验证**（Beta）：[Harmonic Aristotle](https://aristotle.harmonic.fun) 支持 Lean 4

---

## 贡献

欢迎数学社区的贡献：

- **错误报告**：[GitHub Issues](https://github.com/ml1301215/vibe-proving-math/issues)
- **功能请求**：描述使用场景和预期行为
- **代码贡献**：遵循 [CLAUDE.md](CLAUDE.md) 中的规范
- **文档**：改进示例、修正错误、翻译内容

**开发指南**：
- Python 代码遵循 PEP 8
- 前端更改需要缓存版本更新
- LaTeX 输出必须通过清洗
- 新端点需要测试覆盖

---

## 致谢

本项目建立在数学 AI 和定理证明的基础工作之上：

- [TheoremSearch](https://www.theoremsearch.com) — 语义定理数据库
- [Aletheia](https://arxiv.org/abs/2602.10177) — 生成–验证–修订架构
- [LATRACE](https://github.com/zxxz1000/LATRACE) — 长期记忆系统
- [Nanonets OCR](https://nanonets.com) — 公式感知的 PDF 提取
- [Harmonic Aristotle](https://aristotle.harmonic.fun) — Lean 4 形式化引擎
- [Research Math Assistant](https://github.com/ml1301215/research-math-assistant) — 社区资源

特别感谢数学 AI 研究社区推进自动推理。

---

## 引用

如果您在研究中使用 vibe_proving，请引用：

```bibtex
@software{vibe_proving2026,
  title = {vibe\_proving: AI-Powered Mathematical Research Assistant},
  author = {ML Research},
  year = {2026},
  url = {https://github.com/ml1301215/vibe-proving-math}
}
```

---

## 许可证

[MIT License](LICENSE)

---

## 联系方式

**仓库**：[github.com/ml1301215/vibe-proving-math](https://github.com/ml1301215/vibe-proving-math)  
**问题反馈**：[GitHub Issues](https://github.com/ml1301215/vibe-proving-math/issues)
