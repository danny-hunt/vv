import { useState, useEffect } from "react";
import { TileGrid } from "./components/TileGrid";
import { FloatingControls } from "./components/FloatingControls";
import { usePolling } from "./hooks/usePolling";
import { apiClient } from "./lib/api";
import type { Pane, MergeQueueItem } from "./types";

function App() {
  const { orchestrationState, error, isLoading } = usePolling(5000);
  const [panes, setPanes] = useState<Pane[]>([]);
  const [mergeQueue, setMergeQueue] = useState<MergeQueueItem[]>([]);
  const [isMerging, setIsMerging] = useState(false);
  const [panesBeingKept, setPanesBeingKept] = useState<Set<number>>(new Set());

  // Update panes when orchestration state changes
  useEffect(() => {
    if (orchestrationState) {
      setPanes(orchestrationState.panes);
    }
  }, [orchestrationState]);

  // Process merge queue
  useEffect(() => {
    if (mergeQueue.length > 0 && !isMerging) {
      processMergeQueue();
    }
  }, [mergeQueue, isMerging]);

  const processMergeQueue = async () => {
    if (mergeQueue.length === 0 || isMerging) return;

    setIsMerging(true);
    const currentItem = mergeQueue[0];

    try {
      await apiClient.mergePane(currentItem.pane_id);
      console.log(`Successfully merged pane ${currentItem.pane_id}`);

      // Wait a bit for backend to complete
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Remove from queue
      setMergeQueue((prev) => prev.slice(1));
    } catch (err) {
      console.error(`Failed to merge pane ${currentItem.pane_id}:`, err);
      // Still remove from queue to continue processing
      setMergeQueue((prev) => prev.slice(1));
    } finally {
      setIsMerging(false);
    }
  };

  const handleAddPane = async () => {
    // Find the first inactive pane
    const inactivePaneIds = panes.filter((p) => !p.active).map((p) => p.pane_id);

    if (inactivePaneIds.length === 0) {
      console.error("No available panes");
      return;
    }

    const paneId = inactivePaneIds[0];

    try {
      await apiClient.createPane(paneId);
      console.log(`Created pane ${paneId}`);
    } catch (err) {
      console.error(`Failed to create pane ${paneId}:`, err);
    }
  };

  const handleMerge = (paneId: number) => {
    // Add to merge queue if not already there
    if (!mergeQueue.some((m) => m.pane_id === paneId)) {
      setMergeQueue((prev) => [...prev, { pane_id: paneId, status: "queued" }]);
    }
  };

  const handleDiscard = async (paneId: number) => {
    try {
      await apiClient.deletePane(paneId);
      console.log(`Discarded pane ${paneId}`);

      // Remove from tracking set in case pane was in keep operation
      setPanesBeingKept((prev) => {
        const newSet = new Set(prev);
        newSet.delete(paneId);
        return newSet;
      });
    } catch (err) {
      console.error(`Failed to discard pane ${paneId}:`, err);
    }
  };

  const handleKeep = async (paneId: number) => {
    // Add pane to tracking set to keep it visible during the keep operation
    setPanesBeingKept((prev) => new Set(prev).add(paneId));

    try {
      // Add to merge queue - let processMergeQueue handle the actual merge
      if (!mergeQueue.some((m) => m.pane_id === paneId)) {
        setMergeQueue((prev) => [...prev, { pane_id: paneId, status: "queued" }]);
        console.log(`Keeping pane ${paneId} - added to merge queue`);
      }

      // Wait for merge to complete by polling the pane status
      const waitForMerge = async () => {
        let attempts = 0;
        const maxAttempts = 30; // 30 seconds max wait

        while (attempts < maxAttempts) {
          await new Promise((resolve) => setTimeout(resolve, 1000));

          const state = await apiClient.getOrchestrationState();
          const pane = state.panes.find((p) => p.pane_id === paneId);

          // If pane is now inactive (on main), merge is complete
          if (pane && !pane.active) {
            console.log(`Merge complete for pane ${paneId}, creating new branch`);
            // Create a new branch for continued work
            await apiClient.createPane(paneId);
            return;
          }

          attempts++;
        }

        console.warn(`Timeout waiting for merge to complete for pane ${paneId}`);
      };

      // Wait for merge and create new branch
      await waitForMerge();
    } catch (err) {
      console.error(`Failed to keep pane ${paneId}:`, err);
    } finally {
      // Remove pane from tracking set once keep operation is complete
      setPanesBeingKept((prev) => {
        const newSet = new Set(prev);
        newSet.delete(paneId);
        return newSet;
      });
    }
  };

  const handleTitleChange = (paneId: number, title: string) => {
    setPanes((prev) => prev.map((p) => (p.pane_id === paneId ? { ...p, title } : p)));
  };

  const activePanes = panes.filter((p) => p.active || panesBeingKept.has(p.pane_id));

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-2">Error connecting to backend</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <TileGrid
        panes={activePanes}
        onTitleChange={handleTitleChange}
        onDiscard={handleDiscard}
        onKeep={handleKeep}
        mergeQueue={mergeQueue}
      />

      <FloatingControls activePaneCount={activePanes.length} onAddPane={handleAddPane} />

      {/* Merge queue indicator */}
      {mergeQueue.length > 0 && (
        <div className="fixed bottom-6 right-6 bg-card border rounded-lg p-4 shadow-lg z-50">
          <h3 className="text-sm font-semibold mb-2">Merge Queue</h3>
          <div className="space-y-1">
            {mergeQueue.map((item, index) => (
              <div key={item.pane_id} className="text-xs text-muted-foreground">
                {index === 0 && isMerging ? "⏳" : "⏸️"} Pane {item.pane_id}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
