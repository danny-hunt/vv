import { Button } from "./ui/button";
import { Plus, X } from "lucide-react";

interface FloatingControlsProps {
  activePaneCount: number;
  onAddPane: () => void;
  onRemovePane: () => void;
  canRemove: boolean;
}

export function FloatingControls({
  activePaneCount,
  onAddPane,
  onRemovePane,
  canRemove,
}: FloatingControlsProps) {
  const canAdd = activePaneCount < 6;
  const showRemove = activePaneCount > 1;

  return (
    <div className="fixed bottom-6 left-6 flex gap-3 z-50">
      {canAdd && (
        <Button
          size="lg"
          onClick={onAddPane}
          className="rounded-full w-14 h-14 shadow-lg"
        >
          <Plus className="h-6 w-6" />
        </Button>
      )}

      {showRemove && (
        <Button
          size="lg"
          variant="destructive"
          onClick={onRemovePane}
          disabled={!canRemove}
          className="rounded-full w-14 h-14 shadow-lg"
        >
          <X className="h-6 w-6" />
        </Button>
      )}
    </div>
  );
}

