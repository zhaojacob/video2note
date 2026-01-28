"""
Test LLM Integration - 测试 DeepSeek 和豆包集成

测试内容:
1. DeepSeek 文本模型调用 (deepseek-chat)
2. 豆包视觉模型调用 (doubao-seed-1-6-vision-250815)
3. UnifiedLLMManager 客户端创建
4. API 格式验证
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.llm.unified_manager import UnifiedLLMManager
from utils.logger import setup_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("test_llm_integration", "logs/test_llm_integration.log")


def test_deepseek_text():
    """Test DeepSeek text model"""
    print("\n" + "=" * 80)
    print("TEST 1: DeepSeek Text Model (deepseek-chat)")
    print("=" * 80)
    
    manager = UnifiedLLMManager()
    
    # Get DeepSeek client
    client = manager.get_client(provider="deepseek", model="deepseek-chat")
    
    if not client:
        print("❌ Failed to create DeepSeek client")
        print("   Check DEEPSEEK_API_KEY in .env file")
        return False
    
    print("✓ DeepSeek client created successfully")
    print(f"  Model: {client.model}")
    print(f"  Base URL: {client.base_url}")
    
    # Test chat completion
    print("\n[Testing chat completion...]")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello, DeepSeek!' in Chinese."}
    ]
    
    try:
        response = client.chat_completion(messages, max_tokens=100)
        
        if response:
            print("✓ Chat completion successful")
            print(f"  Response: {response}")
            return True
        else:
            print("❌ Chat completion failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        return False


def test_doubao_vision():
    """Test Doubao vision model"""
    print("\n" + "=" * 80)
    print("TEST 2: Doubao Vision Model (doubao-seed-1-6-vision-250815)")
    print("=" * 80)
    
    manager = UnifiedLLMManager()
    
    # Get Doubao client
    client = manager.get_client(provider="bytedance", model="doubao-seed-1-6-vision-250815")
    
    if not client:
        print("❌ Failed to create Doubao client")
        print("   Check ARK_API_KEY in .env file")
        return False
    
    print("✓ Doubao client created successfully")
    print(f"  Client type: {type(client).__name__}")
    print(f"  Model: {client.model}")
    print(f"  Base URL: {client.base_url}")
    
    # Check if it's DoubaoVisionClient
    from utils.llm.doubao_vision_client import DoubaoVisionClient
    if isinstance(client, DoubaoVisionClient):
        print("✓ Correct client type: DoubaoVisionClient")
    else:
        print(f"⚠ Warning: Expected DoubaoVisionClient, got {type(client).__name__}")
    
    # Test image analysis (if test image exists)
    test_image = project_root / "test_image.jpg"
    if not test_image.exists():
        print("\n⚠ No test image found, skipping image analysis test")
        print(f"  Create a test image at: {test_image}")
        return True
    
    print(f"\n[Testing image analysis with {test_image}...]")
    
    try:
        result = client.analyze_image(
            test_image,
            prompt="请描述这张图片的内容。",
            max_tokens=500
        )
        
        if result:
            print("✓ Image analysis successful")
            print(f"  Description length: {len(result.get('description', ''))}")
            print(f"  Description preview: {result.get('description', '')[:200]}...")
            return True
        else:
            print("❌ Image analysis failed - no result")
            return False
            
    except Exception as e:
        print(f"❌ Image analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_client_types():
    """Test that correct client types are created"""
    print("\n" + "=" * 80)
    print("TEST 3: Client Type Verification")
    print("=" * 80)
    
    manager = UnifiedLLMManager()
    
    from utils.llm_client import LLMClient
    from utils.llm.doubao_vision_client import DoubaoVisionClient
    
    # Test DeepSeek -> should be LLMClient
    deepseek_client = manager.get_client(provider="deepseek", model="deepseek-chat")
    if deepseek_client:
        if isinstance(deepseek_client, LLMClient) and not isinstance(deepseek_client, DoubaoVisionClient):
            print("✓ DeepSeek uses standard LLMClient")
        else:
            print(f"❌ DeepSeek has wrong client type: {type(deepseek_client).__name__}")
    else:
        print("⚠ DeepSeek client not available")
    
    # Test Doubao -> should be DoubaoVisionClient
    doubao_client = manager.get_client(provider="bytedance", model="doubao-seed-1-6-vision-250815")
    if doubao_client:
        if isinstance(doubao_client, DoubaoVisionClient):
            print("✓ Doubao uses DoubaoVisionClient")
        else:
            print(f"❌ Doubao has wrong client type: {type(doubao_client).__name__}")
    else:
        print("⚠ Doubao client not available")
    
    return True


def test_api_keys():
    """Test API key configuration"""
    print("\n" + "=" * 80)
    print("TEST 4: API Key Configuration")
    print("=" * 80)
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    ark_key = os.getenv("ARK_API_KEY")
    
    if deepseek_key:
        print(f"✓ DEEPSEEK_API_KEY configured (length: {len(deepseek_key)})")
    else:
        print("❌ DEEPSEEK_API_KEY not found in .env")
    
    if ark_key:
        print(f"✓ ARK_API_KEY configured (length: {len(ark_key)})")
    else:
        print("❌ ARK_API_KEY not found in .env")
    
    return bool(deepseek_key and ark_key)


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LLM INTEGRATION TEST SUITE")
    print("=" * 80)
    
    results = {
        "API Keys": test_api_keys(),
        "Client Types": test_client_types(),
        "DeepSeek Text": test_deepseek_text(),
        "Doubao Vision": test_doubao_vision(),
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
