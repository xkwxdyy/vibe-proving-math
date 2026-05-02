![vibe_proving](assets/banner.svg)

<p align="center">
AI-powered mathematical research assistant for students and researchers
</p>

<p align="center">
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python"></a>
</p>

<p align="center">
<a href="README.zh.md">中文</a> | English
</p>

---

## Overview

**vibe_proving** is an integrated AI platform for mathematical research enthusiasts. It combines language models with theorem retrieval to provide interactive workflows for learning, problem-solving, proof review, and knowledge discovery.

### Core Capabilities

- **Learning Mode** — Generate structured explanations with prerequisites, proofs, examples, and extensions tailored to undergraduate or graduate level
- **Solving Mode** — Automated proof generation with citation verification, confidence scoring, and counterexample detection
- **Review Mode** — Structured analysis of mathematical writing (LaTeX/PDF/images) for logic gaps, citation accuracy, and symbol consistency
- **Search Mode** — Semantic search across 9M+ theorems from arXiv, Stacks Project, and other mathematical databases

### Demonstration

> **Note**: Video demonstrations will be available at `app/视频效果展示/` in a future update.

![Interface](assets/screenshot.png)

---

## Key Features

### 1. Interactive Learning

Transform any mathematical statement into a comprehensive learning resource:
- Background context and motivation
- Prerequisite knowledge with definitions
- Step-by-step proof walkthrough
- Concrete examples and counterexamples
- Extensions and related topics

**Target audience**: Students encountering unfamiliar theorems, researchers exploring new areas.

### 2. Intelligent Problem Solving

