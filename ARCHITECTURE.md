# VV Architecture Documentation

## Overview

VV (Multi-Version Dev Tool) is a full-stack application that orchestrates multiple versions of a webapp running simultaneously, with AI-powered code modifications and git-based version control.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              React Frontend (Port 5173)              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │  Tile 1  │ │  Tile 2  │ │  Tile 3  │  ...       │   │
│  │  │ iframe   │ │ iframe   │ │ iframe   │            │   │
│  │  │ :3001    │ │ :3002    │ │ :3003    │            │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ REST + SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Git Ops    │ │ Agent Mgr   │ │ API Routes  │          │
│  │             │ │             │ │             │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
           │                │                │
           │ Git            │ Subprocess     │ HTTP
           ▼                ▼                ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
│  Webapp Repos   │ │ cursor-agent │ │ Gemini API   │
│  (1, 2, 3...)   │ │     CLI      │ │              │
└─────────────────┘ └──────────────┘ └──────────────┘
```

## Component Breakdown

### Frontend (React + TypeScript)

#### Core Components

**`App.tsx`**
- Root component
- Global state management
- Orchestration polling (5s interval)
- Merge queue management
- Pane lifecycle management

**`TileGrid.tsx`**
- Responsive grid layout
- Adapts to pane count:
  - 1 pane: 1×1
  - 2 panes: 2×1
  - 3-4 panes: 2×2
  - 5-6 panes: 3×2

**`Tile.tsx`**
- Individual pane container
- Iframe embedding
- Status badges (Ahead, Stale, Running)
- Merge button
- Grey overlay for stale panes

**`FloatingWindow.tsx`**
- Collapsible chat interface
- Prompt input
- Agent output display
- Title generation trigger
- Streaming message display

**`FloatingControls.tsx`**
- Plus button (add pane)
- X button (remove pane)
- Button state management

#### Custom Hooks

**`usePolling.ts`**
- Polls `/api/orchestration` every 5s
- Updates global orchestration state
- Handles errors gracefully
- Auto-retry on failure

**`useAgentStream.ts`**
- Manages SSE connections
- Streams agent output
- Handles connection lifecycle
- Error recovery

#### Libraries

**`api.ts`**
- API client wrapper
- Type-safe endpoints
- Error handling
- SSE connection factory

**`gemini.ts`**
- Google Gemini integration
- Title generation
- Fallback handling
- Prompt engineering

**`utils.ts`**
- Tailwind class merging
- Common utilities

### Backend (Python + FastAPI)

#### Core Modules

**`main.py`**
- FastAPI application
- CORS configuration
- Route definitions
- Global state (merge queue)
- Async merge processing

**API Endpoints:**
```python
POST   /api/panes/{pane_id}/create     # Initialize pane
GET    /api/orchestration              # Get all pane statuses
POST   /api/panes/{pane_id}/agent      # Start agent
GET    /api/panes/{pane_id}/agent/stream  # SSE stream
POST   /api/panes/{pane_id}/merge      # Queue merge
GET    /api/merge-queue                # Get queue status
DELETE /api/panes/{pane_id}            # Reset pane
```

**`git_ops.py`**
- Git repository management
- Branch operations
- Status checking (ahead/stale)
- Merge operations

**Key Functions:**
```python
create_pane_branch(pane_id)  # Create tmp-{id}-{uuid6} branch
get_branch_status(pane_id)   # Get current git state
is_ahead(pane_id)            # Check if ahead of main
is_stale(pane_id)            # Check if behind main
merge_pane(pane_id)          # Merge to main and push
```

**`agent.py`**
- cursor-agent CLI integration
- Process management
- Output streaming
- Lifecycle tracking

**Key Functions:**
```python
start_agent(pane_id, prompt)      # Start subprocess
stream_agent_output(pane_id)      # Yield output lines
is_agent_running(pane_id)         # Check status
stop_agent(pane_id)               # Terminate process
```

## Data Flow

### Pane Creation Flow

```
1. User clicks + button
   ↓
