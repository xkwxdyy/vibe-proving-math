# Contributing to vibe_proving

感谢你愿意参与本项目。以下为协作约定；开发与运行说明见 [README.md](README.md)。

## 环境

- Python **3.11+**
- 从 `app/config.example.toml` 复制出本地 `app/config.toml` 并填入你自己的 API 配置（**勿将含真实密钥的 `config.toml` 提交到 Git**）。

安装与启动见 [README.md](README.md) / [README.zh.md](README.zh.md)。

## 提 Issue

- 尽量说明：操作系统、Python 版本、复现步骤、期望行为与实际行为。
- 若涉及前端，注明浏览器与访问路径（例如 `/ui/`）。

## 提 Pull Request

1. 从最新 `main`（或默认分支）创建功能分支。
2. 改动保持聚焦，避免无关大重构。
3. 提交前请在本地启动服务并手动验证你改动涉及的路径（本仓库不维护自动化测试套件）。

4. PR 描述中说明**动机**与**主要变更**；若改动了用户可见行为，请一并更新 README 相关段落。

## 代码风格

- 与现有代码保持一致（导入顺序、命名、错误处理方式）。
- 不要提交调试用的临时脚本、截图或含密钥的配置。

## 许可证

向本仓库提交代码即表示你同意在 **[MIT License](LICENSE)** 下授权你的贡献。
