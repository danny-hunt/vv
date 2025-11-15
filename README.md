# VV - Multi-Version Dev Tool

VV is a UI-first development tool that allows you to run and view multiple versions of the same webapp simultaneously in one browser tab. It provides a tiled view of up to 6 different versions running on different ports, with git orchestration and AI-powered code modifications.

## Features

- 🎯 **Tiled View**: Display up to 6 versions of your webapp in a responsive grid layout
- 🔄 **Git Orchestration**: Automatic branch management for each pane
- 🤖 **AI-Powered Changes**: Request code changes using cursor-agent CLI
- 💾 **Auto-Commit**: Automatically stage and commit all changes after agent completes
- 📊 **Status Tracking**: Visual indicators for ahead/stale branches
- 🔀 **Smart Merging**: Sequential merge queue with automatic conflict handling
- 💬 **Interactive UI**: Collapsible floating windows for each pane
- 🏷️ **Auto-Titles**: AI-generated titles using Google Gemini

## Architecture

```
vv/
├── backend/          # Python FastAPI server
│   ├── main.py       # Main API server
│   ├── git_ops.py    # Git operations
│   └── agent.py      # cursor-agent integration
├── frontend/         # React + Vite UI
│   └── src/
│       ├── components/   # UI components
│       ├── hooks/        # React hooks
│       └── lib/          # Utilities
└── 1/, 2/, 3/, 4/, 5/, 6/  # Webapp clones
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- cursor-agent CLI installed and in PATH
- Git repositories in folders 1-6
- Each webapp should run on ports 3001-3006

## Setup

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file:

```bash
echo "WEBAPP_BASE_PATH=$(pwd)/.." > .env
```

5. Start the backend server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Create a `.env` file:

```bash
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_GEMINI_API_KEY=your_gemini_api_key_here
EOF
```

4. Start the development server:

```bash
npm run dev
```

The UI will be available at `http://localhost:5173`.

### Webapp Setup

Ensure you have 6 clones of your webapp in folders named `1`, `2`, `3`, `4`, `5`, and `6` at the root of the vv directory. Each should be configured to run on ports 3001-3006 respectively.

## Usage

1. **Start VV**: Open `http://localhost:5173` in your browser

2. **Add a Pane**: Click the `+` button in the bottom-left corner

   - This creates a new git branch and displays the webapp in a new tile

3. **Request Changes**: Use the floating window on each tile

   - Type your request and press Enter or click Submit
   - The first request will generate an AI title for the pane
   - Agent responses will stream in real-time
   - All changes are automatically staged and committed when the agent completes

4. **Merge Changes**: Click the "Merge" button on panes marked as "Ahead"

   - Multiple merge requests are processed sequentially
   - Merges push changes to the main branch

5. **Remove Panes**: Click the `X` button when you have more than one pane
   - Cannot remove panes with running agents or pending merges

## API Endpoints

### Backend API

- `POST /api/panes/{pane_id}/create` - Initialize a pane
- `GET /api/orchestration` - Get status of all panes
- `POST /api/panes/{pane_id}/agent` - Start cursor-agent
- `GET /api/panes/{pane_id}/agent/stream` - SSE stream of agent output
- `POST /api/panes/{pane_id}/merge` - Queue a merge
- `GET /api/merge-queue` - Get merge queue status
- `DELETE /api/panes/{pane_id}` - Reset a pane

Full API documentation available at `http://localhost:8000/docs`

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

Frontend:

```bash
cd frontend
npm run build
```

## Status Indicators

- **Ahead**: Branch has commits not in main (shows blue badge)
- **Stale**: Branch is missing commits from main (shows red badge)
- **Agent Running**: cursor-agent is currently running (shows yellow badge)

## Troubleshooting

### Backend won't start

- Ensure Python 3.10+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify the `.env` file has the correct `WEBAPP_BASE_PATH`

### Frontend won't connect

- Verify the backend is running on `http://localhost:8000`
- Check the `VITE_API_URL` in frontend `.env` file
- Ensure CORS is properly configured in the backend

### Agent not working

- Verify cursor-agent CLI is installed: `which cursor-agent`
- Check that the webapp directories (1-6) exist and are git repositories
- Look at backend logs for detailed error messages

### Iframes not loading

- Ensure your webapps are running on ports 3001-3006
- Check browser console for CORS or security errors
- Verify the iframe sandbox permissions

## Notes

- Merge conflict resolution is not fully implemented yet
- Merges that have conflicts will fail
- The agent uses cursor-agent CLI which must be separately installed
- Each pane's branch follows the pattern `tmp-{id}-{uuid6}`

## License

MIT
