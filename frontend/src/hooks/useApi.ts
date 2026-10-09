import { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { request } from '@/api/client';
import { ApiError } from '@/types';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
}

export function useApi<T>(fn: () => Promise<T>, options: UseApiOptions<T> = {}) {
  const { immediate = true, onSuccess } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(immediate);

  const run = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      onSuccess?.(result);
      return result;
    } catch (caughtError) {
      const errorMessage = caughtError instanceof AxiosError
        ? caughtError.response?.data?.detail ?? caughtError.message
        : 'Request failed';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [fn, onSuccess]);

  useEffect(() => {
    if (immediate) {
      void run();
    }
  }, [immediate, run]);

  return { data, error, isLoading, run, setData };
}

export function usePaginatedApi<T>(
  fn: (page: number, pageSize: number) => Promise<{ items: T[]; total: number; total_pages: number }>,
  pageSize = 10,
) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (nextPage = page) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fn(nextPage, pageSize);
      setItems(response.items);
      setTotal(response.total);
      setPage(nextPage);
    } catch (caughtError) {
      const detail = caughtError instanceof AxiosError
        ? caughtError.response?.data?.detail ?? caughtError.message
        : 'Unable to load data';
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  }, [fn, page, pageSize]);

  useEffect(() => { void load(1); }, [load]);

  return { items, total, page, isLoading, error, setPage: load, totalPages: Math.ceil(total / pageSize) };
}

export function getApiError(error: unknown): string {
  if (error instanceof AxiosError && error.response?.data) {
    return (error.response.data as ApiError).detail ?? error.message;
  }
  return error instanceof Error ? error.message : 'Request failed';
}

export const apiRequest = request;
