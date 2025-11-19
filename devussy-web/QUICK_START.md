# Devussy Frontend - Quick Start Guide

**Status**: ✅ Fully Functional  
**Time to Run**: 2 minutes

---

## 🚀 Start in 3 Steps

### 1. Start Backend (Terminal 1)
```bash
cd C:\Users\kyle\projects\devussy03\devussy-testing
python dev_server.py
```

Wait for: `Starting Python API server on port 8000...`

### 2. Start Frontend (Terminal 2)
```bash
cd C:\Users\kyle\projects\devussy03\devussy-testing\devussy-web
npm run dev
```

Wait for: `Ready on http://localhost:3000`

### 3. Open Browser
```
http://localhost:3000
```

---

## 🎯 Quick Test

1. **Interview** - Answer a few questions
2. **Design** - Wait for streaming, click "Approve & Plan"
3. **Plan** - Verify cards show full content, click "Approve & Start Execution"
4. **Execute** - Watch phases stream in real-time!

---

## ✅ What to Expect

### Backend Console
```
[detail.py] Received request for phase 1
[detailed_devplan] Using streaming for phase 1
[detail.py] Streamed 50 tokens so far...
[detail.py] Phase 1 generation complete, got 16 steps
```

### Browser Console (F12)
```
[executePhase] Starting phase 1
[executePhase] Phase 1: Content #1: Starting...
[executePhase] Phase 1: Content #2: ## Step 1.1...
[executePhase] Phase 1 done signal received
```

### UI
- ✅ Terminal output streams in real-time
- ✅ Multiple phases run concurrently
- ✅ Green checkmarks when complete
- ✅ Progress counter updates

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.9+

# Install dependencies
pip install -e .
```

### Frontend Won't Start
```bash
# Install dependencies
npm install

# Clear cache
rm -rf .next
npm run dev
```

### No Streaming Output
1. Check both servers are running
2. Refresh browser (Ctrl+R)
3. Check browser console for errors
4. Verify backend shows "Using streaming"

---

## 📚 More Info

- **Full Documentation**: `README.md`
- **Complete Handoff**: `SESSION_HANDOFF.md`
- **Status Report**: `FINAL_STATUS.md`

---

## 🎉 That's It!

You should now see the full pipeline working with real-time streaming.

**Enjoy!** 🚀
