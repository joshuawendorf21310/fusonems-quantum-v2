import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

/**
 * Ensures the site root (/) always serves the marketing landing page,
 * never the founder/admin console. Do not add rewrites that send "/" to "/founder".
 * If production still shows admin at root, check nginx/hosting rewrites for fusionemsquantum.com.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Root must serve the landing page (app/page.tsx). Never rewrite to /founder.
  if (pathname === "/") {
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: "/",
}
