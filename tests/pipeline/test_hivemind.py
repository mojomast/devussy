import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.pipeline.hivemind import HiveMindManager

@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.generate_completion = AsyncMock(return_value="Mock Response")
    client.generate_completion_streaming = AsyncMock()
    client.streaming_enabled = False
    return client

@pytest.fixture
def hivemind_manager(mock_llm_client):
    return HiveMindManager(mock_llm_client)

@pytest.mark.asyncio
async def test_initialization(hivemind_manager, mock_llm_client):
    assert hivemind_manager.llm_client == mock_llm_client

@pytest.mark.asyncio
async def test_execute_parallel_basic(hivemind_manager, mock_llm_client):
    mock_llm_client.generate_completion.side_effect = ["Response 1", "Response 2", "Response 3"]
    
    responses = await hivemind_manager._execute_parallel(
        prompt="Test Prompt",
        count=3,
        temperature_jitter=False,
        base_temperature=0.7
    )
    
    assert len(responses) == 3
    assert responses == ["Response 1", "Response 2", "Response 3"]
    assert mock_llm_client.generate_completion.call_count == 3

@pytest.mark.asyncio
async def test_execute_parallel_jitter(hivemind_manager, mock_llm_client):
    mock_llm_client.generate_completion.return_value = "Response"
    
    await hivemind_manager._execute_parallel(
        prompt="Test Prompt",
        count=3,
        temperature_jitter=True,
        base_temperature=0.7
    )
    
    assert mock_llm_client.generate_completion.call_count == 3
    
    # Check temperatures
    calls = mock_llm_client.generate_completion.call_args_list
    temps = [call.kwargs['temperature'] for call in calls]
    
    # With 3 drones and base 0.7, we expect spread around 0.7
    # Logic: offset = (i / (count - 1) - 0.5) * 0.4
    # i=0: (0 - 0.5) * 0.4 = -0.2 -> 0.5
    # i=1: (0.5 - 0.5) * 0.4 = 0 -> 0.7
    # i=2: (1 - 0.5) * 0.4 = 0.2 -> 0.9
    
    assert 0.5 == pytest.approx(temps[0])
    assert 0.7 == pytest.approx(temps[1])
    assert 0.9 == pytest.approx(temps[2])

@patch("src.pipeline.hivemind.render_template")
def test_format_for_arbiter(mock_render, hivemind_manager):
    mock_render.return_value = "Rendered Prompt"
    
    prompt = hivemind_manager._format_for_arbiter(
        original_prompt="Original",
        drone_responses=["R1", "R2"]
    )
    
    assert prompt == "Rendered Prompt"
    mock_render.assert_called_once()
    
    call_args = mock_render.call_args
    assert call_args[0][0] == "hivemind_arbiter.jinja"
    context = call_args[0][1]
    assert context["original_prompt"] == "Original"
    assert len(context["drones"]) == 2
    assert context["drones"][0]["content"] == "R1"

@pytest.mark.asyncio
async def test_call_arbiter_no_streaming(hivemind_manager, mock_llm_client):
    mock_llm_client.generate_completion.return_value = "Arbiter Decision"
    
    response = await hivemind_manager._call_arbiter("Prompt")
    
    assert response == "Arbiter Decision"
    mock_llm_client.generate_completion.assert_called_once()
    # Check low temp
    assert mock_llm_client.generate_completion.call_args.kwargs["temperature"] == 0.2

@pytest.mark.asyncio
async def test_call_arbiter_streaming(hivemind_manager, mock_llm_client):
    mock_llm_client.streaming_enabled = True
    mock_handler = MagicMock()
    mock_handler.on_token_async = AsyncMock()
    
    # Mock the streaming behavior
    async def mock_stream(prompt, callback, **kwargs):
        callback("Chunk 1")
        callback("Chunk 2")
    
    mock_llm_client.generate_completion_streaming.side_effect = mock_stream
    
    response = await hivemind_manager._call_arbiter(
        "Prompt",
        streaming_handler=mock_handler
    )
    
    assert response == "Chunk 1Chunk 2"
    mock_llm_client.generate_completion_streaming.assert_called_once()
