import type { RouteModuleHandleContext } from "next/dist/server/route-modules/route-module";

declare module "next/dist/server/route-modules/route-module" {
  interface RouteModuleHandleContext {
    params:
      | Record<string, string | string[] | undefined>
      | undefined
      | Promise<Record<string, string | string[] | undefined> | undefined>;
  }
}
