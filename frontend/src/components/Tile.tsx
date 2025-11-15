import { useState } from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { FloatingWindow } from "./FloatingWindow";
import { GitMerge, Trash2, Check } from "lucide-react";
import type { Pane } from "@/types";

const PANE_LABELS = ["apricot", "banana", "cucumber", "dragonfruit", "eggplant", "fennel"];

const PANE_COLORS: Record<string, string> = {
  apricot: "bg-orange-500/60",
  banana: "bg-yellow-500/60",
  cucumber: "bg-green-300/60",
  dragonfruit: "bg-pink-500/60",
  eggplant: "bg-purple-600/60",
  fennel: "bg-green-500/60",
};

interface TileProps {
  pane: Pane;
  onTitleChange: (paneId: number, title: string) => void;
  onDiscard: (paneId: number) => void;
  onKeep: (paneId: number) => void;
  isInMergeQueue: boolean;
}

export function Tile({ pane, onTitleChange, onDiscard, onKeep, isInMergeQueue }: TileProps) {
  const [title, setTitle] = useState(pane.title);

  const handleTitleGenerated = (newTitle: string) => {
    setTitle(newTitle);
    onTitleChange(pane.pane_id, newTitle);
  };

  const iframeUrl = `http://localhost:300${pane.pane_id}`;
  const paneLabel = PANE_LABELS[pane.pane_id - 1];
  const paneColor = PANE_COLORS[paneLabel];

  return (
    <div className="relative w-full h-full bg-background border rounded-lg overflow-hidden">
      {/* Status badges */}
      <div className="absolute bottom-2 left-2 z-10 flex gap-2">
        <Badge className={`text-xs text-white border-0 ${paneColor}`}>{paneLabel}</Badge>
        {pane.is_ahead && (
          <Badge variant="default" className="text-xs bg-blue-600">
            Ahead
          </Badge>
        )}
        {pane.is_stale && (
          <Badge variant="destructive" className="text-xs">
            Stale
          </Badge>
        )}
        {pane.agent_running && (
          <Badge variant="secondary" className="text-xs bg-yellow-600">
            Agent Running
          </Badge>
        )}
      </div>

      {/* Discard and Keep buttons */}
      {pane.active && !pane.agent_running && !isInMergeQueue && (
        <div className="absolute bottom-2 right-2 z-10 flex gap-2">
          <Button
            size="sm"
            variant="destructive"
            onClick={() => onDiscard(pane.pane_id)}
            className="shadow-lg"
            title="Discard changes and reset to main"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            onClick={() => onKeep(pane.pane_id)}
            className="shadow-lg bg-green-600 hover:bg-green-700"
            title="Keep changes (merge to main and start new branch)"
          >
            <Check className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Floating window for agent interaction */}
      <FloatingWindow paneId={pane.pane_id} title={title} onTitleGenerated={handleTitleGenerated} />

      {/* Iframe with webapp */}
      <iframe
        src={iframeUrl}
        className="w-full h-full border-0"
        title={`${paneLabel} pane`}
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
      />

      {/* Grey overlay when stale */}
      {pane.is_stale && <div className="absolute inset-0 bg-gray-500 bg-opacity-30 pointer-events-none z-0" />}
    </div>
  );
}
