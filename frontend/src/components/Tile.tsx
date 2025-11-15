import { useState } from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { FloatingWindow } from "./FloatingWindow";
import { GitMerge } from "lucide-react";
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
  onMerge: (paneId: number) => void;
  onTitleChange: (paneId: number, title: string) => void;
}

export function Tile({ pane, onMerge, onTitleChange }: TileProps) {
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
        <Badge className={`text-xs text-white border-0 ${paneColor}`}>
          {paneLabel}
        </Badge>
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

      {/* Merge button */}
      {pane.is_ahead && !pane.agent_running && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10">
          <Button
            size="sm"
            onClick={() => onMerge(pane.pane_id)}
            className="shadow-lg"
          >
            <GitMerge className="h-4 w-4 mr-2" />
            Merge
          </Button>
        </div>
      )}

      {/* Floating window for agent interaction */}
      <FloatingWindow
        paneId={pane.pane_id}
        title={title}
        onTitleGenerated={handleTitleGenerated}
      />

      {/* Iframe with webapp */}
      <iframe
        src={iframeUrl}
        className="w-full h-full border-0"
        title={`${paneLabel} pane`}
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
      />

      {/* Grey overlay when stale */}
      {pane.is_stale && (
        <div className="absolute inset-0 bg-gray-500 bg-opacity-30 pointer-events-none z-0" />
      )}
    </div>
  );
}

