# Commit Message Example

This document demonstrates how commit messages now describe the desired change.

## Example Workflow

### Step 1: User submits a prompt
```
User types in pane 1: "Add dark mode toggle to the header"
```

### Step 2: Agent makes changes
The cursor-agent:
- Creates a dark mode state in App.tsx
- Adds a toggle button to Header.tsx
- Updates CSS with dark mode styles

### Step 3: Auto-commit with descriptive message
```bash
# The commit is automatically created with the user's prompt as the message
git log --oneline
abc1234 Add dark mode toggle to the header
```

**Before this change**, the commit would have been:
```bash
git log --oneline
abc1234 Agent changes  # ❌ Not descriptive
```

### Step 4: User merges to main
When the user clicks "Merge" on pane 1:

```bash
# The merge commit uses the same descriptive message
git log --oneline
def5678 Add dark mode toggle to the header  # The merge commit
abc1234 Add dark mode toggle to the header  # The original commit
```

**Before this change**, the merge commit would have been:
```bash
git log --oneline
def5678 Merge tmp-1-abc123  # ❌ Technical branch name, not meaningful
abc1234 Agent changes
```

## Benefits

1. **Readable Git History**: Anyone looking at `git log` can understand what changes were made
2. **Better Collaboration**: Team members can see the intent behind each change
3. **Easier Debugging**: When investigating issues, commit messages provide context
4. **Self-Documenting**: No need to manually write commit messages

## Real Git Log Example

### Before (Generic Messages)
```
$ git log --oneline
a1b2c3d Merge tmp-3-def456
e4f5g6h Agent changes
h7i8j9k Merge tmp-2-ghi789
k0l1m2n Agent changes
n3o4p5q Merge tmp-1-jkl012
q6r7s8t Agent changes
```

### After (Descriptive Messages)
```
$ git log --oneline
a1b2c3d Fix mobile responsive layout issues
e4f5g6h Fix mobile responsive layout issues
h7i8j9k Add user authentication with JWT
k0l1m2n Add user authentication with JWT
n3o4p5q Implement search functionality
q6r7s8t Implement search functionality
```

## Technical Implementation

The system achieves this by:

1. **Storing the prompt**: When `start_agent()` is called, the user's prompt is stored in `agent_prompts` dictionary
2. **Using it for commits**: When the agent completes, `commit_changes()` is called with the stored prompt as the message
3. **Extracting for merges**: When merging, the most recent commit message from the branch is extracted and used as the merge commit message
4. **Cleanup**: The stored prompt is removed after the agent completes to avoid memory leaks

## Edge Cases Handled

1. **No changes**: If the agent runs but makes no changes, no commit is created (silent handling)
2. **Missing prompt**: If the prompt is somehow not available, falls back to "Agent changes"
3. **Merge conflicts**: Conflict resolution commits use "Resolved merge conflicts" as a standard message
4. **Failed extraction**: If extracting the branch commit message fails, falls back to "Merge tmp-X-XXX" format

