# Merge Conflict Resolution Testing Guide

This guide describes how to test the automatic merge conflict resolution feature.

## Overview

The system now automatically detects merge conflicts during the merge operation and invokes cursor-agent to resolve them. If successful, the merge completes automatically. If the agent fails, the merge is aborted and the pane is reset to a clean state.

## Testing Prerequisites

1. Backend and frontend servers running
2. cursor-agent CLI available in PATH
3. At least 2 webapp instances (panes) set up

## Test Scenario 1: Simple Conflict Resolution

### Setup

1. Create Pane 1 and make changes to a file (e.g., `src/App.css`)
2. Merge Pane 1 to main
3. Create Pane 2 and make **different** changes to the same file (`src/App.css`)
4. Attempt to merge Pane 2

### Expected Behavior

- Merge operation detects conflict
- System logs show: `[MERGE QUEUE] Conflict detected for pane 2, attempting automatic resolution`
- cursor-agent is invoked with conflict resolution prompt
- Agent resolves the conflict
- Merge completes automatically
- Pane 2 returns to main branch

### Verification Commands

```bash
# Check backend logs for conflict detection and resolution
tail -f backend_logs.txt | grep "CONFLICT\|Conflict detected\|Agent successfully resolved"

# Check git status in pane directory
cd 2
git status  # Should show clean working tree on main branch
git log --oneline -3  # Should show merge commit
```

## Test Scenario 2: Agent Fails to Resolve Conflict

### Setup

1. Create a complex conflict that's difficult to resolve automatically
2. Or simulate agent failure by temporarily moving cursor-agent binary

### Expected Behavior

- Merge operation detects conflict
- cursor-agent attempts resolution
- Agent fails or exits with error
- System logs show: `[MERGE QUEUE] Agent failed to resolve conflicts`
- Merge is aborted with `git merge --abort`
- Repository is reset to clean state
- Pane remains on its feature branch (not on main)

### Verification Commands

```bash
# Check backend logs
tail -f backend_logs.txt | grep "Agent failed\|Aborting merge"

# Check git status
cd 2
git status  # Should show clean working tree on feature branch
git branch  # Should show still on tmp-2-xxxxx branch
```

## Test Scenario 3: Multiple Files in Conflict

### Setup

1. Create changes in multiple files across two panes
2. Merge first pane
3. Attempt to merge second pane with overlapping changes

### Expected Behavior

- Conflict detected in multiple files
- Agent receives list of all conflicted files
- Agent resolves all conflicts
- All files are staged and committed
- Merge completes successfully

## Monitoring

### Backend Logs

Key log messages to watch for:

- `[MERGE QUEUE] Conflict detected for pane X`
- `[MERGE QUEUE] Invoking agent to resolve conflicts`
- `[Pane X] Starting conflict resolution with agent`
- `[Pane X] Agent successfully resolved conflicts`
- `[MERGE QUEUE] Merge completed successfully`

Or for failures:

- `[MERGE QUEUE] Agent failed to resolve conflicts`
- `[MERGE QUEUE] Aborting merge`
- `[MERGE QUEUE] Successfully aborted merge`

### Frontend

- Merge queue indicator should show pane being processed
- After resolution, pane should return to main branch
- No "Ahead" or "Stale" badges should remain

## Manual Testing Steps

### Step 1: Create Conflict

```bash
# Terminal 1 - Pane 1
cd 1
echo ".test { color: red; }" >> src/App.css
# Use UI to merge pane 1

# Terminal 2 - Pane 2
cd 2
echo ".test { color: blue; }" >> src/App.css
# Use UI to merge pane 2 - this will create a conflict
```

### Step 2: Observe Resolution

- Watch backend logs for conflict detection
- Monitor agent output in logs
- Verify merge completes or aborts appropriately

### Step 3: Verify State

```bash
cd 2
git status  # Should be clean
git log -1 --oneline  # Should show merge commit if successful
git diff main origin/main  # Should show no differences
```

## Edge Cases to Test

1. **Conflict in deleted file**: One pane modifies a file, another deletes it
2. **Binary file conflict**: Conflicts in non-text files
3. **Very large diff**: Test with many changes to ensure agent handles large context
4. **Multiple sequential conflicts**: Several panes with conflicts queued up
5. **Agent timeout**: Very complex conflict that takes too long to resolve

## Troubleshooting

### Agent Not Found

If you see "cursor-agent CLI not found in PATH":

```bash
which cursor-agent
# Add to PATH if needed
```

### Conflicts Remain After Agent Run

- Check agent output for errors
- Verify agent has permissions to modify files
- Check if conflict markers are too complex for agent

### Merge Stuck in Progress

- Check if agent process is still running
- Review backend logs for exceptions
- May need to manually abort merge in pane directory

## Success Criteria

- ✅ Conflicts are automatically detected
- ✅ Agent is invoked with appropriate context
- ✅ Simple conflicts are resolved automatically
- ✅ Complex/failed resolutions trigger abort
- ✅ System returns to stable state after resolution
- ✅ No manual intervention required for common conflicts
- ✅ Logs provide clear visibility into the process
