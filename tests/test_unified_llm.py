"""
Test script for Unified LLM Architecture

This script verifies that the new unified LLM architecture is working correctly.
Run this to ensure your setup is correct.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("[1/6] Testing imports...")
    try:
        from utils.llm.base_client import BaseLLMClient
        from utils.llm.model_registry import ModelRegistry, ModelCapability, BUILTIN_MODELS
        from utils.llm.unified_manager import UnifiedLLMManager
        from config.llm_config import get_recommended_models, get_fallback_chain
        print("  [OK] All imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False


def test_model_registry():
    """Test model registry"""
    print("\n[2/6] Testing ModelRegistry...")
    try:
        from utils.llm.model_registry import ModelRegistry, ModelCapability

        # Test get_model_info
        glm_info = ModelRegistry.get_model_info("glm-4-flash")
        assert glm_info is not None
        assert glm_info.provider == "zhipu"
        print(f"  [OK] get_model_info('glm-4-flash'): {glm_info.name}")

        # Test list_models
        vision_models = ModelRegistry.list_models(capability=ModelCapability.VISION)
        assert len(vision_models) > 0
        print(f"  [OK] list_models(vision): {len(vision_models)} models")

        # Test get_vision_models
        vision_models2 = ModelRegistry.get_vision_models()
        print(f"  [OK] get_vision_models(): {len(vision_models2)} models")

        return True
    except Exception as e:
        print(f"  [FAIL] ModelRegistry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_config():
    """Test LLM config module"""
    print("\n[3/6] Testing LLM config...")
    try:
        from config.llm_config import get_recommended_models, get_fallback_chain

        # Test get_recommended_models
        polish_rec = get_recommended_models("polish")
        assert "models" in polish_rec
        assert "fallback" in polish_rec
        print(f"  [OK] get_recommended_models('polish'): {polish_rec['models']}")

        # Test get_fallback_chain
        text_chain = get_fallback_chain("text")
        assert len(text_chain) > 0
        print(f"  [OK] get_fallback_chain('text'): {text_chain}")

        return True
    except Exception as e:
        print(f"  [FAIL] LLM config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_manager():
    """Test UnifiedLLMManager"""
    print("\n[4/6] Testing UnifiedLLMManager...")
    try:
        from utils.llm.unified_manager import UnifiedLLMManager

        manager = UnifiedLLMManager()
        print("  [OK] UnifiedLLMManager initialized")

        # Test list_available_models
        available = manager.list_available_models()
        print(f"  [OK] list_available_models(): {len(available)} models available")
        for model_id, info in available.items():
            print(f"    - {model_id}: {info['name']}")

        return True
    except Exception as e:
        print(f"  [FAIL] UnifiedLLMManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_client_inheritance():
    """Test that LLMClient inherits from BaseLLMClient"""
    print("\n[5/6] Testing LLMClient inheritance...")
    try:
        from utils.llm_client import LLMClient
        from utils.llm.base_client import BaseLLMClient

        assert issubclass(LLMClient, BaseLLMClient)
        print("  [OK] LLMClient inherits from BaseLLMClient")

        # Check for new methods
        client_methods = dir(LLMClient)
        assert "analyze_image" in client_methods
        assert "chat_completion_async" in client_methods
        print("  [OK] LLMClient has analyze_image and chat_completion_async methods")

        return True
    except Exception as e:
        print(f"  [FAIL] LLMClient inheritance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_polisher_unified():
    """Test TextPolisher with unified manager"""
    print("\n[6/6] Testing TextPolisher with unified manager...")
    try:
        from utils.text_polisher import TextPolisher

        # Test legacy mode
        polisher_legacy = TextPolisher(use_unified_manager=False)
        assert not polisher_legacy.use_unified_manager
        print("  [OK] TextPolisher legacy mode initialized")

        # Test unified mode
        polisher_unified = TextPolisher(use_unified_manager=True)
        assert polisher_unified.use_unified_manager
        assert polisher_unified.manager is not None
        print("  [OK] TextPolisher unified mode initialized")

        return True
    except Exception as e:
        print(f"  [FAIL] TextPolisher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Unified LLM Architecture Test Suite")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("ModelRegistry", test_model_registry()))
    results.append(("LLM Config", test_llm_config()))
    results.append(("UnifiedLLMManager", test_unified_manager()))
    results.append(("LLMClient Inheritance", test_llm_client_inheritance()))
    results.append(("TextPolisher", test_text_polisher_unified()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] PASSED" if result else "[FAIL] FAILED"
        print(f"{name:.<40} {status}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! The unified LLM architecture is working correctly.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
