#!/usr/bin/env python3
"""
Provider Configuration Verification Script

This script verifies that all provider configurations are consistent and correct.
Run this script after making changes to provider configurations.
"""

import sys
from utils.llm.provider_registry import BUILTIN_PROVIDERS, ProviderRegistry
from utils.llm.model_registry import BUILTIN_MODELS
from config.settings import GLM_CONFIG, DOUBAO_CONFIG, MODELSCOPE_CONFIG, DEEPSEEK_CONFIG


def check_provider_registry():
    """Check ProviderRegistry configurations"""
    print("=" * 80)
    print("1. CHECKING PROVIDER REGISTRY")
    print("=" * 80)

    issues = []

    for provider_id, provider in BUILTIN_PROVIDERS.items():
        print(f"\n[{provider_id.upper()}]")
        print(f"  Name: {provider.name}")
        print(f"  Base URL: {provider.base_url}")
        print(f"  API Key: {provider.api_key_env}")
        print(f"  Models: {', '.join(provider.models)}")

        # Validate base_url format
        if provider_id == "zhipu":
            # Zhipu should have full path
            if "/chat/completions" not in provider.base_url:
                issues.append(f"[ERROR] Zhipu base_url missing /chat/completions")
            else:
                print(f"  [OK] Base URL format correct (full path)")
        else:
            # Others should NOT have /chat/completions (SDK adds it)
            if "/chat/completions" in provider.base_url:
                issues.append(f"[WARN] {provider_id} base_url includes /chat/completions (SDK will duplicate)")
            else:
                print(f"  [OK] Base URL format correct (base path)")

        # Validate models list
        if not provider.models:
            issues.append(f"[ERROR] {provider_id} has no models defined")
        else:
            print(f"  [OK] Has {len(provider.models)} model(s)")

    return issues


def check_settings_consistency():
    """Check consistency between provider_registry.py and settings.py"""
    print("\n" + "=" * 80)
    print("2. CHECKING SETTINGS.PY CONSISTENCY")
    print("=" * 80)

    issues = []

    # Mapping from provider_id to settings config
    settings_map = {
        "zhipu": ("GLM_CONFIG", GLM_CONFIG),
        "bytedance": ("DOUBAO_CONFIG", DOUBAO_CONFIG),
        "modelscope": ("MODELSCOPE_CONFIG", MODELSCOPE_CONFIG),
        "deepseek": ("DEEPSEEK_CONFIG", DEEPSEEK_CONFIG),
    }

    for provider_id, (config_name, config) in settings_map.items():
        provider = BUILTIN_PROVIDERS.get(provider_id)

        if not provider:
            issues.append(f"❌ Provider {provider_id} not in BUILTIN_PROVIDERS")
            continue

        print(f"\n[{provider_id.upper()}] vs {config_name}")

        # Check model consistency
        settings_model = config.get("model")
        provider_models = provider.models

        if settings_model in provider_models:
            print(f"  [OK] Model '{settings_model}' found in provider.models")
        else:
            issues.append(f"[ERROR] Model mismatch: settings.py='{settings_model}', provider.models={provider_models}")

        # Check base_url consistency
        settings_base_url = config.get("base_url")
        provider_base_url = provider.base_url

        if settings_base_url == provider_base_url:
            print(f"  [OK] Base URL consistent")
        else:
            issues.append(f"[WARN] Base URL mismatch:")
            issues.append(f"     settings.py:  {settings_base_url}")
            issues.append(f"     provider_reg: {provider_base_url}")

    return issues


def check_model_registry():
    """Check ModelRegistry configurations"""
    print("\n" + "=" * 80)
    print("3. CHECKING MODEL REGISTRY")
    print("=" * 80)

    issues = []

    for model_id, model_info in BUILTIN_MODELS.items():
        provider = BUILTIN_PROVIDERS.get(model_info.provider_id)

        if not provider:
            issues.append(f"[ERROR] Model {model_id}: provider '{model_info.provider_id}' not found")
            continue

        print(f"\n[{model_id}]")
        print(f"  Provider: {model_info.provider_id}")
        print(f"  Has model in provider: {model_id in provider.models}")

        # Check if model_id is in provider's models list
        if model_id in provider.models:
            print(f"  [OK] Model ID found in provider's models list")
        else:
            issues.append(f"[WARN] Model ID '{model_id}' not in provider.models={provider.models}")

    return issues


def check_legacy_compatibility():
    """Check backward compatibility properties"""
    print("\n" + "=" * 80)
    print("4. CHECKING LEGACY COMPATIBILITY")
    print("=" * 80)

    issues = []

    for model_id, model_info in BUILTIN_MODELS.items():
        print(f"\n[{model_id}]")

        # Test legacy provider property
        try:
            legacy_provider = model_info.provider
            if legacy_provider == model_info.provider_id:
                print(f"  [OK] Legacy .provider property works")
            else:
                issues.append(f"[ERROR] Legacy .provider mismatch")
        except Exception as e:
            issues.append(f"[ERROR] Legacy .provider property failed: {e}")

        # Test legacy env_key property
        try:
            env_key = model_info.env_key
            if env_key:
                print(f"  [OK] Legacy .env_key property: {env_key}")
            else:
                issues.append(f"[WARN] Legacy .env_key is empty")
        except Exception as e:
            issues.append(f"[ERROR] Legacy .env_key property failed: {e}")

        # Test legacy api_base property
        try:
            api_base = model_info.api_base
            if api_base:
                print(f"  [OK] Legacy .api_base property works")
            else:
                issues.append(f"[WARN] Legacy .api_base is empty")
        except Exception as e:
            issues.append(f"[ERROR] Legacy .api_base property failed: {e}")

    return issues


def main():
    """Run all checks"""
    print("\n" + "=" * 80)
    print("PROVIDER CONFIGURATION VERIFICATION")
    print("=" * 80)

    all_issues = []

    # Run all checks
    all_issues.extend(check_provider_registry())
    all_issues.extend(check_settings_consistency())
    all_issues.extend(check_model_registry())
    all_issues.extend(check_legacy_compatibility())

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if all_issues:
        print(f"\n[ERROR] Found {len(all_issues)} issue(s):\n")
        for issue in all_issues:
            print(f"  {issue}")
        print(f"\n[FAIL] VERIFICATION FAILED")
        return 1
    else:
        print("\n[OK] All checks passed!")
        print("\nProvider configurations are consistent and correct.")
        print(f"\n[PASS] VERIFICATION PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
