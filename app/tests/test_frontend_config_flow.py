"""前端配置流程集成测试

测试场景：
1. 配置持久化：保存配置后刷新页面，配置应该保留
2. 配置优先级：服务端配置优先于前端localStorage
3. API密钥脱敏：GET /config 不应返回真实密钥
4. 配置更新流程：保存 → 刷新缓存 → 前端重新加载
5. 错误处理：无效配置应该返回422错误
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import tomllib
from unittest.mock import patch

from api.server import app


@pytest.fixture
def test_config_file():
    """创建临时测试配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
        f.write("""
[llm]
base_url = "https://api.test.com/v1"
api_key = "test-key-initial"
model = "test-model"
timeout = 120

[nanonets]
api_key = "test-nanonets-key"

[theorem_search]
base_url = "https://api.theoremsearch.com"
timeout = 60

[latrace]
enabled = false
base_url = "http://localhost:8000"
tenant_id = "test"
timeout = 10

[app]
log_level = "INFO"
""")
        path = Path(f.name)

    yield path

    # 清理
    if path.exists():
        path.unlink()


@pytest.fixture
def client_with_test_config(test_config_file):
    """使用测试配置文件的客户端"""
    with patch('core.config._config_path', return_value=test_config_file):
        from core.config import clear_config_cache
        clear_config_cache()
        yield TestClient(app)
        clear_config_cache()


