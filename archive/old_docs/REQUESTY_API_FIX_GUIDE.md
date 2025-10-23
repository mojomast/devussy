# 🔧 Requesty API Integration Fix Guide

**Created:** October 22, 2025  
**Priority:** 🚨 CRITICAL  
**Issue:** 400 Bad Request from Requesty API - all projects failing

---

## 🎯 Quick Summary

**Problem:** All projects fail immediately with `400 Bad Request` from `https://router.requesty.ai/v1/chat/completions`

**Root Cause:** Likely model name format issue - Requesty requires `provider/model` format

**Solution:** Add verbose logging, validate model format, improve error handling

**User Request:** "I want there to be a verbose console section below live logs that shows me the exact api requests and responses please."

---

## 📚 Requesty API Requirements

### From https://docs.requesty.ai/quickstart

**Base URL:**
```
https://router.requesty.ai/v1
```

**Authentication:**
```
Authorization: Bearer {YOUR_API_KEY}
```

**Model Format (CRITICAL):**
```
✅ CORRECT: "openai/gpt-4o"
✅ CORRECT: "anthropic/claude-3-5-sonnet"
✅ CORRECT: "google/gemini-pro"

❌ WRONG: "gpt-4o" (missing provider/)
❌ WRONG: "claude-3-5-sonnet" (missing provider/)
```

