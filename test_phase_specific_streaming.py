#!/usr/bin/env python3
"""
Test script to verify phase-specific streaming functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.menu import SessionSettings, get_design_streaming_status, get_devplan_streaming_status, get_handoff_streaming_status
from src.config import AppConfig

def test_session_settings_fields():
    """Test that SessionSettings has the new phase-specific streaming fields."""
    print("Testing SessionSettings model fields...")
    
    # Test that all fields exist
    settings = SessionSettings()
    
    # Check that the new fields exist
    assert hasattr(settings, 'streaming_design_enabled'), "streaming_design_enabled field missing"
    assert hasattr(settings, 'streaming_devplan_enabled'), "streaming_devplan_enabled field missing" 
    assert hasattr(settings, 'streaming_handoff_enabled'), "streaming_handoff_enabled field missing"
    assert hasattr(settings, 'streaming'), "streaming field missing"
    
    print("✓ All phase-specific streaming fields exist")

def test_helper_methods():
    """Test the helper methods for determining streaming status."""
    print("\nTesting helper methods...")
    
    config = AppConfig()
    config.streaming_enabled = False
    
    # Test case 1: No session settings
    result = get_design_streaming_status(config, None)
    assert result == False, f"Expected False, got {result}"
    
    result = get_devplan_streaming_status(config, None)
    assert result == False, f"Expected False, got {result}"
    
    result = get_handoff_streaming_status(config, None)
    assert result == False, f"Expected False, got {result}"
    
    # Test case 2: Global streaming enabled
    settings = SessionSettings()
    settings.streaming = True
    
    result = get_design_streaming_status(config, settings)
    assert result == True, f"Expected True, got {result}"
    
    result = get_devplan_streaming_status(config, settings)
    assert result == True, f"Expected True, got {result}"
    
    result = get_handoff_streaming_status(config, settings)
    assert result == True, f"Expected True, got {result}"
    
    # Test case 3: Phase-specific overrides
    settings.streaming = False  # Global disabled
    settings.streaming_design_enabled = True  # Design enabled
    settings.streaming_devplan_enabled = False  # DevPlan disabled
    settings.streaming_handoff_enabled = True  # Handoff enabled
    
    result = get_design_streaming_status(config, settings)
    assert result == True, f"Expected True for design, got {result}"
    
    result = get_devplan_streaming_status(config, settings)
    assert result == False, f"Expected False for devplan, got {result}"
    
    result = get_handoff_streaming_status(config, settings)
    assert result == True, f"Expected True for handoff, got {result}"
    
    # Test case 4: Partial phase-specific settings (fallback to global)
    settings2 = SessionSettings()
    settings2.streaming = True
    settings2.streaming_design_enabled = None  # Not set
    settings2.streaming_devplan_enabled = None  # Not set
    settings2.streaming_handoff_enabled = None  # Not set
    
    result = get_design_streaming_status(config, settings2)
    assert result == True, f"Expected True (fallback to global), got {result}"
    
    print("✓ All helper methods work correctly")

def test_config_application():
    """Test that settings can be applied to config with phase-specific streaming."""
    print("\nTesting config application...")
    
    from src.ui.menu import apply_settings_to_config
    
    config = AppConfig()
    settings = SessionSettings()
    
    # Set phase-specific streaming
    settings.streaming_design_enabled = True
    settings.streaming_devplan_enabled = False
    settings.streaming_handoff_enabled = True
    
    # Apply settings
    apply_settings_to_config(config, settings)
    
    # Check that stage configs were created with correct streaming flags
    assert config.design_llm is not None, "design_llm should be created"
    assert config.devplan_llm is not None, "devplan_llm should be created"
    assert config.handoff_llm is not None, "handoff_llm should be created"
    
    assert config.design_llm.streaming_enabled == True, f"Expected design streaming enabled, got {config.design_llm.streaming_enabled}"
    assert config.devplan_llm.streaming_enabled == False, f"Expected devplan streaming disabled, got {config.devplan_llm.streaming_enabled}"
    assert config.handoff_llm.streaming_enabled == True, f"Expected handoff streaming enabled, got {config.handoff_llm.streaming_enabled}"
    
    print("✓ Config application works correctly")

def test_backward_compatibility():
    """Test that backward compatibility is maintained."""
    print("\nTesting backward compatibility...")
    
    config = AppConfig()
    config.streaming_enabled = True
    
    # Test that old global streaming still works
    settings = SessionSettings()
    settings.streaming = True  # Old global field
    
    # Without phase-specific settings, should fall back to global
    result = get_design_streaming_status(config, settings)
    assert result == True, f"Expected True (backward compatibility), got {result}"
    
    result = get_devplan_streaming_status(config, settings)
    assert result == True, f"Expected True (backward compatibility), got {result}"
    
    result = get_handoff_streaming_status(config, settings)
    assert result == True, f"Expected True (backward compatibility), got {result}"
    
    print("✓ Backward compatibility maintained")

def main():
    """Run all tests."""
    print("Testing Phase-Specific Streaming Implementation")
    print("=" * 50)
    
    try:
        test_session_settings_fields()
        test_helper_methods()
        test_config_application()
        test_backward_compatibility()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Phase-specific streaming implementation is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)