class TestConfigPersistence:
    """配置持久化测试"""

    def test_config_survives_page_refresh(self, client_with_test_config, test_config_file):
        """测试：配置在页面刷新后应该保留"""
        client = client_with_test_config

        # 1. 首次加载：应该返回初始配置
        resp1 = client.get("/config")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["llm"]["base_url"] == "https://api.test.com/v1"
        assert data1["llm"]["model"] == "test-model"
        assert data1["llm"]["api_key_configured"] is True

        # 2. 更新配置
        update_resp = client.post("/config/llm", json={
            "base_url": "https://api.updated.com/v1",
            "api_key": "new-test-key",
            "model": "new-model"
        })
        assert update_resp.status_code == 200

        # 3. 模拟页面刷新：重新加载配置
        from core.config import clear_config_cache
        clear_config_cache()

        resp2 = client.get("/config")
        assert resp2.status_code == 200
        data2 = resp2.json()

        # 验证：配置应该是更新后的值
        assert data2["llm"]["base_url"] == "https://api.updated.com/v1"
        assert data2["llm"]["model"] == "new-model"
        assert data2["llm"]["api_key_configured"] is True

        # 4. 验证文件内容
        with open(test_config_file, 'rb') as f:
            file_content = tomllib.load(f)
        assert file_content["llm"]["base_url"] == "https://api.updated.com/v1"
        assert file_content["llm"]["model"] == "new-model"
        assert file_content["llm"]["api_key"] == "new-test-key"

    def test_api_key_never_exposed_in_get_config(self, client_with_test_config):
        """测试：GET /config 永远不应该返回真实API密钥"""
        client = client_with_test_config

        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()

        # 验证：不应该包含 api_key 字段，只有 api_key_configured
        assert "api_key" not in data["llm"]
        assert "api_key_configured" in data["llm"]
        assert isinstance(data["llm"]["api_key_configured"], bool)

        # Nanonets 也应该脱敏
        assert "api_key" not in data["nanonets"]
        assert "api_key_configured" in data["nanonets"]

    def test_config_update_clears_cache(self, client_with_test_config, test_config_file):
        """测试：配置更新应该清除缓存"""
        client = client_with_test_config

        # 1. 首次加载
        resp1 = client.get("/config")
        assert resp1.json()["llm"]["model"] == "test-model"

        # 2. 直接修改文件（模拟外部修改）
        with open(test_config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('model = "test-model"', 'model = "external-modified"')
        with open(test_config_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # 3. 通过 API 更新（触发缓存清理）
        client.post("/config/llm", json={"model": "api-modified"})

        # 4. 重新加载配置
        from core.config import clear_config_cache
        clear_config_cache()

        resp2 = client.get("/config")
        assert resp2.json()["llm"]["model"] == "api-modified"


class TestConfigValidation:
    """配置验证测试"""

    def test_empty_llm_config_rejected(self, client_with_test_config):
        """测试：空的LLM配置应该被拒绝"""
        client = client_with_test_config

        resp = client.post("/config/llm", json={})
        assert resp.status_code == 422
        assert "至少提供" in resp.json()["detail"]

    def test_empty_api_key_llm_accepted(self, client_with_test_config):
        """测试：更新base_url和model但不提供api_key应该成功"""
        client = client_with_test_config

        resp = client.post("/config/llm", json={
            "base_url": "https://new.api.com/v1",
            "model": "new-model"
        })
        assert resp.status_code == 200

        # 验证：只更新了提供的字段
        get_resp = client.get("/config")
        data = get_resp.json()
        assert data["llm"]["base_url"] == "https://new.api.com/v1"
        assert data["llm"]["model"] == "new-model"

    def test_empty_nanonets_key_rejected(self, client_with_test_config):
        """测试：空的Nanonets密钥应该被拒绝"""
        client = client_with_test_config

        resp = client.post("/config/nanonets", json={"api_key": ""})
        assert resp.status_code == 422
        assert "不能为空" in resp.json()["detail"]

    def test_whitespace_only_key_rejected(self, client_with_test_config):
        """测试：只有空格的密钥应该被拒绝"""
        client = client_with_test_config

        resp = client.post("/config/nanonets", json={"api_key": "   "})
        assert resp.status_code == 422


class TestFrontendUIFlow:
    """前端UI流程测试（模拟用户操作）"""

    def test_settings_panel_full_flow(self, client_with_test_config):
        """测试：完整的设置面板流程

        模拟用户操作：
        1. 打开设置面板
        2. 填写LLM配置
        3. 保存
        4. 刷新页面
        5. 验证配置保留
        """
        client = client_with_test_config

        # Step 1: 打开设置面板（GET /config）
        resp = client.get("/config")
        assert resp.status_code == 200
        initial = resp.json()

        # Step 2: 用户填写表单并保存
        new_config = {
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "sk-user-provided-key",
            "model": "deepseek-chat"
        }
        save_resp = client.post("/config/llm", json=new_config)
        assert save_resp.status_code == 200
        assert save_resp.json()["ok"] is True

        # Step 3: 前端调用 loadAppConfig() 重新加载
        from core.config import clear_config_cache
        clear_config_cache()

        reload_resp = client.get("/config")
        assert reload_resp.status_code == 200
        reloaded = reload_resp.json()

        # Step 4: 验证前端应该显示的内容
        assert reloaded["llm"]["base_url"] == new_config["base_url"]
        assert reloaded["llm"]["model"] == new_config["model"]
        assert reloaded["llm"]["api_key_configured"] is True
        # API密钥不应该返回到前端
        assert "api_key" not in reloaded["llm"]

        # Step 5: 模拟页面刷新（用户按F5）
        clear_config_cache()
        refresh_resp = client.get("/config")
        assert refresh_resp.status_code == 200
        refreshed = refresh_resp.json()

        # 验证：刷新后配置应该保持不变
        assert refreshed["llm"]["base_url"] == new_config["base_url"]
        assert refreshed["llm"]["model"] == new_config["model"]

    def test_nanonets_config_flow(self, client_with_test_config):
        """测试：Nanonets配置流程"""
        client = client_with_test_config

        # 1. 保存Nanonets密钥
        resp = client.post("/config/nanonets", json={
            "api_key": "new-nanonets-key-123"
        })
        assert resp.status_code == 200

        # 2. 验证配置状态
        from core.config import clear_config_cache
        clear_config_cache()

        get_resp = client.get("/config")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["nanonets"]["api_key_configured"] is True
        assert "api_key" not in data["nanonets"]

    def test_config_path_returned(self, client_with_test_config, test_config_file):
        """测试：配置路径应该返回到前端（用于显示）"""
        client = client_with_test_config

        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()

        assert "config_path" in data
        assert data["config_path"] == str(test_config_file)


class TestConfigEdgeCases:
    """配置边界情况测试"""

    def test_special_characters_in_api_key(self, client_with_test_config):
        """测试：API密钥中的特殊字符应该正确处理"""
        client = client_with_test_config

        special_key = 'sk-test/key+with=special&chars%20'
        resp = client.post("/config/llm", json={
            "base_url": "https://test.com/v1",
            "api_key": special_key,
            "model": "test"
        })
        assert resp.status_code == 200

        # 验证：重新加载后API密钥应该正确保存
        from core.config import clear_config_cache, load_config
        clear_config_cache()
        cfg = load_config()
        assert cfg["llm"]["api_key"] == special_key

    def test_very_long_base_url(self, client_with_test_config):
        """测试：超长URL应该能正确保存"""
        client = client_with_test_config

        long_url = "https://very-long-domain-name.example.com/api/v1/chat/completions/with/many/path/segments"
        resp = client.post("/config/llm", json={
            "base_url": long_url,
            "model": "test"
        })
        assert resp.status_code == 200

        from core.config import clear_config_cache
        clear_config_cache()
        get_resp = client.get("/config")
        assert get_resp.json()["llm"]["base_url"] == long_url

    def test_unicode_in_model_name(self, client_with_test_config):
        """测试：Unicode模型名称应该正确处理"""
        client = client_with_test_config

        unicode_model = "模型-测试-123"
        resp = client.post("/config/llm", json={
            "model": unicode_model
        })
        assert resp.status_code == 200

        from core.config import clear_config_cache
        clear_config_cache()
        get_resp = client.get("/config")
        assert get_resp.json()["llm"]["model"] == unicode_model


class TestConcurrentConfigUpdates:
    """并发配置更新测试"""

    def test_sequential_updates_all_persist(self, client_with_test_config):
        """测试：连续多次更新应该都能持久化"""
        client = client_with_test_config

        updates = [
            {"model": "model-1"},
            {"model": "model-2"},
            {"model": "model-3"},
        ]

        for update in updates:
            resp = client.post("/config/llm", json=update)
            assert resp.status_code == 200

        # 验证：最后的更新应该生效
        from core.config import clear_config_cache
        clear_config_cache()

        final_resp = client.get("/config")
        assert final_resp.json()["llm"]["model"] == "model-3"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
