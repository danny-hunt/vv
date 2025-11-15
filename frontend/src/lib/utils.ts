import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PANE_LABELS = ["apricot", "banana", "cucumber", "dragonfruit", "eggplant", "fennel"];

/**
 * Get the fruit/vegetable label for a pane by its ID (1-indexed)
 */
export function getPaneLabel(paneId: number): string {
  return PANE_LABELS[paneId - 1] || `pane-${paneId}`;
}
