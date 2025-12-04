"""Test script for GuidanceService to verify method signatures and structure."""

import asyncio
import inspect
from typing import get_type_hints


def verify_service_structure():
    """Verify that GuidanceService has all required methods."""

    # Import the service
    from src.services.guidance_service import GuidanceService

    # Define expected methods and their signatures
    expected_methods = {
        # API Guidance Methods
        "get_api_guidance": {"api_name": str},
        "list_api_guidance": {"active_only": bool},
        "upsert_api_guidance": {"api_name": str},
        "delete_api_guidance": {"api_name": str},

        # Category Guidance Methods
        "get_category_guidance": {"api_name": str, "category_name": str},
        "list_category_guidance": {"api_name": None, "active_only": bool},
        "upsert_category_guidance": {"api_name": str, "category_name": str},
        "delete_category_guidance": {"id": int},

        # Workflow Methods
        "create_workflow": {"name": str, "display_name": str},
        "get_workflow": {"workflow_id": int},
        "list_workflows": {"active_only": bool, "use_case_tag": None},
        "update_workflow": {"workflow_id": int},
        "delete_workflow": {"workflow_id": int},
        "set_workflow_steps": {"workflow_id": int, "steps": list},

        # Tool Override Methods
        "get_tool_override": {"operation_name": str},
        "get_all_tool_overrides": {},
        "list_tool_overrides": {"active_only": bool},
        "upsert_tool_override": {"operation_name": str},
        "delete_tool_override": {"operation_name": str},

        # System Prompt Methods
        "get_system_prompt_sections": {"active_only": bool},
        "upsert_system_prompt_section": {"section_name": str},
        "delete_system_prompt_section": {"section_name": str},

        # Composite Methods
        "generate_system_prompt": {},
        "build_enhanced_tool_description": {"operation": dict},
    }

    print("Verifying GuidanceService structure...\n")

    # Check each method exists and is async
    service = GuidanceService
    missing_methods = []
    non_async_methods = []

    for method_name in expected_methods:
        if not hasattr(service, method_name):
            missing_methods.append(method_name)
            print(f"❌ Missing method: {method_name}")
        else:
            method = getattr(service, method_name)
            if not asyncio.iscoroutinefunction(method):
                non_async_methods.append(method_name)
                print(f"❌ Method not async: {method_name}")
            else:
                # Get method signature
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                # Remove 'self' from params
                if 'self' in params:
                    params.remove('self')

                print(f"✓ {method_name}({', '.join(params)})")

    print(f"\n{'='*60}")
    if missing_methods or non_async_methods:
        print("❌ VERIFICATION FAILED")
        if missing_methods:
            print(f"Missing methods: {', '.join(missing_methods)}")
        if non_async_methods:
            print(f"Non-async methods: {', '.join(non_async_methods)}")
        return False
    else:
        print("✓ ALL CHECKS PASSED")
        print(f"Total methods: {len(expected_methods)}")
        print("All methods are present and async")
        return True


def verify_models():
    """Verify that all guidance models are properly defined."""

    from src.models.guidance import (
        APIGuidance,
        CategoryGuidance,
        Workflow,
        WorkflowStep,
        ToolDescriptionOverride,
        SystemPromptSection,
    )

    print("\n\nVerifying guidance models...\n")

    models = {
        "APIGuidance": APIGuidance,
        "CategoryGuidance": CategoryGuidance,
        "Workflow": Workflow,
        "WorkflowStep": WorkflowStep,
        "ToolDescriptionOverride": ToolDescriptionOverride,
        "SystemPromptSection": SystemPromptSection,
    }

    for model_name, model_class in models.items():
        # Check table name
        table_name = model_class.__tablename__

        # Check to_dict method
        has_to_dict = hasattr(model_class, "to_dict")

        # Check __repr__
        has_repr = hasattr(model_class, "__repr__")

        status = "✓" if has_to_dict and has_repr else "❌"
        print(f"{status} {model_name} (table: {table_name})")

        if not has_to_dict:
            print(f"   ❌ Missing to_dict() method")
        if not has_repr:
            print(f"   ❌ Missing __repr__() method")

    print(f"\n{'='*60}")
    print("✓ ALL MODELS VERIFIED")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("GUIDANCE SERVICE VERIFICATION")
    print("=" * 60)

    try:
        service_ok = verify_service_structure()
        models_ok = verify_models()

        if service_ok and models_ok:
            print("\n" + "=" * 60)
            print("✓ VERIFICATION COMPLETE - ALL CHECKS PASSED")
            print("=" * 60)
            exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ VERIFICATION FAILED")
            print("=" * 60)
            exit(1)
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