**Recommended Headers (Optional but improves analytics):**
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://devussy.app",
    "X-Title": "DevUssY"
}
```

**Request Format (OpenAI-compatible):**
```json
{
  "model": "openai/gpt-4o",
  "messages": [
    {"role": "user", "content": "Your prompt here"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

---

## 🔍 Diagnostic Steps

### Step 1: Check Current Model Configuration

**File:** `config/config.yaml`

```bash
# In PowerShell:
Get-Content config\config.yaml | Select-String "model:"
```

**Look for:**
- Is the model field present?
- Does it have the `provider/` prefix?
- Example: `model: openai/gpt-4o-mini` ✅

**If wrong:**
```yaml
llm:
  provider: requesty
  model: openai/gpt-4o-mini  # ← Add this if missing
```

### Step 2: Check User Credentials

**Files:** `web_projects/.config/credentials/*.json`

```powershell
# List all credentials:
Get-ChildItem web_projects\.config\credentials\*.json | ForEach-Object {
    $cred = Get-Content $_.FullName | ConvertFrom-Json
    Write-Host "$($_.Name): Provider=$($cred.provider), Model=$($cred.model)"
}
```

**Look for:**
- Do model fields have `provider/` prefix?
- If not, need to add validation

### Step 3: Enable Verbose Logging

**Quick test before implementing full solution:**

**File:** `src/clients/requesty_client.py`

Add at line 61 (in `_post_chat` method, before the API call):

```python
# TEMPORARY DEBUG LOGGING
import json
print("\n" + "="*80)
print("[REQUESTY DEBUG] Making API call")
print(f"Endpoint: {self._endpoint}")
print(f"Model: {model}")
print(f"Headers: {json.dumps(headers, indent=2)}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("="*80 + "\n")
```

Add after the API call (line 73):

```python
# TEMPORARY DEBUG LOGGING
print("\n" + "="*80)
print(f"[REQUESTY DEBUG] Response status: {resp.status}")
if resp.status >= 400:
    error_text = await resp.text()
    print(f"[REQUESTY ERROR] Response body: {error_text}")
    print("="*80 + "\n")
    raise Exception(f"Requesty API error {resp.status}: {error_text}")
print("="*80 + "\n")
```

**Test:**
1. Restart backend: `python -m uvicorn src.web.app:app --reload`
2. Create a test project
3. Watch backend terminal for debug output
4. You'll see EXACTLY what's being sent and what error Requesty returns

---

## 🔧 Implementation Plan

### Task 1: Add Model Format Validation

**File:** `src/clients/requesty_client.py`

In `_post_chat` method, add validation:

```python
async def _post_chat(self, prompt: str, **kwargs: Any) -> str:
    """Post to OpenAI-compatible chat completions endpoint."""
    model = kwargs.get("model", self._model)
    
    # VALIDATE MODEL FORMAT
    if "/" not in model:
        raise ValueError(
            f"Invalid model format for Requesty: '{model}'. "
            f"Must use provider/model format (e.g., 'openai/gpt-4o'). "
            f"See https://docs.requesty.ai/models for available models."
        )
    
    temperature = kwargs.get("temperature", self._temperature)
    # ... rest of method
```

### Task 2: Add Recommended Headers

**File:** `src/clients/requesty_client.py`

Update headers dict:

```python
headers = {
    "Authorization": f"Bearer {self._api_key}" if self._api_key else "",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://devussy.app",  # Improves analytics
    "X-Title": "DevUssY",  # Improves analytics
}
```

### Task 3: Improve Error Handling

**File:** `src/clients/requesty_client.py`

Replace `resp.raise_for_status()` with:

```python
async with session.post(
    self._endpoint, json=payload, headers=headers
) as resp:
    if resp.status >= 400:
        error_body = await resp.text()
        raise Exception(
            f"Requesty API error {resp.status}: {error_body}\n"
            f"Request: {json.dumps(payload, indent=2)}"
        )
    
    data = await resp.json()
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
```

### Task 4: Add API Logging to Backend

**File:** `src/web/project_manager.py`

In `_run_current_stage` method, after LLM call:

```python
# Log API request/response for debugging
api_log_file = Path(project.output_dir) / "api_log.jsonl"
log_entry = {
    "timestamp": datetime.utcnow().isoformat(),
    "stage": project.current_stage.value,
    "model": config.llm.model,
    "request": {
        "prompt_length": len(prompt),
        "model": config.llm.model,
        "temperature": config.llm.temperature,
    },
    "response": {
        "success": True,
        "content_length": len(response),
    }
}

with open(api_log_file, "a") as f:
    f.write(json.dumps(log_entry) + "\n")

# Emit to frontend via WebSocket
await self._emit_websocket(project.id, {
    "type": "api_log",
    "data": log_entry
})
```

### Task 5: Add Verbose Console UI

**File:** `frontend/src/pages/ProjectDetailPage.tsx`

Add state:

```typescript
const [apiLogs, setApiLogs] = useState<Array<{
  timestamp: string;
  stage: string;
  model: string;
  request: any;
  response?: any;
  error?: string;
}>>([]);
```

Add WebSocket handler in `useEffect`:

```typescript
case 'api_log':
  setApiLogs(prev => [...prev, message.data]);
  break;
```

Add UI section (after Live Logs):

```tsx
{/* API Console (Verbose) */}
<div className="bg-gray-900 dark:bg-gray-950 rounded-lg p-4">
  <h3 className="text-lg font-semibold mb-3 text-white flex items-center gap-2">
    <span>🔍</span>
    API Console (Verbose)
  </h3>
  
  {apiLogs.length === 0 ? (
    <p className="text-gray-400 text-sm">No API calls yet...</p>
  ) : (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {apiLogs.map((log, i) => (
        <div key={i} className="border-l-4 border-blue-500 pl-3 py-2">
          <div className="text-gray-400 text-xs mb-1">
            [{new Date(log.timestamp).toLocaleTimeString()}] Stage: {log.stage}
          </div>
          <div className="text-green-400 text-sm font-semibold mb-2">
            ✅ Model: {log.model}
          </div>
          
          {/* Request */}
          <details className="mb-2">
            <summary className="text-blue-300 text-sm cursor-pointer hover:text-blue-200">
              📤 Request
            </summary>
            <pre className="text-gray-300 text-xs mt-1 ml-4 overflow-x-auto">
              {JSON.stringify(log.request, null, 2)}
            </pre>
          </details>
          
          {/* Response */}
          {log.response && (
            <details>
              <summary className="text-green-300 text-sm cursor-pointer hover:text-green-200">
                📥 Response
              </summary>
              <pre className="text-gray-300 text-xs mt-1 ml-4 overflow-x-auto">
                {JSON.stringify(log.response, null, 2)}
              </pre>
            </details>
          )}
          
          {/* Error */}
          {log.error && (
            <div className="text-red-400 text-sm mt-2">
              ❌ Error: {log.error}
            </div>
          )}
        </div>
      ))}
    </div>
  )}
</div>
```

### Task 6: Add Help Text in UI

**File:** `frontend/src/pages/CreateProjectPage.tsx`

After model input field:

```tsx
<input
  type="text"
  value={formData.model}
  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
  className="mt-1 block w-full rounded-md border-gray-300 bg-white dark:bg-gray-700 dark:border-gray-600"
  placeholder="e.g., openai/gpt-4o-mini"
/>
<p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
  For Requesty: use <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">provider/model</code> format
  (e.g., <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">openai/gpt-4o</code>)
  <a 
    href="https://docs.requesty.ai/models" 
    target="_blank" 
    rel="noopener noreferrer"
    className="text-blue-500 hover:text-blue-600 ml-1"
  >
    View available models →
  </a>
</p>
```

---

## ✅ Testing Checklist

### Before Fix:
- [x] Projects fail with 400 error ❌
- [x] No visibility into API requests ❌
- [x] User cannot debug issues ❌

### After Fix:
- [ ] Projects complete Design stage successfully ✅
- [ ] Verbose console shows exact request/response ✅
- [ ] Model format validated before API call ✅
- [ ] Clear error messages when format is wrong ✅
- [ ] Help text guides users to correct format ✅

### Test Cases:

**Test 1: Valid Model Format**
```
Model: openai/gpt-4o-mini
Expected: ✅ Success, Design file generated
```

**Test 2: Invalid Model Format (No Prefix)**
```
Model: gpt-4o-mini
Expected: ❌ Clear error: "Must use provider/model format"
```

**Test 3: Non-Existent Model**
```
Model: fake/nonexistent-model
Expected: ❌ Requesty error displayed in verbose console
```

**Test 4: Verbose Console**
```
Action: Create project
Expected: See request/response in UI with:
  - Timestamp
  - Model used
  - Request payload (collapsed)
  - Response (collapsed)
  - Any errors
```

---

## 🎓 Key Learnings for Next Agent

1. **Always read API docs first** - Requesty docs clearly state model format requirement
2. **Verbose logging is critical** - Cannot debug API issues without seeing requests
3. **User experience matters** - Help text prevents common mistakes
4. **Error messages should be actionable** - Tell users HOW to fix the issue
5. **Model format is the likely culprit** - Requesty is strict about `provider/model` format

---

## 📞 Quick Reference

**Requesty Docs:** https://docs.requesty.ai/quickstart  
**Available Models:** https://docs.requesty.ai/models  
**Example Model Names:**
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `anthropic/claude-3-5-sonnet`
- `anthropic/claude-3-5-haiku`
- `google/gemini-pro`

**Common Errors:**
- `400 Bad Request` → Usually model format or invalid parameters
- `401 Unauthorized` → Invalid API key
- `404 Not Found` → Model doesn't exist
- `429 Too Many Requests` → Rate limit hit

---

**Good luck! This should be a quick fix once you add the logging and see what's wrong! 🚀**
