export type AwaitableRouteContext<P extends Record<string, string>> =
  ({ params: P } | { params: Promise<P> }) & { [key: string]: unknown };
