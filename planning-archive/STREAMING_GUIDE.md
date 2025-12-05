# Devussy Streaming Guide

This guide explains Devussy's phase-specific streaming features, helping you optimize your development workflow with real-time token streaming.

## Overview

Devussy's streaming system allows you to control how LLM responses are displayed during each phase of the development pipeline. Instead of waiting for complete responses, streaming shows tokens as they're generated, providing immediate feedback and reducing perceived waiting time.

## Phase-Specific Streaming

### What is Streaming?

**Streaming** means that instead of waiting for the complete LLM response, tokens (pieces of text) are displayed in real-time as they're generated. This provides:

- **Immediate feedback** - See progress immediately
- **Reduced perceived waiting time** - Content appears progressively
- **Better user experience** - Know the system is working
- **Early interruption capability** - Stop generation if needed

### The Three Phases

Devussy operates in three distinct phases, each with different characteristics:

#### 1. Design Phase
**Purpose**: Create initial project architecture and planning
**Generates**: Architecture overview, technology stack, objectives, dependencies

**Streaming Benefits**: ✅ **Highly Recommended**
- Fast generation (typically 30-90 seconds)
- Immediate feedback builds confidence
- Helps catch issues early in the process

**When to Enable**: Always recommended for better UX

#### 2. DevPlan Phase  
**Purpose**: Develop structured development roadmap
**Generates**: Phase-based structure, detailed steps, dependencies, timelines

**Streaming Benefits**: ⚖️ **User Preference**
- Variable generation time (can be 2-10+ minutes)
- Good for monitoring progress on long generations
- May impact performance slightly

**When to Enable**: 
- Enable if you want to monitor long-running generations
- Disable if you prefer faster batch processing

#### 3. Handoff Phase
**Purpose**: Create final documentation bundle
**Generates**: Comprehensive handoff document, next steps, context preservation

**Streaming Benefits**: ✅ **Recommended**
- Typically fast generation (1-3 minutes)
- Provides closure feedback
- Good for final review process

**When to Enable**: Generally recommended

## Configuration Methods

### Method 1: Interactive Settings Menu

1. Start Devussy and navigate to **Modify Options**
2. Select **Streaming Options**
3. Configure each phase individually:
   - Design Phase Streaming
   - DevPlan Phase Streaming
   - Handoff Phase Streaming
   - Global Streaming (affects all phases)

### Method 2: Environment Variables

```bash
# Enable streaming for all phases
export STREAMING_ENABLED=true

# Phase-specific control (overrides global setting)
export STREAMING_DESIGN_ENABLED=true
export STREAMING_DEVPLAN_ENABLED=false
export STREAMING_HANDOFF_ENABLED=true

# Run Devussy with these settings
python -m src.cli interactive
```

### Method 3: Configuration File

Edit `config/config.yaml`:

```yaml
# Global streaming setting
streaming_enabled: false

# Note: Phase-specific settings are configured via settings menu or environment variables
```

## Streaming Priority System

Devussy uses a smart fallback system to determine if streaming is enabled:

### Priority Order
1. **Phase-specific setting** (if explicitly configured)
2. **Global streaming setting** (fallback)
3. **Config file setting** (fallback)
4. **Disabled** (default)

### Example Scenarios

**Scenario 1: All disabled by default**
```
Phase-specific: Not set
Global setting: Not set
Config file: false
Result: All phases use streaming = false
```

**Scenario 2: Global enabled, phases unspecified**
```
Phase-specific: Not set
Global setting: true
Config file: false
Result: All phases use streaming = true
```

**Scenario 3: Mixed settings**
```
Phase-specific: Design=true, DevPlan=false, Handoff=not set
Global setting: true
Config file: false
Result: Design=true, DevPlan=false, Handoff=true (falls back to global)
```

## Performance Considerations

### Streaming vs. Non-Streaming

| Aspect | Streaming Enabled | Streaming Disabled |
|--------|------------------|-------------------|
| **User Experience** | Real-time feedback | Wait for completion |
| **Perceived Speed** | Faster | Slower |
| **Actual Speed** | Slightly slower | Slightly faster |
| **Interruption** | Can stop mid-generation | Must wait for complete response |
| **Resource Usage** | Slightly higher | Slightly lower |

### Recommendations by Use Case

#### Development/Prototyping
```yaml
Design: Enabled  # Quick feedback
DevPlan: Enabled  # Monitor long generations
Handoff: Enabled  # Final verification
```

#### Production/Automated
```yaml
Design: Enabled  # Still valuable
DevPlan: Disabled  # Faster batch processing
Handoff: Enabled  # Final checks
```

#### Testing/Debugging
```yaml
Design: Enabled  # See what's happening
DevPlan: Enabled  # Monitor issues
Handoff: Enabled  # Verify outputs
```

