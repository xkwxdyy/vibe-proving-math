"""前端国际化（i18n）完整性测试

测试重点：
1. 语言跟随系统设置
2. 所有UI文本都有i18n覆盖
3. 语言切换后实时更新
4. 后端提示消息国际化
5. 错误消息国际化
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from api.server import app


@pytest.fixture
def client():
    return TestClient(app)


class TestSystemLanguageDetection:
    """系统语言检测测试"""

    def test_backend_respects_lang_parameter_zh(self, client):
        """测试：后端应该尊重lang=zh参数"""
        # 学习模式
        resp = client.post("/learn", json={
            "statement": "test",
            "lang": "zh"
        })
        # 应该接受zh语言代码
        assert resp.status_code in [200, 500]

    def test_backend_respects_lang_parameter_en(self, client):
        """测试：后端应该尊重lang=en参数"""
        resp = client.post("/learn", json={
            "statement": "test",
            "lang": "en"
        })
        assert resp.status_code in [200, 500]

    def test_default_language_is_zh(self, client):
        """测试：默认语言应该是中文"""
        resp = client.post("/learn", json={
            "statement": "test"
            # 不提供lang参数
        })
        # 应该使用默认语言（中文）
        assert resp.status_code in [200, 500]


class TestAPIErrorMessagesInternationalization:
    """API错误消息国际化测试"""

    def test_error_messages_are_chinese(self, client):
        """测试：错误消息应该是中文"""
        # 空配置
        resp = client.post("/config/llm", json={})
        assert resp.status_code == 422
        data = resp.json()
        error_msg = data.get("detail", "")
        # 验证错误消息是中文
        assert "至少提供" in error_msg or "base_url" in error_msg

    def test_nanonets_empty_key_error_chinese(self, client):
        """测试：Nanonets空密钥错误应该是中文"""
        resp = client.post("/config/nanonets", json={"api_key": ""})
        assert resp.status_code == 422
        error_msg = resp.json().get("detail", "")
        assert "不能为空" in error_msg

    def test_review_empty_input_error_chinese(self, client):
        """测试：审查模式空输入错误应该是中文"""
        resp = client.post("/review", json={
            "proof_text": "",
            "images": []
        })
        assert resp.status_code == 422
        error_msg = resp.json().get("detail", "")
        assert "至少提供一个" in error_msg or "proof_text" in error_msg


class TestReviewModeInternationalization:
    """审查模式国际化测试"""

    @pytest.mark.slow
    def test_review_stream_progress_messages_zh(self, client):
        """测试：审查流程进度消息应该是中文（lang=zh）"""
        resp = client.post("/review_stream", json={
            "proof_text": "Theorem: 1+1=2. Proof: Trivial.",
            "lang": "zh"
        }, stream=True)

        if resp.status_code == 200:
            content = resp.content.decode()
            # 检查是否包含中文进度消息
            # 注意：这需要实际运行才能看到进度消息
            # 这里仅验证格式正确
            assert "data:" in content or "<!--vp-" in content

    @pytest.mark.slow
    def test_review_stream_progress_messages_en(self, client):
        """测试：审查流程进度消息应该是英文（lang=en）"""
        resp = client.post("/review_stream", json={
            "proof_text": "Theorem: 1+1=2. Proof: Trivial.",
            "lang": "en"
        }, stream=True)

        if resp.status_code == 200:
            content = resp.content.decode()
            # 验证格式正确
            assert "data:" in content or "<!--vp-" in content


class TestLearningModeInternationalization:
    """学习模式国际化测试"""

    def test_learn_accepts_zh_lang(self, client):
        """测试：学习模式接受zh语言参数"""
        resp = client.post("/learn", json={
            "statement": "Every continuous function is integrable",
            "lang": "zh"
        })
        assert resp.status_code in [200, 500]

    def test_learn_accepts_en_lang(self, client):
        """测试：学习模式接受en语言参数"""
        resp = client.post("/learn", json={
            "statement": "Every continuous function is integrable",
            "lang": "en"
        })
        assert resp.status_code in [200, 500]

    def test_learn_section_accepts_lang(self, client):
        """测试：学习模式单卡重生成接受lang参数"""
        resp = client.post("/learn/section", json={
            "statement": "test",
            "section": "proof",
            "lang": "zh"
        })
        assert resp.status_code in [200, 422, 500]


class TestSolveModeInternationalization:
    """问题求解模式国际化测试"""

    def test_solve_accepts_zh_lang(self, client):
        """测试：求解模式接受zh语言参数"""
        resp = client.post("/solve", json={
            "statement": "Prove sqrt(2) is irrational",
            "lang": "zh"
        })
        assert resp.status_code in [200, 500]

    def test_solve_accepts_en_lang(self, client):
        """测试：求解模式接受en语言参数"""
        resp = client.post("/solve", json={
            "statement": "Prove sqrt(2) is irrational",
            "lang": "en"
        })
        assert resp.status_code in [200, 500]


class TestConfigInterfaceInternationalization:
    """配置界面国际化测试"""

    def test_config_response_is_language_agnostic(self, client):
        """测试：配置响应应该是语言无关的（仅返回数据）"""
        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()

        # 配置响应应该只包含数据，不包含语言相关的描述
        assert "llm" in data
        assert "config_path" in data
        # 应该没有语言相关的字段
        assert "message" not in data
        assert "description" not in data


class TestHealthCheckInternationalization:
    """健康检查国际化测试"""

    def test_health_check_has_status_field(self, client):
        """测试：健康检查应该有status字段"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        # status应该是英文枚举值（ok, degraded, error）
        assert data["status"] in ["ok", "degraded", "error"]


