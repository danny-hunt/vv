# Merge Conflict Resolution - Implementation Summary

## Overview

Implemented automatic merge conflict resolution using cursor-agent. When a merge operation encounters conflicts, the system automatically invokes cursor-agent to resolve them. If successful, the merge completes automatically. If the agent fails, the merge is aborted and the pane is reset to a clean state.

## Changes Made

### 1. Enhanced `git_ops.py`

#### New Methods

**`get_conflicted_files(pane_id, repo)`**
- Extracts list of files with merge conflicts
- Uses `repo.index.unmerged_blobs()` to identify conflicted files
- Returns list of file paths

**`get_branch_diff(pane_id, branch_name, repo)`**
- Gets full diff of changes from the branch compared to main
- Uses `git diff origin/main branch_name`
- Truncates to 50,000 chars to avoid overwhelming the agent
- Returns diff as string

**`abort_merge(pane_id)`**
- Aborts an in-progress merge and resets to clean state
- Runs `git merge --abort` followed by `git reset --hard`
- Used when agent fails to resolve conflicts

**`complete_merge(pane_id, branch_to_merge)`**
- Completes a merge after conflicts have been resolved
- Verifies no unresolved conflicts remain
- Pushes to origin main
- Deletes the temporary branch
- Separated from initial merge attempt to allow conflict resolution in between

**`resolve_merge_conflict(pane_id, branch_name, conflicted_files, diff, agent_manager)`** (async)
- Orchestrates automatic conflict resolution using cursor-agent
- Builds comprehensive prompt including:
  - List of conflicted files
  - Full diff of changes
  - Step-by-step instructions for resolution
- Calls `agent_manager.run_agent_sync()` and waits for completion
- Verifies conflicts are actually resolved
- Returns status: "success" or "error"

#### Modified Methods

**`merge_pane(pane_id)`**
- Enhanced to detect merge conflicts
- Checks GitCommandError stdout for "CONFLICT" keyword
- Returns new status "conflict" with additional data:
  - `branch`: Name of branch being merged
  - `conflicted_files`: List of files with conflicts
  - `diff`: Full diff of the branch
- Original merge-and-push logic preserved for conflict-free merges

### 2. Enhanced `agent.py`

#### New Method

**`run_agent_sync(pane_id, user_prompt)`** (async)
- Synchronous version of agent execution
- Waits for cursor-agent to complete before returning
- Captures all output for logging
- Automatically commits changes if agent succeeds (exit code 0)
- Uses commit message: "Resolved merge conflicts"
- Returns:
  - `status`: "success" or "error"
  - `exit_code`: Agent process exit code
  - `output`: Full agent output
  - `message`: Status message

### 3. Enhanced `main.py`

#### Modified Function

**`process_merge_queue()`**
- Now handles three merge statuses:
  1. **"success"**: Normal merge completed
  2. **"conflict"**: Conflict detected, triggers resolution
  3. **"error"**: Other error, logged and skipped
  
- Conflict resolution flow:
  1. Extract conflict details from merge result
  2. Log conflict detection
  3. Call `git_ops.resolve_merge_conflict()`
  4. If resolution succeeds:
     - Call `git_ops.complete_merge()` to push and cleanup
     - Log success
  5. If resolution fails:
     - Call `git_ops.abort_merge()` to reset
     - Log failure
  
- Enhanced error handling with try-catch around merge abort

## Conflict Resolution Flow

```
User clicks Merge
    ↓
merge_pane(pane_id) called
    ↓
git merge branch --no-ff
    ↓
    ├─ No conflict → Push & cleanup → SUCCESS
    ↓
    └─ CONFLICT detected
        ↓
        Extract conflicted files & diff
        ↓
        Return status="conflict"
        ↓
        process_merge_queue() detects conflict
        ↓
        resolve_merge_conflict() called
        ↓
        Build agent prompt with context
        ↓
        run_agent_sync() invoked
        ↓
        Agent analyzes and fixes conflicts
        ↓
        Agent commits merge (git commit --no-edit)
        ↓
        ├─ Agent succeeds → complete_merge() → Push & cleanup → SUCCESS
        └─ Agent fails → abort_merge() → Reset to clean state → FAILURE
```

