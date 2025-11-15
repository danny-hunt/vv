import { Tile } from "./Tile";
import type { Pane, MergeQueueItem } from "@/types";

interface TileGridProps {
  panes: Pane[];
  onTitleChange: (paneId: number, title: string) => void;
  onDiscard: (paneId: number) => void;
  onKeep: (paneId: number) => void;
  mergeQueue: MergeQueueItem[];
}

export function TileGrid({ panes, onTitleChange, onDiscard, onKeep, mergeQueue }: TileGridProps) {
  const count = panes.length;

  // Determine grid layout based on number of panes
  let gridClass = "";
  if (count === 1) {
    gridClass = "grid-cols-1 grid-rows-1";
  } else if (count === 2) {
    gridClass = "grid-cols-2 grid-rows-1";
  } else if (count === 3 || count === 4) {
    gridClass = "grid-cols-2 grid-rows-2";
  } else if (count === 5 || count === 6) {
    gridClass = "grid-cols-3 grid-rows-2";
  }

  return (
    <div className={`w-full h-full grid ${gridClass} gap-0`}>
      {panes.map((pane) => (
        <Tile
          key={pane.pane_id}
          pane={pane}
          onTitleChange={onTitleChange}
          onDiscard={onDiscard}
          onKeep={onKeep}
          isInMergeQueue={mergeQueue.some((m) => m.pane_id === pane.pane_id)}
        />
      ))}
    </div>
  );
}
