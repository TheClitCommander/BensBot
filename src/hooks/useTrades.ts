import { useQuery } from '@tanstack/react-query';
import { api } from '../utils/api';

export interface Trade {
  id: number;
  symbol: string;
  date: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  total: number;
}

export interface TradesData {
  trades: Trade[];
}

export function useTrades() {
  return useQuery({
    queryKey: ['trades'],
    queryFn: async () => {
      const response = await api.get('/trades');
      return response.data;
    },
    refetchInterval: 300000,  // Refresh data every 5 minutes
    staleTime: 600000,        // Keep data for 10 minutes if window loses focus
  });
} 