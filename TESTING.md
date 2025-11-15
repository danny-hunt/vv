# VV Testing Guide

This document outlines the testing strategy and test cases for the VV multi-version dev tool.

## Testing Strategy

VV is a complex system with multiple components:

1. **Backend API** (Python/FastAPI)
2. **Frontend UI** (React/TypeScript)
3. **Git Operations** (GitPython)
4. **Agent Integration** (cursor-agent CLI)
5. **AI Integration** (Google Gemini)

## Prerequisites for Testing

- All 6 webapp directories (1-6) must be git repositories with a `main` branch
- Backend server running on port 8000
- Frontend dev server running on port 5173
- All 6 webapps running on ports 3001-3006
- cursor-agent CLI available in PATH
- Gemini API key configured

## Unit Testing (Future)

While not currently implemented, these components should have unit tests:

### Backend Tests

- `test_git_ops.py` - Test git operations in isolation
- `test_agent.py` - Test agent manager with mocked subprocess
- `test_main.py` - Test API endpoints with TestClient

### Frontend Tests

- `api.test.ts` - Test API client functions
- `usePolling.test.ts` - Test polling hook
- `useAgentStream.test.ts` - Test SSE hook
- Component tests for Tile, TileGrid, FloatingWindow

## Integration Testing

### Test Suite 1: Basic Pane Operations

#### Test 1.1: Create First Pane

**Steps:**

1. Open VV in browser
2. Click the `+` button
3. Wait for initialization

**Expected Results:**

- Pane appears in the grid
- Backend creates branch `tmp-1-XXXXXX`
- Iframe loads `http://localhost:3001`
- Floating window shows "Pane 1"
- Status badge shows "Pane 1"

**Verification:**

```bash
cd 1
git branch
# Should show tmp-1-XXXXXX
```

#### Test 1.2: Create Multiple Panes

**Steps:**

1. Start with one pane
2. Click `+` to add panes until you have 6
3. Observe grid layout changes

**Expected Results:**

- Grid layout adapts: 1→1x1, 2→2x1, 3-4→2x2, 5-6→3x2
- Each pane has unique ID
- Each pane loads correct port (3001-3006)
- All floating windows are accessible

#### Test 1.3: Remove Pane

**Steps:**

1. Create 2+ panes
2. Click `X` button
3. Verify last pane is removed

**Expected Results:**

- Pane disappears from grid
- Backend resets pane to main branch
- `X` button disappears if only 1 pane remains
- Grid layout adjusts

**Verification:**

```bash
cd 6  # or whichever was removed
git branch
# Should show * main
```

### Test Suite 2: Agent Workflow

#### Test 2.1: Submit First Prompt

**Steps:**

1. Create a pane
2. Type a prompt in floating window: "Add a comment to the main file"
3. Click Submit

**Expected Results:**

- Title generates automatically (e.g., "Add Comment")
- Prompt textarea is disabled during agent run
- "Agent Running" badge appears
- Agent output streams to floating window
- Submit button shows "Agent Running..."

#### Test 2.2: Stream Agent Output

**Steps:**

1. Submit a prompt
2. Watch the streaming output

**Expected Results:**

- Output appears line by line in real-time
- Scroll area auto-scrolls to bottom
- No lag or frozen UI
- "Agent Running" badge stays visible

#### Test 2.3: Agent Completion

**Steps:**

1. Wait for agent to complete
2. Observe final state

**Expected Results:**

- "Agent Running" badge disappears
- Submit button becomes enabled
- If changes were made: "Ahead" badge appears
- Prompt can be submitted again

#### Test 2.4: Multiple Agents

**Steps:**

1. Create 3 panes
2. Submit prompts to all 3 simultaneously
3. Observe behavior

**Expected Results:**

- All 3 agents run independently
- Streaming works for all
- Each has its own title
- No interference between panes

### Test Suite 3: Git Status Tracking

#### Test 3.1: Ahead Status

