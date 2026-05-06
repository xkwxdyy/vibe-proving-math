# vibe_proving 架构图 (Mermaid版本)

## 整体系统架构

```mermaid
graph TB
    User[用户浏览器]
    
    subgraph Frontend["前端 (SPA)"]
        HTML[index.html<br/>主页+聊天视图]
        JS[app.js<br/>6500行核心逻辑]
        CSS[style.css<br/>主题+响应式]
        KaTeX[KaTeX CDN<br/>数学公式]
        Marked[marked.js<br/>Markdown]
    end
    
    subgraph Backend["后端 FastAPI"]
        Server[api/server.py<br/>Uvicorn服务器]
        
        subgraph Modes["模式处理器"]
            Learning[learning/pipeline.py<br/>结构化教学]
            Solving[solving/<br/>解题过程]
            Research[research/reviewer.py<br/>文献检索]
            Reviewing[reviewing/<br/>论文审阅]
        end
        
        subgraph Core["核心模块"]
            Config[config.py<br/>配置管理]
            LLM[llm.py<br/>LLM客户端]
            Text[text_sanitize.py<br/>文本清理]
            Theorem[theorem_search.py<br/>定理搜索]
        end
        
        subgraph Skills["技能模块"]
            Prereq[prerequisite_map.py]
            Proof[proof/]
            Verify[verification/]
        end
    end
    
    subgraph Storage["配置存储"]
        ConfigFile[config.toml<br/>LLM配置持久化]
        Memory[memory.json<br/>会话历史]
    end
    
    subgraph External["外部API"]
        DeepSeek[DeepSeek API<br/>v4 Pro]
        Gemini[Gemini API<br/>3.1 Pro]
        TheoremAPI[Theorem Search]
        Nanonets[Nanonets OCR]
        Aristotle[Aristotle平台<br/>Lean4验证]
    end
    
    User -->|HTTP/HTTPS| HTML
    HTML --> JS
    HTML --> CSS
    JS --> KaTeX
    JS --> Marked
    JS -->|REST + SSE| Server
    
    Server --> Learning
    Server --> Solving
    Server --> Research
    Server --> Reviewing
    
    Server --> Config
    Server --> LLM
    Server --> Text
    Server --> Theorem
    
    Learning --> Skills
    Solving --> Skills
    
    Config -->|读写| ConfigFile
    Server -->|存储| Memory
    
    LLM -->|API调用| DeepSeek
    LLM -->|API调用| Gemini
    Theorem -->|查询| TheoremAPI
    Reviewing -->|OCR| Nanonets
    JS -->|外部跳转| Aristotle
    
    style Frontend fill:#e3f2fd
    style Backend fill:#fff3e0
    style Storage fill:#f3e5f5
    style External fill:#e8f5e9
```

## 6大功能模式流程

```mermaid
graph LR
    subgraph "6大核心模式"
        L[ℓ Learning<br/>分步教学]
        S[σ Solving<br/>解题过程]
        R[¶ Research<br/>文献检索]
        V[✓ Reviewing<br/>论文审阅]
        SE[∇ Search<br/>知识检索]
        F[⊢ Formalization<br/>外部验证]
    end
    
    L -->|结构化输出| Out1[Background<br/>Prerequisites<br/>Proof<br/>Examples]
    S -->|解题步骤| Out2[分析<br/>求解<br/>验证]
    R -->|检索结果| Out3[相关工作<br/>引用管理]
    V -->|审阅结果| Out4[批注<br/>建议]
    SE -->|搜索结果| Out5[定理<br/>概念]
    F -->|跳转| Out6[Aristotle平台]
    
    style L fill:#bbdefb
    style S fill:#c5e1a5
    style R fill:#ffccbc
    style V fill:#f8bbd0
    style SE fill:#ffe0b2
    style F fill:#d1c4e9
```

## 数据流与通信协议

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端JS
    participant B as 后端FastAPI
    participant L as LLM API
    participant C as config.toml
    
    Note over U,C: 场景1: API配置
    U->>F: 填写API配置
    F->>B: POST /config/llm
    B->>C: 写入配置
    B-->>F: 200 OK
    F-->>U: 显示"配置已保存"
    
    Note over U,C: 场景2: Learning模式查询
    U->>F: 输入"勾股定理"
    F->>B: POST /learn (SSE)
    B->>L: 调用LLM API
    
    loop 流式响应
        L-->>B: 返回部分内容
        B-->>F: SSE: <!--vp-result:...-->
        F-->>U: 实时渲染
    end
    
    L-->>B: 完整响应
    B-->>F: SSE: <!--vp-final:...-->
    F-->>U: 最终渲染 + LaTeX
    
    Note over U,C: 场景3: 刷新验证
    U->>F: 刷新页面
    F->>B: GET /health
    B->>C: 读取配置
    C-->>B: 返回配置
    B-->>F: JSON: {llm: {...}}
    F-->>U: 显示已保存配置
```

## 前端状态管理

```mermaid
stateDiagram-v2
    [*] --> Home: 页面加载
    
    Home --> Chat_Learning: 点击Learning卡片
    Home --> Chat_Solving: 点击Solving卡片
    Home --> Chat_Research: 点击Research卡片
    Home --> Chat_Reviewing: 点击Reviewing卡片
    Home --> Chat_Search: 点击Search卡片
    Home --> External: 点击Formalization
    
    Chat_Learning --> Generating: 提交查询
    Chat_Solving --> Generating: 提交查询
    Chat_Research --> Generating: 提交查询
    Chat_Reviewing --> Generating: 提交查询
    
    Generating --> Chat_Learning: 生成完成
    Generating --> Chat_Solving: 生成完成
    Generating --> Chat_Research: 生成完成
    Generating --> Chat_Reviewing: 生成完成
    Generating --> Generating: 可点击Stop中断
    
    Chat_Learning --> Home: 返回主页
    Chat_Solving --> Home: 返回主页
    Chat_Research --> Home: 返回主页
    Chat_Reviewing --> Home: 返回主页
    
    External --> [*]: 新窗口打开
    
    note right of Home
        AppState.view = 'home'
        AppState.mode = null
    end note
    
    note right of Chat_Learning
        AppState.view = 'chat'
        AppState.mode = 'learning'
    end note
    
    note right of Generating
        AppState.generating = true
        Send按钮disabled
        Stop按钮visible
    end note
```
## 技术栈一览

```mermaid
mindmap
    root((vibe_proving))
        前端
            HTML5
            CSS3
                响应式布局
                主题切换
                动画效果
            JavaScript ES6+
                状态管理 AppState
                SSE客户端
                事件处理
            CDN依赖
                KaTeX 数学渲染
                marked.js Markdown
        后端
            Python 3.11+
            FastAPI
                异步处理
                SSE支持
                自动文档
            Uvicorn
                ASGI服务器
            核心库
                TOML配置
                HTTP客户端
        外部服务
            LLM API
                DeepSeek v4 Pro
                Gemini 3.1 Pro
                自定义端点
            Theorem Search
            Nanonets OCR
            Aristotle Lean4
        开发工具
            部署
                Docker可选
                Nginx反向代理
```
