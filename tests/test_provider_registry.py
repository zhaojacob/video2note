"""
Tests for Provider Registry

Tests the Provider-First LLM architecture including:
- ProviderRegistry initialization
- Provider capability filtering
- Finding providers that offer specific models
- Custom provider registration
- Backward compatibility
"""
import os
import pytest
from utils.llm.provider_registry import (
    ProviderRegistry,
    ProviderInfo,
    ProviderCapability,
    BUILTIN_PROVIDERS
)


class TestProviderRegistry:
    """Test ProviderRegistry functionality"""

    def test_initialization(self):
        """Test that ProviderRegistry initializes with all built-in providers"""
        registry = ProviderRegistry()
        providers = registry.get_all_providers()

        # Check that all built-in providers are present
        assert "zhipu" in providers
        assert "openai" in providers
        assert "deepseek" in providers
        assert "modelscope" in providers
        assert "bytedance" in providers

    def test_get_provider(self):
        """Test getting a specific provider"""
        registry = ProviderRegistry()

        zhipu = registry.get_provider("zhipu")
        assert zhipu is not None
        assert zhipu.id == "zhipu"
        assert zhipu.name == "智谱AI (GLM)"
        assert zhipu.base_url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        assert zhipu.api_key_env == "GLM_API_KEY"
        assert "glm-4-flash" in zhipu.models
        assert ProviderCapability.TEXT in zhipu.capabilities

    def test_get_nonexistent_provider(self):
        """Test getting a provider that doesn't exist"""
        registry = ProviderRegistry()
        provider = registry.get_provider("nonexistent")
        assert provider is None

    def test_list_providers_no_filter(self):
        """Test listing all providers without filtering"""
        registry = ProviderRegistry()
        providers = registry.list_providers()

        assert len(providers) >= 5  # At least 5 built-in providers
        assert "zhipu" in providers
        assert "deepseek" in providers

    def test_list_providers_by_capability_vision(self):
        """Test filtering providers by vision capability"""
        registry = ProviderRegistry()
        vision_providers = registry.list_providers(capability=ProviderCapability.VISION)

        # Zhipu, OpenAI, and Bytedance support vision
        assert "zhipu" in vision_providers
        assert "openai" in vision_providers
        assert "bytedance" in vision_providers

    def test_list_providers_by_capability_thinking(self):
        """Test filtering providers by thinking capability"""
        registry = ProviderRegistry()
        thinking_providers = registry.list_providers(capability=ProviderCapability.THINKING)

        # Zhipu and ModelScope support thinking
        assert "zhipu" in thinking_providers
        assert "modelscope" in thinking_providers

    def test_list_providers_by_capability_fast(self):
        """Test filtering providers by fast capability"""
        registry = ProviderRegistry()
        fast_providers = registry.list_providers(capability=ProviderCapability.FAST)

        # Zhipu, DeepSeek, and OpenAI support fast
        assert "zhipu" in fast_providers
        assert "deepseek" in fast_providers
        assert "openai" in fast_providers

    def test_get_providers_for_model(self):
        """Test finding providers that offer a specific model"""
        registry = ProviderRegistry()

        # Test GLM-4-flash (offered by zhipu)
        glm_flash_providers = registry.get_providers_for_model("glm-4-flash")
        assert len(glm_flash_providers) >= 1
        assert any(p.id == "zhipu" for p in glm_flash_providers)

    def test_get_providers_for_nonexistent_model(self):
        """Test finding providers for a model that doesn't exist"""
        registry = ProviderRegistry()
        providers = registry.get_providers_for_model("nonexistent-model")
        assert len(providers) == 0

    def test_register_custom_provider(self):
        """Test dynamically registering a custom provider"""
        registry = ProviderRegistry()

        # Create a custom provider
        custom_provider = ProviderInfo(
            id="test-custom",
            name="Test Custom Provider",
            base_url="https://test.example.com/v1",
            api_key_env="TEST_API_KEY",
            models=["test-model-1", "test-model-2"],
            capabilities=[ProviderCapability.TEXT],
            timeout=30,
            default_max_tokens=2048
        )

        # Register it
        registry.register_custom_provider(custom_provider)

        # Verify it's registered
        retrieved = registry.get_provider("test-custom")
        assert retrieved is not None
        assert retrieved.id == "test-custom"
        assert retrieved.name == "Test Custom Provider"
        assert "test-model-1" in retrieved.models