**Steps:**

1. Create a pane
2. Run agent that makes changes
3. Wait for completion

**Expected Results:**

- "Ahead" badge appears
- Merge button becomes visible
- Polling continues updating status

**Verification:**

```bash
cd 1
git log --oneline main..HEAD
# Should show commits not in main
```

#### Test 3.2: Stale Status

**Steps:**

1. Create a pane
2. In another terminal, push changes to main
3. Wait 5-10 seconds for polling

**Expected Results:**

- "Stale" badge appears
- Grey overlay appears on pane
- Pane still functional

**Verification:**

```bash
cd 1
git log --oneline HEAD..origin/main
# Should show commits in main not in branch
```

#### Test 3.3: Ahead AND Stale

**Steps:**

1. Create pane and make changes (Ahead)
2. Push changes to main from elsewhere (Stale)
3. Wait for polling

**Expected Results:**

- Both "Ahead" and "Stale" badges visible
- Merge button still shown
- Grey overlay present

### Test Suite 4: Merge Operations

#### Test 4.1: Single Merge

**Steps:**

1. Create pane with changes (Ahead)
2. Click "Merge" button
3. Observe merge process

**Expected Results:**

- Merge queue indicator appears bottom-right
- Shows "⏳ Pane 1" while merging
- After completion:
  - "Ahead" badge disappears
  - Pane returns to main branch
  - Merge queue indicator disappears

**Verification:**

```bash
cd 1
git branch
# Should show * main
git log --oneline -3
# Should show merged commits
```

#### Test 4.2: Multiple Merges (Sequential)

**Steps:**

1. Create 3 panes with changes
2. Click "Merge" on all 3
3. Observe queue processing

**Expected Results:**

- Merge queue shows all 3 panes
- First shows ⏳ (processing)
- Others show ⏸️ (queued)
- Processes one at a time
- Queue empties sequentially

#### Test 4.3: Cannot Remove During Merge

**Steps:**

1. Start a merge
2. Try to click `X` button

**Expected Results:**

- `X` button is disabled
- Cannot remove pane until merge completes
- Queue continues processing

#### Test 4.4: Cannot Merge During Agent

**Steps:**

1. Start an agent run
2. Try to click "Merge" button

**Expected Results:**

- "Merge" button should not appear
- Or be disabled if it does appear
- Can merge after agent completes

### Test Suite 5: Error Handling

#### Test 5.1: Backend Connection Error

**Steps:**

1. Stop backend server
2. Refresh frontend

**Expected Results:**

- Error message displayed
- Shows "Error connecting to backend"
- Shows specific error message
- No broken UI

#### Test 5.2: Git Operation Error

**Steps:**

1. Manually corrupt git repository
2. Try to create pane

**Expected Results:**

- Backend returns error
- Frontend shows error message
- Other panes continue working

#### Test 5.3: Agent Not Found

**Steps:**

1. Temporarily remove cursor-agent from PATH
2. Try to submit prompt

**Expected Results:**

- Error message about cursor-agent
- Agent doesn't start
- UI returns to ready state

#### Test 5.4: Merge Conflict

**Steps:**

1. Create scenario with merge conflict
2. Attempt merge

**Expected Results:**

- Merge fails (expected behavior)
- Error shown in logs
- Pane removed from queue
- Other merges continue

### Test Suite 6: UI/UX Testing

#### Test 6.1: Window Collapse/Expand

**Steps:**

1. Click on floating window header
2. Click again to expand

**Expected Results:**

- Window collapses smoothly
- Content hidden when collapsed
- State persists until clicked
- No layout issues

#### Test 6.2: Title Generation

**Steps:**

1. Submit various prompts
2. Observe generated titles

**Test Cases:**

- "Add a login button" → "Add Login" or similar
- "Fix the navbar styling issues" → "Fix Navbar" or similar
- "Create dashboard" → "Create Dashboard"

**Expected Results:**

