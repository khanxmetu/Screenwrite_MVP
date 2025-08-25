// Set to true for production, false for development
const isProduction = false;

export const getApiBaseUrl = (fastapi: boolean = false): string => {
  if (!isProduction) {
    return fastapi ? "http://127.0.0.1:8001" : "http://localhost:8000";
  }

  if (typeof window !== "undefined" && !fastapi) {
    return `${window.location.origin}/api`;
  } else if (typeof window !== "undefined" && fastapi) {
    return `${window.location.origin}/ai/api`;
  }

  // Fallback for SSR or other environments (idk)
  return "/api";
};

export const apiUrl = (endpoint: string, fastapi: boolean = false): string => {
  const baseUrl = getApiBaseUrl(fastapi);
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

// New interface for AI composition generation
export interface ConversationMessage {
  user_request: string;
  ai_response: string;
  generated_code: string;
  timestamp: string;
}

export interface CompositionRequest {
  user_request: string;
  current_content: any[];
  preview_settings: any;
  media_library?: any[]; // Optional list of available media files
  current_generated_code?: string; // Optional current AI-generated TSX code for context
  conversation_history?: ConversationMessage[]; // Past requests and responses for context
}

export interface CompositionResponse {
  composition_code: string;
  content_data: any[];
  explanation: string;
  duration: number;
  success: boolean;
  error_message?: string;
}

// Error correction interfaces
export interface CodeFixRequest {
  broken_code: string;
  error_message: string;
  error_stack?: string;
  media_library?: any[];
}

export interface CodeFixResponse {
  corrected_code: string;
  explanation: string;
  duration: number;
  success: boolean;
  error_message?: string;
}

// Function to generate composition via AI
export async function generateComposition(request: CompositionRequest): Promise<CompositionResponse> {
  try {
    const response = await fetch(apiUrl("/ai/generate-composition", true), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error generating composition:", error);
    return {
      composition_code: "",
      content_data: [],
      explanation: "Failed to generate composition",
      duration: 0,
      success: false,
      error_message: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

// Function to fix broken code via AI
export async function fixCode(request: CodeFixRequest): Promise<CodeFixResponse> {
  try {
    const response = await fetch(apiUrl("/ai/fix-code", true), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fixing code:", error);
    return {
      corrected_code: request.broken_code, // Return original as fallback
      explanation: "Failed to fix code",
      duration: 10.0,
      success: false,
      error_message: error instanceof Error ? error.message : "Unknown error",
    };
  }
}