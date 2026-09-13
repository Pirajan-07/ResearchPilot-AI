import { 
  PaperSummaryResponse, 
  PaperInsightsResponse,
  UploadResponse,
  DocumentStatusResponse,
  QueryResponse
} from "@/types/analysis";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/documents/`, {
    method: "POST",
    body: formData,
    // Note: Do not set Content-Type header manually when using FormData, 
    // the browser sets it automatically with the correct boundary.
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to upload document (HTTP ${response.status})`);
  }

  return response.json();
}

export async function listDocuments(): Promise<DocumentStatusResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to fetch documents (HTTP ${response.status})`);
  }
  
  return response.json();
}

export async function getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to fetch document status (HTTP ${response.status})`);
  }
  
  return response.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: "DELETE",
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to delete document (HTTP ${response.status})`);
  }
}

export async function queryDocument(documentId: string, question: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to query document (HTTP ${response.status})`);
  }
  
  return response.json();
}

export async function fetchSummary(documentId: string): Promise<PaperSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/summary`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to fetch summary (HTTP ${response.status})`);
  }
  
  return response.json();
}

export async function fetchInsights(documentId: string): Promise<PaperInsightsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/insights`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Failed to fetch insights (HTTP ${response.status})`);
  }
  
  return response.json();
}