Generator–Verifier–Reviser pipeline with quality control:
- Direct retrieval: Check if problem already solved in theorem databases
- Proof generation: Create initial proof draft with reasoning steps
- Independent verification: Validate logic without generator bias
- Citation checking: Verify theorem references via [TheoremSearch](https://www.theoremsearch.com)
- Counterexample testing: Attempt to falsify claims before accepting
- Confidence scoring: Transparent assessment with explicit uncertainty

**Output format**: Structured proof with confidence score, verified citations, failed paths, and reasoning obstacles.

### 3. Proof Review

Automated analysis of mathematical writing:
- **Logic consistency**: Detect missing steps, circular reasoning, unjustified leaps
- **Citation accuracy**: Verify referenced theorems exist and are correctly stated
- **Symbol consistency**: Track variable scope, assumption dependencies

**Supported formats**: Text, LaTeX, images (via vision models), PDF (via OCR).

### 4. Theorem Discovery

Semantic search over mathematical literature:
- 9M+ theorems indexed from arXiv, Stacks Project, and specialized databases
- Natural language queries (no formula syntax required)
- Similarity scoring and ranking
- Direct links to original papers

---

## Installation

```bash
git clone https://github.com/ml1301215/vibe-proving-math.git
cd vibe-proving-math/app
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.toml config.toml
```

Edit `config.toml` and set at minimum:

```toml
[llm]
api_key = "your-api-key"
base_url = "https://api.deepseek.com/v1"  # or other OpenAI-compatible endpoint
model = "deepseek-chat"
```

**Recommended LLM Providers**:

| Provider | Strengths | Base URL | Get Key |
|----------|-----------|----------|---------|
| DeepSeek | Cost-effective reasoning | `https://api.deepseek.com/v1` | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| Gemini | Strong mathematical reasoning | `https://generativelanguage.googleapis.com/v1beta/openai` | [aistudio.google.com](https://aistudio.google.com/apikey) |
| OpenAI | General-purpose reliability | `https://api.openai.com/v1` | [platform.openai.com](https://platform.openai.com/api-keys) |

Start the server:

```bash
python -m uvicorn api.server:app --host 127.0.0.1 --port 8080
```

Access the web interface at `http://127.0.0.1:8080/ui/` or API documentation at `http://127.0.0.1:8080/docs`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Interface                        │
│         (Markdown + KaTeX + SSE Streaming)              │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   FastAPI Server        │
          │  /learn  /solve  /review│
          │  /search  /formalize    │
          └────────────┬────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
┌────▼────┐    ┌──────▼──────┐   ┌─────▼─────┐
│Learning │    │   Solving   │   │  Review   │
│Pipeline │    │   Pipeline  │   │  Pipeline │
└────┬────┘    └──────┬──────┘   └─────┬─────┘
     │                │                 │
     └────────────────┼─────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
┌────▼──────┐  ┌─────▼──────┐  ┌─────▼────┐
│ LLM Core  │  │  Theorem   │  │ Nanonets │
│ (OpenAI)  │  │  Search    │  │   OCR    │
└───────────┘  └────────────┘  └──────────┘
```

### Quality Control Mechanisms

1. **Citation Verification**: External database lookup prevents hallucinated references
2. **Independent Verification**: Proof steps validated without access to generator reasoning
3. **Counterexample Generation**: Active falsification attempts before claiming truth
4. **LaTeX Sanitization**: Automatic cleaning of control sequences for frontend rendering
5. **Confidence Reporting**: System refuses to answer when uncertain rather than fabricating

---

## API Reference

Complete documentation at `/docs`. Core endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/learn` | POST | Generate structured explanations |
| `/solve` | POST | Proof generation with verification |
| `/review_stream` | POST | Streaming proof review (text/images) |
| `/review_pdf_stream` | POST | PDF upload and structured analysis |
| `/search` | GET | Theorem semantic search |
| `/formalize` | POST | Natural language → Lean 4 (Beta) |

**Example** (Solving mode):

```bash
curl -X POST http://127.0.0.1:8080/solve \
  -H "Content-Type: application/json" \
  -d '{
    "statement": "Prove: For all primes p > 2, p ≡ 1 or 3 (mod 4)",
    "stream": false
  }'
```

Returns:

```json
{
  "verdict": "proved",
  "confidence": 0.89,
  "blueprint": "## Proof\n\nLet p be a prime > 2...",
  "references": [
    {
      "name": "Quadratic Residues Modulo Primes",
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

## Use Cases

### For Students

- **Concept exploration**: Input unfamiliar theorems to receive prerequisite breakdowns
- **Proof understanding**: Step-by-step walkthroughs with reasoning annotations
- **Exam preparation**: Generate practice problems and worked examples

### For Researchers

- **Literature review**: Semantic search across theorem databases
- **Proof drafting**: Generate initial proof sketches with citation suggestions
- **Manuscript review**: Automated consistency checking before submission

### For Educators

- **Teaching material**: Automatically generate explanations at multiple difficulty levels
- **Assignment checking**: Detect logic gaps in student submissions
- **Curriculum design**: Identify prerequisite chains for course planning

---

## Testing

```bash
cd app
pytest tests -m "not slow"  # Fast regression (no external API calls)
pytest tests                # Full suite (requires API keys)
```

Test coverage includes:
- Configuration parsing and validation
- LLM client integration (streaming and non-streaming)
- All five operational modes
- Citation verification pipeline
- LaTeX sanitization
- Error handling and edge cases

---

## Technical Stack

- **Backend**: FastAPI with Server-Sent Events for progressive streaming
- **Frontend**: Vanilla HTML/CSS/JS with KaTeX and Markdown rendering (no build toolchain)
- **LLM Integration**: OpenAI-compatible interface (model-agnostic)
- **Theorem Database**: [TheoremSearch](https://www.theoremsearch.com) API integration
- **PDF Processing**: [Nanonets OCR](https://nanonets.com) for formula-preserving extraction
- **Formal Verification** (Beta): [Harmonic Aristotle](https://aristotle.harmonic.fun) for Lean 4

---

## Contributing

We welcome contributions from the mathematical community:

- **Bug reports**: [GitHub Issues](https://github.com/ml1301215/vibe-proving-math/issues)
- **Feature requests**: Describe use cases and expected behavior
- **Code contributions**: Follow conventions in [CLAUDE.md](CLAUDE.md)
- **Documentation**: Improve examples, fix errors, translate content

**Development guidelines**:
- Python code follows PEP 8
- Frontend changes require cache-busting version updates
- LaTeX output must pass sanitization
- New endpoints require test coverage

---

## Acknowledgments

This project builds upon foundational work in mathematical AI and theorem proving:

- [TheoremSearch](https://www.theoremsearch.com) — Semantic theorem database
- [Aletheia](https://arxiv.org/abs/2602.10177) — Generator–Verifier–Reviser architecture
- [LATRACE](https://github.com/zxxz1000/LATRACE) — Long-term memory system
- [Nanonets OCR](https://nanonets.com) — Formula-aware PDF extraction
- [Harmonic Aristotle](https://aristotle.harmonic.fun) — Lean 4 formalization engine
- [Research Math Assistant](https://github.com/ml1301215/research-math-assistant) — Community resources

Special thanks to the mathematical AI research community for advancing automated reasoning.

---

## Citation

If you use vibe_proving in your research, please cite:

```bibtex
@software{vibe_proving2026,
  title = {vibe\_proving: AI-Powered Mathematical Research Assistant},
  author = {ML Research},
  year = {2026},
  url = {https://github.com/ml1301215/vibe-proving-math}
}
```

---

## License

[MIT License](LICENSE)

---

## Contact

**Repository**: [github.com/ml1301215/vibe-proving-math](https://github.com/ml1301215/vibe-proving-math)  
**Issues**: [GitHub Issues](https://github.com/ml1301215/vibe-proving-math/issues)
