# Quick Start Guide

This guide will help you get VV up and running in minutes.

## Prerequisites Checklist

- [ ] Python 3.10+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] cursor-agent CLI installed (`which cursor-agent`)
- [ ] Google Gemini API key (get one at https://ai.google.dev/)
- [ ] 6 git repositories in folders `1/` through `6/`
- [ ] Each webapp configured to run on ports 3001-3006

## Step 1: Setup Webapp Repositories

If you haven't already, create 6 clones of your webapp:

```bash
# Example: Clone your webapp 6 times
for i in {1..6}; do
  git clone <your-webapp-repo-url> $i
  cd $i
  # Configure to run on port 300$i
  # This will vary based on your webapp
  cd ..
done
```

## Step 2: Start the Backend

```bash
# Option 1: Use the helper script
chmod +x start-backend.sh
./start-backend.sh

# Option 2: Manual setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "WEBAPP_BASE_PATH=$(pwd)/.." > .env
python main.py
```

You should see: `INFO:     Uvicorn running on http://0.0.0.0:8000`

## Step 3: Start the Frontend

Open a new terminal:

```bash
# Option 1: Use the helper script
chmod +x start-frontend.sh
./start-frontend.sh

# Option 2: Manual setup
cd frontend
npm install
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_GEMINI_API_KEY=your_actual_api_key_here
EOF
npm run dev
```

You should see: `Local:   http://localhost:5173/`

## Step 4: Start Your Webapps

In 6 separate terminals (or use tmux/screen):

```bash
# Terminal 1
cd 1
# Start your webapp on port 3001

# Terminal 2
cd 2
# Start your webapp on port 3002

# ... repeat for 3, 4, 5, 6
```

## Step 5: Open VV

1. Open your browser to `http://localhost:5173`
2. Click the `+` button to add your first pane
3. Wait for the pane to initialize (git branch creation)
4. You should see your webapp loaded in the tile

## Step 6: Test the Workflow

### Add Multiple Panes

- Click `+` multiple times to add more panes (up to 6)
- Each pane creates a new git branch

### Request Code Changes

1. Click in the floating window on any tile
2. Type a prompt like "Add a red border to the main container"
3. Press Enter or click Submit
4. Watch the agent work in real-time
5. A title will be auto-generated for the pane

### Merge Changes

1. Once an agent completes, the pane will show "Ahead" badge
2. Click the "Merge" button at the top of the tile
3. Watch the merge queue process
4. Changes are merged to main and pushed

### Remove Panes

- Click the `X` button to remove the most recent pane
- Cannot remove panes with running agents or pending merges

## Troubleshooting

### "Connection refused" on frontend

- Make sure the backend is running on port 8000
- Check `VITE_API_URL` in `frontend/.env`

### "cursor-agent not found"

```bash
# Install cursor-agent (varies by installation method)
# Check the cursor-agent documentation
which cursor-agent  # Should show a path
```

### Iframe shows "Connection refused"

- Make sure your webapps are actually running on ports 3001-3006
- Check each webapp individually: `curl http://localhost:3001`

### Git errors in backend logs

- Verify folders 1-6 are git repositories: `ls -la 1/.git`
- Ensure you have origin remote configured: `cd 1 && git remote -v`
- Check you can pull from main: `cd 1 && git pull origin main`

### Agent not streaming

- Check backend logs for errors
- Verify cursor-agent works: `cd 1 && cursor-agent "add a comment"`
- Check browser console for SSE connection errors

## Testing the Full Stack

Here's a complete test to verify everything works:

```bash
# 1. Check backend
curl http://localhost:8000
# Should return: {"message":"VV Backend API","version":"1.0"}

# 2. Check orchestration endpoint
curl http://localhost:8000/api/orchestration
# Should return JSON with 6 panes

# 3. Create a pane
curl -X POST http://localhost:8000/api/panes/1/create
# Should return success with branch name

# 4. Check git branch was created
cd 1 && git branch
# Should show tmp-1-XXXXXX branch (where XXXXXX is uuid)

# 5. Open frontend and test UI
open http://localhost:5173
```

## Next Steps

- Configure your webapps to automatically restart when code changes
- Set up multiple terminals with tmux or screen for easier management
- Explore the API documentation at http://localhost:8000/docs
- Customize the UI colors and layout to your preference

## Getting Help

If you encounter issues:

1. Check the logs:

   - Backend: Terminal where you ran `python main.py`
   - Frontend: Browser console (F12)
   - Webapps: Check each webapp's logs

2. Verify git state:

   ```bash
   cd 1
   git status
   git branch
   git log --oneline -5
   ```

3. Test components individually:
   - Backend only: Use curl or Postman
   - Frontend only: Check if API calls are made
   - Git operations: Test manually first

Happy coding with VV! 🚀
