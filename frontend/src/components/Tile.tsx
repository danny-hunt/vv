import { useState } from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { FloatingWindow } from "./FloatingWindow";
import { GitMerge } from "lucide-react";
import type { Pane } from "@/types";

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

  return (
    <div className="relative w-full h-full bg-background border rounded-lg overflow-hidden">
      {/* Status badges */}
      <div className="absolute top-2 left-2 z-10 flex gap-2">
        <Badge variant="secondary" className="text-xs">
          Pane {pane.pane_id}
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
        title={`Pane ${pane.pane_id}`}
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
      />

      {/* Grey overlay when stale */}
      {pane.is_stale && (
        <div className="absolute inset-0 bg-gray-500 bg-opacity-30 pointer-events-none z-0" />
      )}
    </div>
  );
}

