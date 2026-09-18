import { QueryClient } from "@tanstack/react-query";

// Shared query client for the CRM.
//
// The previous global policy used staleTime=0 + refetchOnMount="always".
// That forced almost every menu navigation to wait for another database
// request, even when the same data had just been loaded. Keep a short freshness
// window instead: cached data renders immediately, while stale data can refresh
// in the background when appropriate.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // CRM master/list data changes, but normally does not need a round-trip
      // on every route mount. This makes menu-to-menu navigation instant when
      // the query is already cached.
      staleTime: 15_000,
      gcTime: 30 * 60 * 1000,
      refetchOnMount: true,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: 1,
      retryDelay: 250,
    },
  },
});
