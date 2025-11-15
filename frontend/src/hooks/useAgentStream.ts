import { useEffect, useState, useCallback } from "react";
import { apiClient } from "@/lib/api";

interface UseAgentStreamOptions {
  paneId: number;
  onComplete?: () => void;
}

export function useAgentStream({ paneId, onComplete }: UseAgentStreamOptions) {
  const [messages, setMessages] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  const startStreaming = useCallback(() => {
    // Close existing connection if any
    if (eventSource) {
      eventSource.close();
    }

    setMessages([]);
    setIsStreaming(true);
    setError(null);

    const es = apiClient.createAgentStreamConnection(paneId);

    es.onmessage = (event) => {
      const data = event.data;

      if (data === "[DONE]") {
        es.close();
        setIsStreaming(false);
        onComplete?.();
      } else {
        setMessages((prev) => [...prev, data]);
      }
    };

    es.onerror = (err) => {
      console.error("SSE error:", err);
      setError("Connection error");
      setIsStreaming(false);
      es.close();
    };

    setEventSource(es);
  }, [paneId, onComplete, eventSource]);

  const stopStreaming = useCallback(() => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
      setIsStreaming(false);
    }
  }, [eventSource]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return {
    messages,
    isStreaming,
    error,
    startStreaming,
    stopStreaming,
  };
}

