import { QueryClient } from "@tanstack/react-query";

// Shared query client for the CRM. Keep list/master data fresh whenever a user
// opens a menu again or returns to the browser after another user has changed data.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Do not treat CRM records as fresh for long periods. Each mounted menu
      // should request the latest server state instead of showing an old cache.
      staleTime: 0,
      gcTime: 30 * 60 * 1000,
      refetchOnMount: "always",
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
  },
});
