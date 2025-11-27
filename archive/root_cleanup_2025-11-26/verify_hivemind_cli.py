
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
from src.config import AppConfig, HiveMindConfig
from src.pipeline.detailed_devplan import DetailedDevPlanGenerator
from src.models import DevPlan, DevPlanPhase
from src.concurrency import ConcurrencyManager

async def verify_hivemind_flow():
    print("Starting HiveMind Verification...")
    
    # 1. Setup Config
    config = AppConfig()
    config.hivemind.enabled = True
    config.hivemind.drone_count = 3
    
    # 2. Mock LLM Client
    mock_llm = MagicMock()
    mock_llm.generate_completion = AsyncMock(side_effect=[
        "Drone 1 response",
        "Drone 2 response",
        "Drone 3 response",
        "Arbiter response: Final Plan"
    ])
    # Mock streaming if needed, but we can stick to non-streaming for logic check
    mock_llm.streaming_enabled = False
    
    # 3. Setup Generator
    concurrency = ConcurrencyManager(max_concurrent=1)
    generator = DetailedDevPlanGenerator(mock_llm, concurrency)
    
    # Force the generator's hivemind instance to use our config if it reads from global
    # Note: detailed_devplan.py calls load_config() inside _generate_phase_details
    # So we need to patch load_config or set env vars.
    # Setting env vars is safer for integration testing.
    os.environ["HIVEMIND_ENABLED"] = "true"
    os.environ["HIVEMIND_DRONE_COUNT"] = "3"
    
    # 4. Create Dummy Input
    basic_plan = DevPlan(
        phases=[DevPlanPhase(number=1, title="Test Phase", steps=[])],
        summary="Test Summary"
    )
    
    # 5. Run Generate
    print("Running generator...")
    result = await generator.generate(
        basic_devplan=basic_plan,
        project_name="Test Project",
        tech_stack=["Python"]
    )
    
    # 6. Verify
    print("Verifying calls...")
    # We expect 3 drone calls + 1 arbiter call = 4 calls
    call_count = mock_llm.generate_completion.call_count
    print(f"LLM generate_completion called {call_count} times")
    
    if call_count >= 4:
        print("SUCCESS: HiveMind flow triggered (Drones + Arbiter)")
    else:
        print(f"FAILURE: Expected at least 4 calls, got {call_count}")
        
    # Verify Arbiter output made it to the result
    phase1 = result.phases[0]
    # The detailed_devplan.py parses the response. 
    # Our mock response "Arbiter response: Final Plan" might not parse well into steps,
    # but we just want to ensure the flow happened.
    print(f"Result raw response chars: {len(result.raw_detailed_responses[1])}")

if __name__ == "__main__":
    asyncio.run(verify_hivemind_flow())