class TestProviderInfo:
    """Test ProviderInfo dataclass"""

    def test_get_api_key(self):
        """Test getting API key from environment"""
        provider = ProviderInfo(
            id="test",
            name="Test",
            base_url="https://test.com",
            api_key_env="GLM_API_KEY",  # Use existing env var
            models=["test-model"],
            capabilities=[ProviderCapability.TEXT]
        )

        # This will return the value from environment or None
        api_key = provider.get_api_key()
        # We can't assert the value since we don't know if it's set
        # Just verify the method works
        assert isinstance(api_key, (str, type(None)))

    def test_has_model(self):
        """Test checking if provider supports a model"""
        provider = ProviderInfo(
            id="test",
            name="Test",
            base_url="https://test.com",
            api_key_env="TEST_KEY",
            models=["model-1", "model-2", "model-3"],
            capabilities=[ProviderCapability.TEXT]
        )

        assert provider.has_model("model-1") is True
        assert provider.has_model("model-2") is True
        assert provider.has_model("nonexistent") is False

    def test_supports_capability(self):
        """Test checking if provider supports a capability"""
        provider = ProviderInfo(
            id="test",
            name="Test",
            base_url="https://test.com",
            api_key_env="TEST_KEY",
            models=["model-1"],
            capabilities=[ProviderCapability.TEXT, ProviderCapability.FAST]
        )

        assert provider.supports_capability(ProviderCapability.TEXT) is True
        assert provider.supports_capability(ProviderCapability.FAST) is True
        assert provider.supports_capability(ProviderCapability.VISION) is False


class TestBackwardCompatibility:
    """Test backward compatibility with legacy code"""

    def test_builtin_models_provider_id(self):
        """Test that BUILTIN_MODELS use provider_id"""
        from utils.llm.model_registry import BUILTIN_MODELS

        # Check that models have provider_id field
        glm_flash = BUILTIN_MODELS.get("glm-4-flash")
        assert glm_flash is not None
        assert hasattr(glm_flash, 'provider_id')
        assert glm_flash.provider_id == "zhipu"

    def test_model_info_legacy_properties(self):
        """Test that ModelInfo legacy properties work"""
        from utils.llm.model_registry import BUILTIN_MODELS

        glm_flash = BUILTIN_MODELS.get("glm-4-flash")
        assert glm_flash is not None

        # Test legacy provider property
        assert glm_flash.provider == "zhipu"

        # Test legacy env_key property
        env_key = glm_flash.env_key
        assert env_key == "GLM_API_KEY"

        # Test legacy api_base property
        api_base = glm_flash.api_base
        assert "open.bigmodel.cn" in api_base


class TestBuiltinProviders:
    """Test built-in provider configurations"""

    def test_zhipu_provider(self):
        """Test Zhipu provider configuration"""
        zhipu = BUILTIN_PROVIDERS.get("zhipu")
        assert zhipu is not None
        assert zhipu.id == "zhipu"
        assert "glm-4-flash" in zhipu.models
        assert "glm-4.6v" in zhipu.models
        assert ProviderCapability.VISION in zhipu.capabilities
        assert ProviderCapability.THINKING in zhipu.capabilities

    def test_openai_provider(self):
        """Test OpenAI provider configuration"""
        openai = BUILTIN_PROVIDERS.get("openai")
        assert openai is not None
        assert openai.id == "openai"
        assert "gpt-4o" in openai.models
        assert "gpt-4o-mini" in openai.models
        assert ProviderCapability.VISION in openai.capabilities

    def test_deepseek_provider(self):
        """Test DeepSeek provider configuration"""
        deepseek = BUILTIN_PROVIDERS.get("deepseek")
        assert deepseek is not None
        assert deepseek.id == "deepseek"
        assert "deepseek-chat" in deepseek.models
        assert ProviderCapability.LONG_CONTEXT in deepseek.capabilities
        assert ProviderCapability.FAST in deepseek.capabilities

    def test_modelscope_provider(self):
        """Test ModelScope provider configuration"""
        modelscope = BUILTIN_PROVIDERS.get("modelscope")
        assert modelscope is not None
        assert modelscope.id == "modelscope"
        assert "deepseek-ai/DeepSeek-V3.2" in modelscope.models
        assert ProviderCapability.THINKING in modelscope.capabilities
        assert modelscope.requires_extra_body is True
        assert modelscope.extra_body_params is not None

    def test_bytedance_provider(self):
        """Test Bytedance provider configuration"""
        bytedance = BUILTIN_PROVIDERS.get("bytedance")
        assert bytedance is not None
        assert bytedance.id == "bytedance"
        assert "doubao-vision" in bytedance.models
        assert ProviderCapability.VISION in bytedance.capabilities
        assert ProviderCapability.BILINGUAL in bytedance.capabilities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
