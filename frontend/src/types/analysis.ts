export interface PaperSummaryResponse {
  overview: string;
  problem: string;
  objectives: string;
  methodology: string;
  dataset: string;
  findings: string;
  limitations: string;
  conclusion: string;
  future_direction: string;
}

export interface PaperInsightsResponse {
  problem: string;
  methodology: string;
  dataset: string;
  contribution: string;
  findings: string[];
  limitations: string[];
  future_direction: string;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface StageStatus {
  name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface DocumentStatusResponse {
  document_id: string;
  filename: string;
  status: string;
  page_count: number;
  chunk_count: number;
  stages: StageStatus[];
  created_at: string;
  completed_at: string | null;
  error: string | null;
  has_summary: boolean;
  has_insights: boolean;
}

export interface SourceReference {
  chunk_id: string;
  page_number: number;
  source_filename: string;
  excerpt: string;
}

export interface QueryResponse {
  document_id: string;
  question: string;
  answer: string;
  sources: SourceReference[];
}
