import type {
  OrchestrationState,
  MergeQueue,
  AgentRequest,
  CreatePaneResponse,
} from "@/types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async createPane(paneId: number): Promise<CreatePaneResponse> {
    const response = await fetch(`${this.baseUrl}/api/panes/${paneId}/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to create pane");
    }

    return response.json();
  }

  async getOrchestrationState(): Promise<OrchestrationState> {
    const response = await fetch(`${this.baseUrl}/api/orchestration`);

    if (!response.ok) {
      throw new Error("Failed to fetch orchestration state");
    }

    return response.json();
  }

  async startAgent(paneId: number, prompt: string): Promise<{ status: string; message: string }> {
    const request: AgentRequest = { prompt };
    const response = await fetch(`${this.baseUrl}/api/panes/${paneId}/agent`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to start agent");
    }

    return response.json();
  }

  createAgentStreamConnection(paneId: number): EventSource {
    return new EventSource(`${this.baseUrl}/api/panes/${paneId}/agent/stream`);
  }

  async mergePane(paneId: number): Promise<{ status: string; message: string; queue_position?: number }> {
    const response = await fetch(`${this.baseUrl}/api/panes/${paneId}/merge`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to merge pane");
    }

    return response.json();
  }

  async getMergeQueue(): Promise<MergeQueue> {
    const response = await fetch(`${this.baseUrl}/api/merge-queue`);

    if (!response.ok) {
      throw new Error("Failed to fetch merge queue");
    }

    return response.json();
  }

  async deletePane(paneId: number): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/panes/${paneId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to delete pane");
    }

    return response.json();
  }
}

export const apiClient = new ApiClient(API_URL);