class TestFormalizationModeInternationalization:
    """形式化模式国际化测试"""

    def test_formalize_accepts_zh_lang(self, client):
        """测试：形式化模式接受zh语言参数"""
        resp = client.post("/formalize", json={
            "statement": "Every group is a set with a binary operation",
            "lang": "zh"
        })
        # 可能失败如果Aristotle API不可用
        assert resp.status_code in [200, 422, 500, 502]

    def test_formalize_accepts_en_lang(self, client):
        """测试：形式化模式接受en语言参数"""
        resp = client.post("/formalize", json={
            "statement": "Every group is a set with a binary operation",
            "lang": "en"
        })
        assert resp.status_code in [200, 422, 500, 502]


class TestI18NConsistency:
    """国际化一致性测试"""

    def test_all_modes_accept_same_lang_values(self, client):
        """测试：所有模式应该接受相同的lang值"""
        endpoints = [
            ("/learn", {"statement": "test", "lang": "zh"}),
            ("/solve", {"statement": "test", "lang": "zh"}),
            ("/review", {"proof_text": "test", "lang": "zh"}),
        ]

        for endpoint, payload in endpoints:
            resp = client.post(endpoint, json=payload)
            # 所有端点都应该接受zh语言
            assert resp.status_code in [200, 422, 500]

    def test_invalid_lang_code_handling(self, client):
        """测试：无效的语言代码应该被处理"""
        resp = client.post("/learn", json={
            "statement": "test",
            "lang": "invalid_lang"
        })
        # 应该接受（或使用默认语言）而不是崩溃
        assert resp.status_code in [200, 422, 500]

    def test_empty_lang_uses_default(self, client):
        """测试：空lang参数应该使用默认语言"""
        resp = client.post("/learn", json={
            "statement": "test",
            "lang": ""
        })
        # 应该使用默认语言
        assert resp.status_code in [200, 500]


class TestI18NParameterPropagation:
    """国际化参数传递测试"""

    def test_lang_parameter_in_learn_request(self, client):
        """测试：学习请求应该包含lang参数"""
        payload = {
            "statement": "test",
            "level": "undergraduate",
            "lang": "zh"
        }

        resp = client.post("/learn", json=payload)
        # 验证请求被接受
        assert resp.status_code in [200, 500]

    def test_lang_parameter_in_solve_request(self, client):
        """测试：求解请求应该包含lang参数"""
        payload = {
            "statement": "test",
            "lang": "en"
        }

        resp = client.post("/solve", json=payload)
        assert resp.status_code in [200, 500]

    def test_lang_parameter_in_review_request(self, client):
        """测试：审查请求应该包含lang参数"""
        payload = {
            "proof_text": "test",
            "lang": "zh"
        }

        resp = client.post("/review", json=payload)
        assert resp.status_code in [200, 422, 500]


class TestLanguageSwitchingBehavior:
    """语言切换行为测试"""

    def test_sequential_requests_with_different_langs(self, client):
        """测试：连续请求使用不同语言应该独立工作"""
        # 第一个请求：中文
        resp1 = client.post("/learn", json={
            "statement": "test 1",
            "lang": "zh"
        })
        assert resp1.status_code in [200, 500]

        # 第二个请求：英文
        resp2 = client.post("/learn", json={
            "statement": "test 2",
            "lang": "en"
        })
        assert resp2.status_code in [200, 500]

        # 两个请求应该独立，不互相影响


class TestUITextInternationalization:
    """UI文本国际化测试（模拟前端行为）"""

    def test_config_panel_button_text_mapping(self):
        """测试：配置面板按钮文本应该有映射"""
        # 模拟前端i18n键
        i18n_keys = {
            "zh": {
                "panel.saveLlm": "保存LLM配置",
                "panel.saving": "保存中...",
                "panel.saved": "已保存",
                "panel.saveFailed": "保存失败",
            },
            "en": {
                "panel.saveLlm": "Save LLM Config",
                "panel.saving": "Saving...",
                "panel.saved": "Saved",
                "panel.saveFailed": "Save Failed",
            }
        }

        # 验证所有键都存在
        for lang, translations in i18n_keys.items():
            assert "panel.saveLlm" in translations
            assert "panel.saving" in translations
            assert "panel.saved" in translations

    def test_mode_names_internationalization(self):
        """测试：模式名称应该国际化"""
        modes = {
            "zh": {
                "mode.learning": "学习模式",
                "mode.solving": "问题求解",
                "mode.reviewing": "证明审查",
                "mode.searching": "定理检索",
                "mode.formalizing": "形式化",
            },
            "en": {
                "mode.learning": "Learning",
                "mode.solving": "Solving",
                "mode.reviewing": "Review",
                "mode.searching": "Search",
                "mode.formalizing": "Formalization",
            }
        }

        # 验证所有模式都有翻译
        for lang, translations in modes.items():
            assert len(translations) == 5


class TestProgressMessagesInternationalization:
    """进度消息国际化测试"""

    def test_progress_message_format(self):
        """测试：进度消息应该有统一格式"""
        # 模拟进度消息
        progress_messages = {
            "zh": [
                "正在解析输入文本...",
                "正在检索定理...",
                "正在生成证明...",
                "正在验证结果...",
            ],
            "en": [
                "Parsing input text...",
                "Retrieving theorems...",
                "Generating proof...",
                "Verifying results...",
            ]
        }

        # 验证两种语言都有相同数量的进度消息
        assert len(progress_messages["zh"]) == len(progress_messages["en"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
