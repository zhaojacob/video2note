"""
Test script for unified LLM configuration system

This script tests:
1. YAML configuration loading
2. Provider registry integration
3. UnifiedLLMManager functionality
4. ImageAnalyzer with unified manager
5. TextPolisher with unified manager
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_yaml_loading():
    """Test YAML configuration loading"""
    print("\n" + "="*70)
    print("TEST 1: YAML Configuration Loading")
    print("="*70)

    try:
        from config.yaml_config_loader import (
            load_llm_config,
            get_provider_config,
            get_task_recommendation,
            get_fallback_chain,
            list_available_providers
        )

        # Load configuration
        config = load_llm_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  Version: {config['version']}")
        print(f"  Providers: {len(config['providers'])}")
        print(f"  Task recommendations: {len(config['task_recommendations'])}")

        # Test provider loading
        deepseek = get_provider_config("deepseek")
        if deepseek:
            print(f"\n✓ DeepSeek provider loaded:")
            print(f"  Name: {deepseek.name}")
            print(f"  Base URL: {deepseek.base_url}")
            print(f"  Models: {', '.join(deepseek.models)}")
            print(f"  API Key configured: {'Yes' if deepseek.get_api_key() else 'No'}")

        bytedance = get_provider_config("bytedance")
        if bytedance:
            print(f"\n✓ Bytedance provider loaded:")
            print(f"  Name: {bytedance.name}")
            print(f"  Base URL: {bytedance.base_url}")
            print(f"  Models: {', '.join(bytedance.models)}")
            print(f"  API Key configured: {'Yes' if bytedance.get_api_key() else 'No'}")

        # Test task recommendation
        polish_rec = get_task_recommendation("polish")
        if polish_rec:
            print(f"\n✓ Polish task recommendation:")
            print(f"  Providers: {polish_rec['providers']}")
            print(f"  Models: {polish_rec['models']}")
            print(f"  Reason: {polish_rec['reason']}")

        # Test fallback chain
        text_fallback = get_fallback_chain("text")
        print(f"\n✓ Text fallback chain: {text_fallback}")

        # List available providers
        available = list_available_providers()
        print(f"\n✓ Available providers (with API keys): {available}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_registry():
    """Test provider registry integration"""
    print("\n" + "="*70)
    print("TEST 2: Provider Registry Integration")
    print("="*70)

    try:
        from utils.llm.provider_registry import ProviderRegistry

        registry = ProviderRegistry()

        # Get provider
        deepseek = registry.get_provider("deepseek")
        if deepseek:
            print(f"✓ DeepSeek provider from registry:")
            print(f"  Name: {deepseek.name}")
            print(f"  Base URL: {deepseek.base_url}")
            print(f"  Models: {', '.join(deepseek.models)}")

        # List all providers
        all_providers = registry.list_providers()
        print(f"\n✓ Total providers in registry: {len(all_providers)}")
        for pid, pinfo in all_providers.items():
            api_key_status = "✓" if pinfo.get_api_key() else "✗"
            print(f"  {api_key_status} {pid}: {pinfo.name} ({len(pinfo.models)} models)")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_manager():
    """Test UnifiedLLMManager"""
    print("\n" + "="*70)
    print("TEST 3: UnifiedLLMManager")
    print("="*70)

    try:
        from utils.llm.unified_manager import UnifiedLLMManager

        manager = UnifiedLLMManager()
        print("✓ UnifiedLLMManager initialized")

        # List available models
        available_models = manager.list_available_models()
        print(f"\n✓ Available models: {len(available_models)}")
        for model_id, info in list(available_models.items())[:5]:  # Show first 5
            print(f"  - {model_id} ({info['provider']}): {', '.join(info['capabilities'])}")

        # List available providers
        available_providers = manager.list_available_providers()
        print(f"\n✓ Available providers: {len(available_providers)}")
        for provider_id, info in available_providers.items():
            print(f"  - {provider_id}: {info['name']} ({len(info['models'])} models)")

        # Try to get a client (if API key is configured)
        print("\n✓ Testing client creation:")
        client = manager.get_client(provider="deepseek", model="deepseek-chat")
        if client:
            print(f"  ✓ Created client for deepseek:deepseek-chat")
            print(f"  ✓ Client available: {client.is_available()}")
        else:
            print(f"  ✗ Failed to create client (API key may not be configured)")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_analyzer():
    """Test ImageAnalyzer with unified manager"""
    print("\n" + "="*70)
    print("TEST 4: ImageAnalyzer with Unified Manager")
    print("="*70)

    try:
        from analysis.image_analyzer import ImageAnalyzer

        # Initialize with unified manager (default)
        analyzer = ImageAnalyzer(use_unified_manager=True)
        print("✓ ImageAnalyzer initialized with UnifiedLLMManager")
        print(f"  Using unified manager: {analyzer.use_unified_manager}")
        print(f"  Manager available: {analyzer.manager is not None}")

        # Check task recommendations
        print(f"\n✓ Task recommendations loaded:")
        print(f"  Formula: {analyzer.vision_formula.get('providers', [])}")
        print(f"  Code: {analyzer.vision_code.get('providers', [])}")
        print(f"  Chinese: {analyzer.vision_chinese.get('providers', [])}")
        print(f"  General: {analyzer.vision_general.get('providers', [])}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_polisher():
    """Test TextPolisher with unified manager"""
    print("\n" + "="*70)
    print("TEST 5: TextPolisher with Unified Manager")
    print("="*70)

    try:
        from utils.text_polisher import TextPolisher

        # Initialize with unified manager (default)
        polisher = TextPolisher(use_unified_manager=True)
        print("✓ TextPolisher initialized with UnifiedLLMManager")
        print(f"  Using unified manager: {polisher.use_unified_manager}")
        print(f"  Manager available: {polisher.manager is not None}")
        print(f"  Fallback providers: {polisher.fallback_providers}")
        print(f"  Polisher available: {polisher.is_available()}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings_integration():
    """Test settings.py integration"""
    print("\n" + "="*70)
    print("TEST 6: Settings Integration")
    print("="*70)

    try:
        from config.settings import UNIFIED_LLM_CONFIG

        print("✓ UNIFIED_LLM_CONFIG loaded:")
        print(f"  Enabled: {UNIFIED_LLM_CONFIG['enabled']}")
        print(f"  Default text model: {UNIFIED_LLM_CONFIG['default_text_model']}")
        print(f"  Default vision model: {UNIFIED_LLM_CONFIG['default_vision_model']}")
        print(f"  Default text provider: {UNIFIED_LLM_CONFIG.get('default_text_provider', 'N/A')}")
        print(f"  Default vision provider: {UNIFIED_LLM_CONFIG.get('default_vision_provider', 'N/A')}")
        print(f"  Enable fallback: {UNIFIED_LLM_CONFIG['enable_fallback']}")

        if UNIFIED_LLM_CONFIG['enabled']:
            print("\n✓ Unified manager is ENABLED by default")
        else:
            print("\n✗ Warning: Unified manager is DISABLED")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("UNIFIED LLM CONFIGURATION SYSTEM - TEST SUITE")
    print("="*70)

    results = []

    # Run tests
    results.append(("YAML Loading", test_yaml_loading()))
    results.append(("Provider Registry", test_provider_registry()))
    results.append(("UnifiedLLMManager", test_unified_manager()))
    results.append(("ImageAnalyzer", test_image_analyzer()))
    results.append(("TextPolisher", test_text_polisher()))
    results.append(("Settings Integration", test_settings_integration()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Configuration system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
