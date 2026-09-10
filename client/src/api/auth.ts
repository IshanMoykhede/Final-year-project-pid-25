import { apiClient } from './client';

export interface LoginParams {
  email: string;
  password: string;
}

export interface RegisterParams {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  message: string;
}

export const loginUser = async (data: LoginParams): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);
  return response.data;
};

export const registerUser = async (data: RegisterParams): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/register', data);
  return response.data;
};