2. Frontend finds first available pane ID
   ↓
3. POST /api/panes/{id}/create
   ↓
4. Backend:
   - git checkout main
   - git pull
   - git checkout -b tmp-{id}-{uuid}
   ↓
5. Frontend adds pane to grid
   ↓
6. Iframe loads http://localhost:300{id}
   ↓
7. Polling picks up new active pane
```

### Agent Request Flow

```
1. User types prompt and submits
   ↓
2. If first prompt:
   - Call Gemini API
   - Generate title
   - Update UI
   ↓
3. POST /api/panes/{id}/agent
   ↓
4. Backend starts cursor-agent subprocess
   ↓
5. Frontend connects to SSE endpoint
   ↓
6. Agent output streams line by line
   ↓
7. Output displayed in FloatingWindow
   ↓
8. On completion:
   - Close SSE connection
   - Update agent_running = false
   - Polling detects "ahead" status
```

### Merge Flow

```
1. User clicks Merge button
   ↓
2. Add pane_id to merge queue
   ↓
3. If not already merging:
   - Start async merge processor
   ↓
4. For each queued pane:
   - POST /api/panes/{id}/merge
   - Backend:
     * git checkout main
     * git pull
     * git merge tmp-{id}-{uuid}
     * git push
     * git branch -D tmp-{id}-{uuid}
   - Wait 1 second
   - Process next
   ↓
5. Polling detects pane back on main
   ↓
6. UI removes badges, updates state
```

### Polling Flow

```
Every 5 seconds:
1. GET /api/orchestration
   ↓
2. Backend checks each pane (1-6):
   - Current branch
   - git log origin/main..HEAD (ahead)
   - git log HEAD..origin/main (stale)
   - Check agent_manager.is_running()
   ↓
3. Return status array
   ↓
4. Frontend updates pane state
   ↓
