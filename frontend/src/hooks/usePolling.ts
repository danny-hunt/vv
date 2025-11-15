import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { OrchestrationState } from "@/types";

export function usePolling(interval: number = 5000) {
  const [orchestrationState, setOrchestrationState] = useState<OrchestrationState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const fetchOrchestrationState = async () => {
      try {
        const state = await apiClient.getOrchestrationState();
        if (isMounted) {
          setOrchestrationState(state);
          setError(null);
          setIsLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unknown error");
          setIsLoading(false);
        }
      } finally {
        if (isMounted) {
          timeoutId = setTimeout(fetchOrchestrationState, interval);
        }
      }
    };

    fetchOrchestrationState();

    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [interval]);

  return { orchestrationState, error, isLoading };
}

