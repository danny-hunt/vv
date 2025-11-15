export interface Pane {
  pane_id: number;
  active: boolean;
  branch: string | null;
  is_ahead: boolean;
  is_stale: boolean;
  agent_running: boolean;
  is_updating: boolean;
  is_merging: boolean;
  title?: string;
}

export interface OrchestrationState {
  panes: Pane[];
}

export interface MergeQueueItem {
  pane_id: number;
  status: string;
}

export interface MergeQueue {
  queue: MergeQueueItem[];
  in_progress: boolean;
}

export interface AgentRequest {
  prompt: string;
}

export interface CreatePaneResponse {
  pane_id: number;
  branch: string;
  status: string;
  message: string;
}
