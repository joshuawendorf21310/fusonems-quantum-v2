"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiFetch } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"

export default function RegisterPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    organization_name: "",
    role: "user",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (isAuthenticated) {
    router.push("/dashboard")
    return null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await apiFetch<{ access_token: string }>(
        "/auth/register",
        {
          method: "POST",
          body: JSON.stringify(formData),
        }
      )
      localStorage.setItem("token", response.access_token)
      router.push("/dashboard")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page-shell">
      <div className="page-container">
        <div className="glass-panel" style={{ maxWidth: "480px", margin: "auto", marginTop: "40px" }}>
          <h1 style={{ fontSize: "1.875rem", marginBottom: "8px", color: "#ff7c29" }}>
            Create Account
          </h1>
          <p style={{ color: "rgba(247, 246, 243, 0.72)", marginBottom: "32px" }}>
            Join FusionEMS Quantum
          </p>

          {error && (
            <div
              style={{
                padding: "12px",
                marginBottom: "20px",
                backgroundColor: "rgba(255, 77, 79, 0.1)",
                border: "1px solid rgba(255, 77, 79, 0.3)",
                borderRadius: "8px",
                color: "#ff4d4f",
                fontSize: "0.875rem",
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label
                htmlFor="full_name"
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  letterSpacing: "0.2em",
                  color: "#ff7c29",
                  marginBottom: "8px",
                  textTransform: "uppercase",
                }}
              >
                Full Name
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                value={formData.full_name}
                onChange={handleChange}
                required
                className="form-field"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "rgba(10, 10, 10, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "8px",
                  color: "#f7f6f3",
                  fontSize: "0.95rem",
                }}
              />
            </div>

            <div>
              <label
                htmlFor="email"
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  letterSpacing: "0.2em",
                  color: "#ff7c29",
                  marginBottom: "8px",
                  textTransform: "uppercase",
                }}
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="form-field"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "rgba(10, 10, 10, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "8px",
                  color: "#f7f6f3",
                  fontSize: "0.95rem",
                }}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  letterSpacing: "0.2em",
                  color: "#ff7c29",
                  marginBottom: "8px",
                  textTransform: "uppercase",
                }}
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="form-field"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "rgba(10, 10, 10, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "8px",
                  color: "#f7f6f3",
                  fontSize: "0.95rem",
                }}
              />
            </div>

            <div>
              <label
                htmlFor="organization_name"
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  letterSpacing: "0.2em",
                  color: "#ff7c29",
                  marginBottom: "8px",
                  textTransform: "uppercase",
                }}
              >
                Organization Name
              </label>
              <input
                id="organization_name"
                name="organization_name"
                type="text"
                value={formData.organization_name}
                onChange={handleChange}
                required
                className="form-field"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "rgba(10, 10, 10, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "8px",
                  color: "#f7f6f3",
                  fontSize: "0.95rem",
                }}
              />
            </div>

            <div>
              <label
                htmlFor="role"
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  letterSpacing: "0.2em",
                  color: "#ff7c29",
                  marginBottom: "8px",
                  textTransform: "uppercase",
                }}
              >
                Role
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  backgroundColor: "rgba(10, 10, 10, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "8px",
                  color: "#f7f6f3",
                  fontSize: "0.95rem",
                }}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
                <option value="operator">Operator</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="cta-button cta-primary"
              style={{
                marginTop: "8px",
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p style={{ marginTop: "24px", fontSize: "0.875rem", color: "rgba(247, 246, 243, 0.72)", textAlign: "center" }}>
            Already have an account?{" "}
            <Link
              href="/login"
              style={{
                color: "#ff7c29",
                fontWeight: "600",
              }}
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
