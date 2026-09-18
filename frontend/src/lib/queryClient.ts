import { QueryClient } from "@tanstack/react-query";

// Shared query client for the CRM.
// Cached data should be rendered immediately when users move between menus.
// Freshness is maintained by explicit invalidation after writes and by
// background refetches, rather than blocking every route mount on MongoDB.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 30 * 60 * 1000,
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      retry: 1,
      retryDelay: 250,
    },
  },
});