## Agent Prompt Template

The agent receives:
- List of conflicted files
- Full diff showing what changed in the branch
- Clear instructions to:
  1. Examine conflicts
  2. Resolve by editing files
  3. Remove conflict markers
  4. Stage resolved files
  5. Commit with `git commit --no-edit`
  6. NOT push (done automatically)

## Error Handling

### Conflict Resolution Failures
- Agent fails to start → Abort merge immediately
- Agent exits with error → Abort merge, log details
- Conflicts remain after agent → Abort merge
- Push fails after resolution → Leave in merged state for manual intervention

### Exception Handling
- All merge operations wrapped in try-catch
- Exceptions during merge trigger automatic abort attempt
- Detailed logging at every step

## Testing

### Test Files Created
1. **`MERGE_CONFLICT_TESTING.md`**
   - Comprehensive testing guide
   - Multiple test scenarios
   - Verification commands
   - Edge cases to consider

2. **`test-conflict-resolution.sh`**
   - Automated setup script
   - Creates conflict scenario between panes 1 and 2
   - Step-by-step instructions for testing
   - Cleanup guidance

### Testing Scenarios Covered
1. Simple conflict resolution (same file, different changes)
2. Agent failure handling
3. Multiple files in conflict
4. Complex conflicts
5. Sequential conflicts in queue

## Monitoring and Observability

### Key Log Messages

**Conflict Detection:**
```
[MERGE QUEUE] Conflict detected for pane {id}, attempting automatic resolution
[MERGE QUEUE] Invoking agent to resolve conflicts in {n} file(s)
```

**Resolution Success:**
```
[Pane {id}] Agent successfully resolved conflicts
[MERGE QUEUE] Merge completed successfully for pane {id}
```

**Resolution Failure:**
```
[MERGE QUEUE] Agent failed to resolve conflicts for pane {id}
[MERGE QUEUE] Aborting merge for pane {id}
[MERGE QUEUE] Successfully aborted merge for pane {id}
```

## Benefits

1. **Zero Manual Intervention**: Common conflicts resolved automatically
2. **Safe Fallback**: Failed resolutions abort cleanly
3. **Full Context**: Agent receives complete diff and conflict info
4. **Automatic Cleanup**: Successful merges push and delete branches
5. **Clear Logging**: Every step logged for debugging
6. **User Transparency**: Works within existing merge queue system

## Future Enhancements

Potential improvements:
1. UI notification when conflicts are being resolved
2. Display agent output in frontend during resolution
3. Configurable timeout for agent resolution
4. Metrics on resolution success rate
5. Option to manually review before pushing
6. Support for custom conflict resolution strategies
7. Retry logic with different prompts

## Compatibility

- Works with existing merge queue system
- No changes required to frontend
- Backwards compatible with conflict-free merges
- Uses existing agent infrastructure
- Leverages existing git operations patterns

## Files Modified

1. `/Users/danny/src/vv/backend/git_ops.py` - Core conflict resolution logic
2. `/Users/danny/src/vv/backend/agent.py` - Synchronous agent execution
3. `/Users/danny/src/vv/backend/main.py` - Merge queue conflict handling

## Files Added

1. `/Users/danny/src/vv/MERGE_CONFLICT_TESTING.md` - Testing documentation
2. `/Users/danny/src/vv/test-conflict-resolution.sh` - Test automation script
3. `/Users/danny/src/vv/MERGE_CONFLICT_IMPLEMENTATION.md` - This document

## Success Criteria Met

✅ Conflicts automatically detected during merge
✅ Agent invoked with comprehensive context
✅ Simple conflicts resolved without manual intervention
✅ Failed resolutions trigger clean abort
✅ System returns to stable state after resolution
✅ Clear logging throughout the process
✅ No breaking changes to existing functionality
✅ Comprehensive testing documentation provided

