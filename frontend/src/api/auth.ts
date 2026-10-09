import { request } from './client';
import { TokenResponse, User } from '@/types';

export const login = (email: string, password: string) =>
  request<TokenResponse>({ method: 'POST', url: '/auth/login', data: { email, password } });

export const refreshToken = (refreshToken: string) =>
  request<TokenResponse>({ method: 'POST', url: '/auth/refresh', data: { refresh_token: refreshToken } });

export const getCurrentUser = () => request<User>({ method: 'GET', url: '/auth/me' });
