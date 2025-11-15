import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { ChevronDown, ChevronUp, Send } from "lucide-react";
import { useAgentStream } from "@/hooks/useAgentStream";
import { apiClient } from "@/lib/api";
import { generateTitle } from "@/lib/gemini";

interface FloatingWindowProps {
  paneId: number;
  title?: string;
  onTitleGenerated?: (title: string) => void;
}

export function FloatingWindow({ paneId, title, onTitleGenerated }: FloatingWindowProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(!!title);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, isStreaming, error, startStreaming } = useAgentStream({
    paneId,
    onComplete: () => {
      console.log("Agent streaming completed");
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async () => {
    if (!prompt.trim() || isSubmitting || isStreaming) return;

    setIsSubmitting(true);

    try {
      // If this is the first prompt, generate a title
      if (!hasSubmitted && onTitleGenerated) {
        const generatedTitle = await generateTitle(prompt);
        onTitleGenerated(generatedTitle);
        setHasSubmitted(true);
      }

      // Start the agent
      await apiClient.startAgent(paneId, prompt);

      // Start streaming the response
      startStreaming();

      // Clear the prompt
      setPrompt("");
    } catch (err) {
      console.error("Error starting agent:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Card className="absolute top-4 right-4 w-96 shadow-lg z-10">
      <CardHeader className="pb-3 cursor-pointer" onClick={() => setIsCollapsed(!isCollapsed)}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {title || `Pane ${paneId}`}
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
          >
            {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>

      {!isCollapsed && (
        <CardContent className="space-y-3">
          {/* Message history */}
          <ScrollArea className="h-48 w-full rounded border p-3 bg-muted/30">
            <div ref={scrollRef} className="space-y-2">
              {messages.length === 0 && !isStreaming && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No messages yet. Enter a prompt below.
                </p>
              )}
              {messages.map((message, index) => (
                <div key={index} className="text-sm">
                  <pre className="whitespace-pre-wrap font-mono text-xs">{message}</pre>
                </div>
              ))}
              {isStreaming && messages.length === 0 && (
                <p className="text-sm text-muted-foreground">Agent is running...</p>
              )}
              {error && (
                <p className="text-sm text-destructive">Error: {error}</p>
              )}
            </div>
          </ScrollArea>

          {/* Input area */}
          <div className="space-y-2">
            <Textarea
              placeholder="Describe the changes you want..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
              className="min-h-[80px] resize-none"
            />
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim() || isSubmitting || isStreaming}
              className="w-full"
            >
              {isSubmitting ? (
                "Starting..."
              ) : isStreaming ? (
                "Agent Running..."
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Submit
                </>
              )}
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

