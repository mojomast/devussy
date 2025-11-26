# 👋 START HERE - Next Agent

**Welcome!** You're inheriting a fully functional Devussy web frontend.

---

## 🔗 CRITICAL: Anchor-Based Context Management

> **⚠️ READ THIS FIRST** before diving into the codebase.

Devussy uses **stable HTML comment anchors** for efficient context management. See `AGENTS.md` for the complete guide.

**Quick rules:**
1. Read ONLY anchored sections (e.g., `<!-- NEXT_TASK_GROUP_START -->` to `<!-- NEXT_TASK_GROUP_END -->`), not entire files
2. Use `safe_write_devplan()` from `src/file_manager.py` for all devplan/phase file writes
3. Never remove anchor comments - they're required for validation

---

## 🎯 What You Need to Know

### Status: ✅ PRODUCTION READY

The application works end-to-end with real-time streaming. All critical bugs are fixed.

### Your Mission

Polish the application and add remaining features (GitHub, download, persistence).

### Time Estimate

2-5 days depending on scope.

---

## 📚 Read These Documents (In Order)

### 1. **QUICK_START.md** (2 minutes)
Start the application and verify it works.

### 2. **handoff.md** (15 minutes)
Complete context on what was done, adaptive pipeline implementation, and what needs doing.

### 3. **devplan.md** (10 minutes)
Detailed plan with phases, progress log, and next task group.

### 4. **README.md** (5 minutes)
Project documentation and architecture.

---

## 🚀 Quick Start

```bash
# Terminal 1 - Backend
python dev_server.py

# Terminal 2 - Frontend
cd devussy-web && npm run dev

# Browser
http://localhost:3000
```

---

## ✅ What's Working

- ✅ Interview → Design → Plan → Execute pipeline
- ✅ Real-time SSE streaming
- ✅ Multi-phase concurrent execution
- ✅ Editable phase cards
- ✅ Window management

---

## ⏳ What Needs Work

1. Remove debug logging (1 hour)
2. Test HandoffView (30 min)
3. Add error recovery UI (3 hours)
4. GitHub integration (4 hours)
5. Download zip (2 hours)
6. Project persistence (4 hours)

---

## 🎯 Recommended Approach

### Day 1: Polish
- Remove debug logging
- Test HandoffView
- Add error recovery
- Improve UX

### Day 2: Features
- GitHub integration
- Download zip
- Start persistence

### Day 3: Testing & Deploy
- Comprehensive testing
- Documentation updates
- Deploy to production

---

## 📞 Need Help?

### Check These First
- Browser console (F12)
- Backend console
- `handoff.md` - Detailed technical info and milestone progress
- `AGENTS.md` - Anchor-based context management guide

### Key Files
- `src/components/pipeline/ExecutionView.tsx` - Execution phase
- `src/components/pipeline/PlanView.tsx` - Plan editing
- `devussy-web/api/plan/detail.py` - Phase generation API
- `src/pipeline/detailed_devplan.py` - Streaming implementation

---

## 💡 Pro Tips

1. **Test after every change** - Run full pipeline
2. **Don't break streaming** - It's the core feature
3. **Use functional state updates** - `setState(prev => ...)`
4. **Keep SSE format correct** - `\n\n` not `\\n\\n`
5. **Check both consoles** - Browser and backend

---

## 🎉 You Got This!

The hard work is done. The foundation is solid. Everything works.

Now make it shine! ✨

---

**Next Steps**:
1. Read handoff.md (especially Milestone 5 for latest updates)
2. Read devplan.md (check `<!-- NEXT_TASK_GROUP_START -->` section)
3. Start with Frontend Phase 2 (ComplexityAssessment.tsx)

**Good luck!** 🚀
