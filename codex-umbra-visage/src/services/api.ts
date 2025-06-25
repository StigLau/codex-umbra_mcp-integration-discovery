import type { ApiResponse, ApiError } from '../types';

const CONDUCTOR_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function postMessageToConductor(text: string): Promise<ApiResponse> {
  try {
    const response = await fetch(`${CONDUCTOR_BASE_URL}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message: text,
        user_id: 'default'
      })
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(`HTTP ${response.status}: ${errorData.detail || 'Unknown error'}`);
    }

    const data: ApiResponse = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

export async function checkConductorHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${CONDUCTOR_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function checkSentinelHealth(): Promise<any> {
  try {
    const response = await fetch(`${CONDUCTOR_BASE_URL}/api/v1/sentinel/health`);
    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch {
    return null;
  }
}
