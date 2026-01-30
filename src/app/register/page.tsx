"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function RegisterPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to request access page
    router.replace("/request-access")
  }, [router])

  // Show message while redirecting
  return (
    <main className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 shadow-2xl text-center space-y-4">
          <h1 className="text-2xl font-bold text-white">Registration Disabled</h1>
          <p className="text-gray-400">
            Account creation requires approval. Please request access instead.
          </p>
          <Link
            href="/request-access"
            className="inline-block mt-4 px-6 py-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-orange-500/20 transition-all"
          >
            Request Access
          </Link>
          <p className="text-sm text-gray-500 mt-4">
            <Link href="/login" className="text-orange-500 hover:text-orange-400">
              Return to Login
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
