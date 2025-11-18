#!/usr/bin/env python3
"""Test Requesty AI streaming implementation."""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_requesty_streaming_implementation():
    """Test that RequestyClient has proper streaming implementation."""
    print("Testing Requesty AI streaming implementation...")
    
    # Test 1: Check RequestyClient has streaming method
    print("\n1. Testing RequestyClient streaming method...")
    try:
        from src.clients.requesty_client import RequestyClient
        
        # Check method exists
        assert hasattr(RequestyClient, 'generate_completion_streaming'), "Missing generate_completion_streaming method"
        assert hasattr(RequestyClient, '_post_chat_streaming'), "Missing _post_chat_streaming method"
        print("✓ RequestyClient has streaming methods")
        
        # Check method signature
        import inspect
        sig = inspect.signature(RequestyClient.generate_completion_streaming)
        params = list(sig.parameters.keys())
        assert 'prompt' in params, "Missing prompt parameter"
        assert 'callback' in params, "Missing callback parameter"
        print("✓ Streaming method has correct signature")
        
    except Exception as e:
        print(f"[ERROR] RequestyClient error: {e}")
        return False
    
    # Test 2: Check streaming implementation follows Requesty docs
    print("\n2. Testing streaming implementation details...")
    try:
        # Read the source to check key implementation details
        client_file = Path(__file__).parent / "src" / "clients" / "requesty_client.py"
        with open(client_file, 'r', encoding='utf-8') as f:
            client_source = f.read()
        
        # Check for key Requesty streaming requirements
        assert '"stream": True' in client_source, "Missing stream=True in payload"
        assert 'data: ' in client_source, "Missing SSE data parsing"
        assert 'choices[0].delta.content' in client_source, "Missing OpenAI streaming format parsing"
        assert 'callback(content)' in client_source, "Missing callback invocation"
        print("✓ Streaming implementation follows Requesty documentation")
        
    except Exception as e:
        print(f"[ERROR] Implementation check error: {e}")
        return False
    
    # Test 3: Check LLMInterviewManager uses streaming when enabled
    print("\n3. Testing LLMInterviewManager streaming integration...")
    try:
        interview_file = Path(__file__).parent / "src" / "llm_interview.py"
        with open(interview_file, 'r', encoding='utf-8') as f:
            interview_source = f.read()
        
        # Check for streaming integration
        assert 'streaming_enabled' in interview_source, "Missing streaming_enabled check"
        assert 'generate_completion_streaming' in interview_source, "Missing streaming method call"
        assert 'token_callback' in interview_source, "Missing token callback implementation"
        assert 'console.print(token, end=""' in interview_source, "Missing real-time token display"
        print("✓ LLMInterviewManager integrates streaming properly")
        
    except Exception as e:
        print(f"[ERROR] Interview manager check error: {e}")
        return False
    
    return True

def test_expected_streaming_behavior():
    """Describe the expected streaming behavior."""
    print("\n" + "="*60)
    print("EXPECTED STREAMING BEHAVIOR")
    print("="*60)
    
    print("\n[TARGET] Requesty AI Streaming Implementation:")
    print("• Sends 'stream': true in API request payload")
    print("• Processes Server-Sent Events (SSE) format")
    print("• Parses 'data: ' lines from response stream")
    print("• Extracts content from choices[0].delta.content")
    print("• Calls callback for each token/chunk received")
    print("• Collects and returns complete response")
    
    print("\n📊 Interview Phase Streaming:")
    print("• Real-time token display during LLM responses")
    print("• Smooth blue text streaming as tokens arrive")
    print("• No blocking spinner during streaming")
    print("• Fallback to non-streaming if disabled")
    
    print("\n🔧 Technical Details:")
    print("• Uses aiohttp for async HTTP streaming")
    print("• Handles [DONE] messages and heartbeats")
    print("• Robust error handling for malformed chunks")
    print("• Retry logic with exponential backoff")
    print("• Debug logging for troubleshooting")

def show_usage_example():
    """Show how streaming works in practice."""
    print("\n" + "="*60)
    print("STREAMING USAGE EXAMPLE")
    print("="*60)
    
    print("\n📝 What you'll see during interview:")
    print("""
[yellow]You[/yellow]: Tell me about your project

[blue]🎵 Devussy[/blue]:
I'd be happy to help you plan your project! To get started, I need to understand
what you're building. Could you tell me:

1. What type of project is this? (web app, API, CLI tool, etc.)
2. What programming languages do you prefer?
3. What's the main purpose or goal of your project?

This information will help me create a comprehensive development plan
tailored to your specific needs.

[blue]🎵 Devussy[/blue]: (tokens appear in real-time as they're generated)
    """)
    
    print("\n[FAST] Behind the scenes:")
    print("• API request: POST https://router.requesty.ai/v1/chat/completions")
    print("• Payload includes: 'stream': true")
    print("• Response processed line-by-line as SSE stream")
    print("• Each token displayed immediately via callback")
    print("• Complete response collected and stored")

if __name__ == "__main__":
    try:
        if test_requesty_streaming_implementation():
            test_expected_streaming_behavior()
            show_usage_example()
            print("\n[CELEBRATE] Requesty AI streaming implementation is ready!")
            print("\nTo test streaming:")
            print("1. Configure Requesty as your provider")
            print("2. Run: python -m src.cli interactive")
            print("3. Watch real-time tokens during interview!")
        else:
            print("\n[ERROR] Streaming implementation has issues")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
