import { Button } from "./ui/button";
import { Plus, Loader2 } from "lucide-react";

interface FloatingControlsProps {
  activePaneCount: number;
  onAddPane: () => void;
  isCreatingPane: boolean;
}

export function FloatingControls({ activePaneCount, onAddPane, isCreatingPane }: FloatingControlsProps) {
  const canAdd = activePaneCount < 6;

  return (
    <div className="fixed bottom-6 left-6 flex gap-3 z-50">
      {canAdd && (
        <Button
          onClick={onAddPane}
          disabled={isCreatingPane}
          className="rounded-full w-14 h-14 shadow-lg flex items-center justify-center"
        >
          {isCreatingPane ? (
            <Loader2 className="h-6 w-6 animate-spin" style={{ color: "var(--primary-foreground)" }} />
          ) : (
            <Plus className="h-6 w-6" style={{ color: "var(--primary-foreground)" }} />
          )}
        </Button>
      )}
    </div>
  );
}
