export interface IMessage {
  id: string;
  text: string;
  type: 'user' | 'system';
  timestamp: string;
}

export interface ApiResponse {
  response: string;
  timestamp: string;
}

export interface ApiError {
  detail: string;
  code?: string;
}
