import { QueryClient } from "@tanstack/react-query";

// Exported so lib/session can wipe it at session boundaries — cached data outlives logout.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Master data (customers/products/users/options) stays warm for 10 minutes.
      // List query keys include page/filter state, so changing a filter still fetches
      // the correct server-side result without browser-side filtering.
      staleTime: 10 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});
