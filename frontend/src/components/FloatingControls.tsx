import { Button } from "./ui/button";
import { Plus } from "lucide-react";

interface FloatingControlsProps {
  activePaneCount: number;
  onAddPane: () => void;
}

export function FloatingControls({ activePaneCount, onAddPane }: FloatingControlsProps) {
  const canAdd = activePaneCount < 6;

  return (
    <div className="fixed bottom-6 left-6 flex gap-3 z-50">
      {canAdd && (
        <Button onClick={onAddPane} className="rounded-full w-14 h-14 shadow-lg flex items-center justify-center">
          <Plus className="h-6 w-6" style={{ color: "var(--primary-foreground)" }} />
        </Button>
      )}
    </div>
  );
}