## Troubleshooting

### Common Issues

#### Issue 1: Streaming Not Working
**Symptoms**: No real-time token display, only complete responses

**Solutions**:
1. Check phase-specific settings in **Settings → Streaming Options**
2. Verify environment variables are set correctly
3. Ensure your terminal supports ANSI escape codes
4. Check that the LLM provider supports streaming

#### Issue 2: Streaming Too Slow
**Symptoms**: Tokens appear very slowly, performance issues

**Solutions**:
1. Disable streaming for the DevPlan phase (longest generation)
2. Reduce `max_concurrent_requests` in settings
3. Check network connectivity to LLM provider
4. Consider switching to a faster model

#### Issue 3: Interrupted Streaming
**Symptoms**: Streaming stops unexpectedly, incomplete responses

**Solutions**:
1. Check for network interruptions
2. Verify API key has sufficient quota
3. Increase API timeout settings
4. Check LLM provider status

#### Issue 4: Settings Not Persisting
**Symptoms**: Streaming settings reset between sessions

**Solutions**:
1. Settings are saved in `.devussy_state/ui_prefs`
2. Environment variables persist across sessions
3. Check file permissions for state directory

### Performance Optimization

#### For Faster Generation
1. **Disable streaming** for the DevPlan phase
2. **Use faster models** like `gpt-4o-mini`
3. **Reduce max_tokens** if appropriate
4. **Increase concurrency** for parallel processing

#### For Better UX
1. **Enable streaming** for Design and Handoff phases
2. **Use descriptive prefixes** to identify streaming content
3. **Monitor token usage** to understand costs
4. **Set appropriate timeouts** to avoid premature termination

### Provider-Specific Notes

#### OpenAI
- Supports native streaming via Server-Sent Events
- Most reliable streaming experience
- Check model-specific streaming support

#### Generic/OpenAI-Compatible
- Streaming support depends on provider implementation
- May fall back to simulated streaming
- Check provider documentation

#### Requesty
- Supports streaming for most models
- Good for testing streaming functionality
- Aggregates multiple providers

#### Aether AI
- Supports streaming with recent models
- May have different performance characteristics
- Check model compatibility

#### AgentRouter
- Streaming support varies by underlying model
- Performance depends on selected model
- Test streaming with your chosen model

## Advanced Usage

### Custom Streaming Handlers

Devussy supports custom streaming handlers for specialized use cases:

```python
from src.streaming import StreamingHandler

# Create custom handler
handler = StreamingHandler(
    enable_console=True,
    log_file=Path("streaming.log"),
    prefix="[CUSTOM] ",
    flush_interval=0.1
)

# Use with LLM client
client = OpenAIClient(config)
await client.generate_completion_streaming(prompt, handler.create_async_callback())
```

### Monitoring and Logging

Enable detailed streaming logs:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with streaming
python -m src.cli interactive
```

Logs will show:
- Token streaming events
- Phase transitions
- Performance metrics
- Error conditions

### Integration with External Tools

Streaming output can be integrated with external monitoring tools:

```bash
# Pipe streaming to external monitor
python -m src.cli interactive 2>&1 | tee streaming_output.log

# Monitor in real-time
tail -f streaming_output.log | grep -E "\[design\]|\[devplan\]|\[handoff\]"
```

## Best Practices

### General Guidelines

1. **Start with defaults** and adjust based on experience
2. **Test streaming** with simple projects first
3. **Monitor performance** and adjust as needed
4. **Use appropriate timeouts** for your network conditions
5. **Check provider limits** and quotas regularly

### Phase-Specific Recommendations

#### Design Phase
- ✅ **Always enable** - Fast and valuable feedback
- Monitor for early issues
- Use for validation before proceeding

#### DevPlan Phase  
- ⚖️ **User preference** - Enable if you like monitoring progress
- Disable for faster batch processing
- Useful for long-running generations

#### Handoff Phase
- ✅ **Generally enable** - Provides closure feedback
- Important for final verification
- Typically fast enough that impact is minimal

### Performance Monitoring

Track these metrics:

- **Generation time** per phase
- **Token throughput** (tokens/second)
- **Streaming latency** (delay before first token)
- **Completion rate** (successful vs. failed generations)
- **Resource usage** (CPU, memory, network)

## Conclusion

Devussy's phase-specific streaming gives you fine-grained control over the development experience. By understanding the characteristics of each phase and using the appropriate streaming settings, you can optimize both performance and user experience for your specific workflow.

Remember: streaming is a tool to enhance your development process, not a requirement. Experiment with different configurations to find what works best for your projects and preferences.

For more information, see:
- [README.md](README.md) - Main project documentation
- [Configuration Guide](config/config.yaml) - Configuration options
- [Troubleshooting Guide](#troubleshooting) - Common issues and solutions