- Titles are short (3-5 words)
- Titles are relevant to prompt
- Generated within 1-2 seconds
- Fallback works if Gemini fails

#### Test 6.3: Responsive Grid

**Steps:**

1. Add panes and observe layout
2. Resize browser window

**Expected Results:**

- 1 pane: Full screen
- 2 panes: Side by side
- 3-4 panes: 2x2 grid
- 5-6 panes: 3x2 grid
- No overflow or broken layouts

#### Test 6.4: Badge Visibility

**Steps:**

1. Test all badge combinations

**Expected Results:**

- All badges are readable
- Colors are distinct
- No overlapping
- Visible over various iframe backgrounds

### Test Suite 7: Performance Testing

#### Test 7.1: Polling Performance

**Steps:**

1. Create 6 panes
2. Monitor network tab
3. Observe for 1 minute

**Expected Results:**

- Polls every 5 seconds
- Minimal payload size
- No memory leaks
- No dropped polls

#### Test 7.2: Streaming Performance

**Steps:**

1. Run agents with large outputs
2. Monitor performance

**Expected Results:**

- Smooth scrolling
- No UI freezing
- Messages appear promptly
- Memory usage stable

#### Test 7.3: Multiple Iframes

**Steps:**

1. Load all 6 panes
2. Interact with various iframes

**Expected Results:**

- All iframes responsive
- No significant lag
- Browser doesn't slow down
- Reasonable memory usage

## Manual Test Checklist

Before considering VV ready for use, verify:

- [ ] Backend starts without errors
- [ ] Frontend compiles and starts
- [ ] Can create first pane
- [ ] Can create up to 6 panes
- [ ] Can remove panes (when allowed)
- [ ] Agent prompt submission works
- [ ] Agent output streams correctly
- [ ] Title generation works
- [ ] Ahead detection works
- [ ] Stale detection works
- [ ] Merge button appears when ahead
- [ ] Single merge completes successfully
- [ ] Multiple merges queue correctly
- [ ] Cannot remove during merge
- [ ] Cannot merge during agent
- [ ] Window collapse/expand works
- [ ] Grid layout adapts correctly
- [ ] All badges display correctly
- [ ] Polling continues reliably

## Known Limitations

1. **No Conflict Resolution**: Merges with conflicts will fail
2. **No Agent Cancellation**: Cannot stop a running agent mid-execution
3. **No Persistence**: Pane state lost on refresh
4. **No Error Recovery**: Some errors require manual git cleanup

## Future Testing Improvements

1. Add automated backend API tests with pytest
2. Add frontend component tests with Vitest
3. Add E2E tests with Playwright
4. Add git operation tests with test fixtures
5. Mock cursor-agent for consistent testing
6. Add performance benchmarks
7. Add load testing for concurrent operations

## Debugging Tips

### Backend Issues

```bash
# Check logs
tail -f backend.log

# Test endpoints manually
curl http://localhost:8000/api/orchestration | jq

# Check git state
for i in {1..6}; do
  echo "=== Pane $i ==="
  cd $i && git status && git branch && cd ..
done
```

### Frontend Issues

```javascript
// Open browser console
// Check for errors
// Monitor network tab for failed requests
// Check React DevTools for component state
```

### Git Issues

```bash
# Reset a pane manually
cd 1
git reset --hard origin/main
git checkout main
git clean -fd
```

## Test Results Template

```
Test Date: ___________
Tester: ___________
Environment: ___________

| Test Suite | Test Case | Status | Notes |
|------------|-----------|--------|-------|
| Suite 1 | 1.1 | PASS/FAIL | |
| Suite 1 | 1.2 | PASS/FAIL | |
...
```

## Reporting Issues

When reporting issues, include:

1. Test case number
2. Steps to reproduce
3. Expected vs actual behavior
4. Backend logs
5. Browser console logs
6. Git state (`git status`, `git branch`)
7. Screenshots if UI related