5. UI reflects new badges/overlays
```

## State Management

### Frontend State

**Global App State:**
```typescript
{
  panes: Pane[],              // All 6 panes
  mergeQueue: MergeQueueItem[], // Pending merges
  isMerging: boolean           // Processing flag
}
```

**Pane State:**
```typescript
{
  pane_id: number,        // 1-6
  active: boolean,        // Has branch != main
  branch: string | null,  // Current branch name
  is_ahead: boolean,      // Has commits not in main
  is_stale: boolean,      // Missing commits from main
  agent_running: boolean, // Agent in progress
  title?: string          // AI-generated title
}
```

### Backend State

**Agent Manager:**
```python
{
  running_agents: Dict[int, Process],  # Active subprocesses
  agent_outputs: Dict[int, Queue]      # Output buffers
}
```

**Merge Queue:**
```python
merge_queue: List[int]        # Pane IDs to merge
merge_in_progress: bool       # Processing flag
```

## Key Design Decisions

### 1. Iframe Sandboxing
- Each pane runs in isolated iframe
- Sandbox allows scripts, forms, popups
- Prevents unwanted interactions
- Security boundary between versions

### 2. SSE for Streaming
- Server-Sent Events for agent output
- Simpler than WebSockets
- One-way communication sufficient
- Browser handles reconnection

### 3. Polling for State
- 5-second interval balances freshness vs load
- Git operations are relatively fast
- No need for real-time updates
- Simple to implement and debug

### 4. Sequential Merge Queue
- Prevents conflicts from concurrent merges
- Easier to reason about
- Frontend manages queue
- Backend executes atomically

### 5. Branch Naming
- `tmp-{id}-{uuid6}` pattern
- Easy to identify and clean up
- UUID prevents collisions
- Prefix indicates temporary nature

### 6. Title Generation
- Frontend calls Gemini directly
- Reduces backend complexity
- Faster response
- Fallback to simple truncation

## Error Handling

### Frontend
- API errors: Display user-friendly messages
- Network errors: Retry with exponential backoff
- SSE disconnects: Automatic reconnection
- Invalid state: Reset to safe defaults

### Backend
- Git errors: Return 500 with detailed message
- Agent failures: Clean up subprocess
- Merge conflicts: Fail and remove from queue
- Process crashes: Log and notify frontend

## Security Considerations

### Current
- CORS limited to localhost
- Iframe sandbox restrictions
- No authentication (local dev tool)
- Git operations in trusted repos

### Future Improvements
- Add authentication for multi-user
- Validate git operations more strictly
- Rate limit API endpoints
- Secure sensitive environment variables

## Performance Characteristics

### Scalability
- **6 panes**: Hard limit by design
- **Polling**: 6 git status checks every 5s
- **Iframes**: Browser-dependent (~6 is reasonable)
- **Agents**: Limited by CPU (cursor-agent overhead)

### Bottlenecks
- Git operations (I/O bound)
- cursor-agent execution (CPU bound)
- Gemini API calls (network bound)
- Browser iframe rendering (memory)

## Future Enhancements

### Short Term
- Add agent cancellation
- Persist pane state across refreshes
- Add conflict resolution UI
- Better error messages

### Medium Term
- Add pane reordering/resizing
- Support custom ports
- Add pane history/snapshots
- Improve title generation

### Long Term
- Multi-repo support
- Collaborative features
- Cloud deployment
- Analytics dashboard

## Development Guidelines

### Adding New Features

1. **Backend First**: Define API endpoint
2. **Test API**: Use curl/Postman
3. **Frontend Integration**: Add to API client
4. **UI Component**: Build interface
5. **Connect**: Wire up with hooks
6. **Test**: Manual and automated

### Code Style

**Python:**
- PEP 8 compliance
- Type hints encouraged
- Async/await for I/O
- Descriptive function names

**TypeScript:**
- Strict mode enabled
- Explicit types
- Functional components
- Custom hooks for logic

### Git Workflow

```bash
# Feature branch
git checkout -b feature/name

# Make changes
# Commit often

# Before PR
git rebase main
npm run lint
npm run test

# Create PR
```

## Monitoring & Debugging

### Logs

**Backend:**
```bash
# View logs
tail -f backend.log

# Debug mode
LOG_LEVEL=DEBUG python main.py
```

**Frontend:**
```javascript
// Enable debug logging
localStorage.setItem('debug', 'vv:*')
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000

# Check orchestration
curl http://localhost:8000/api/orchestration | jq

# Check merge queue
curl http://localhost:8000/api/merge-queue | jq
```

### Common Issues

**"Pane won't create"**
- Check git repo exists
- Verify main branch exists
- Check origin remote configured

**"Agent won't start"**
- Verify cursor-agent in PATH
- Check working directory permissions
- Review backend logs

**"Merge fails"**
- Check for conflicts
- Verify push permissions
- Review git state manually

## Dependencies

### Backend
- fastapi: Web framework
- uvicorn: ASGI server
- gitpython: Git operations
- sse-starlette: SSE support
- pydantic: Data validation

### Frontend
- react: UI framework
- vite: Build tool
- @radix-ui: UI primitives
- tailwindcss: Styling
- @google/generative-ai: Gemini API

## Configuration

### Environment Variables

**Backend (.env):**
```bash
WEBAPP_BASE_PATH=/Users/danny/src/vv
LOG_LEVEL=INFO  # Optional
```

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:8000
VITE_GEMINI_API_KEY=your_key_here
```

## Deployment

### Local Development
- Follow QUICKSTART.md
- Use provided shell scripts
- Ensure all prerequisites met

### Production (Future)
- Build frontend: `npm run build`
- Serve with nginx/caddy
- Run backend with gunicorn
- Use process manager (systemd/supervisor)
- Configure reverse proxy
- Add SSL certificates

## License

MIT License - See LICENSE file for details

