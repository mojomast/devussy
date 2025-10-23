"""Test script to verify multi-LLM configuration."""

from src.config import load_config
from src.clients.factory import create_llm_client
from src.pipeline.compose import PipelineOrchestrator
from src.concurrency import ConcurrencyManager

def test_multi_llm_config():
    """Test that per-stage LLM configs are loaded correctly."""
    print("=" * 60)
    print("Testing Multi-LLM Configuration")
    print("=" * 60)
    
    # Load config
    try:
        config = load_config("config/config.yaml")
        print("\n✓ Config loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load config: {e}")
        return False
    
    # Display global LLM config
    print(f"\n📋 Global LLM Config:")
    print(f"   Provider: {config.llm.provider}")
    print(f"   Model: {config.llm.model}")
    print(f"   API Key: {'✓ Set' if config.llm.api_key else '✗ Not set'}")
    print(f"   Temperature: {config.llm.temperature}")
    print(f"   Max Tokens: {config.llm.max_tokens}")
    
    # Check per-stage configs
    print(f"\n📋 Per-Stage LLM Configs:")
    
    for stage in ["design", "devplan", "handoff"]:
        stage_config = config.get_llm_config_for_stage(stage)
        print(f"\n   {stage.upper()} Stage:")
        print(f"      Provider: {stage_config.provider}")
        print(f"      Model: {stage_config.model}")
        print(f"      API Key: {'✓ Set' if stage_config.api_key else '✗ Not set'}")
        print(f"      Temperature: {stage_config.temperature}")
        print(f"      Max Tokens: {stage_config.max_tokens}")
    
    # Test creating orchestrator with stage-specific clients
    print(f"\n📋 Testing PipelineOrchestrator Initialization:")
    try:
        llm_client = create_llm_client(config)
        concurrency_manager = ConcurrencyManager(config.max_concurrent_requests)
        
        orchestrator = PipelineOrchestrator(
            llm_client=llm_client,
            concurrency_manager=concurrency_manager,
            config=config,
        )
        
        print("   ✓ Orchestrator created successfully")
        print(f"   Design client: {type(orchestrator.design_client).__name__}")
        print(f"   DevPlan client: {type(orchestrator.devplan_client).__name__}")
        print(f"   Handoff client: {type(orchestrator.handoff_client).__name__}")
        
    except Exception as e:
        print(f"   ✗ Failed to create orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ Multi-LLM configuration test passed!")
    print("=" * 60)
    print("\n💡 Usage Examples:")
    print("\n1. Set per-stage models in config/config.yaml:")
    print("   design_model: gpt-4")
    print("   devplan_model: gpt-3.5-turbo")
    print("   handoff_model: gpt-4")
    print("\n2. Set per-stage API keys via environment variables:")
    print("   set DESIGN_API_KEY=sk-...")
    print("   set DEVPLAN_API_KEY=sk-...")
    print("   set HANDOFF_API_KEY=sk-...")
    print("\n3. Run commands normally - they'll use stage-specific configs:")
    print("   python -m src.cli interactive-design")
    print("   python -m src.cli run-full-pipeline --name 'My Project' ...")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_multi_llm_config()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
