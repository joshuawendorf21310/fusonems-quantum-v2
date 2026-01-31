"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type FireScheduleShift = {
  shift_id: string;
  shift_name: string;
  shift_type: string;
  start_time: string;
  end_time: string;
  station_name: string;
  capacity: number;
  assigned_personnel: Array<{ personnel_id: number; personnel_name: string; role: string }>;
  status: string;
};

const glassmorphism = {
  background: "rgba(17, 17, 17, 0.8)",
  backdropFilter: "blur(10px)",
  border: "1px solid rgba(255, 107, 53, 0.2)",
};

export default function FireScheduling() {
  const router = useRouter();
  const [shifts, setShifts] = useState<FireScheduleShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "calendar">("list");
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    setLoading(true);
    apiFetch<FireScheduleShift[]>("/fire/schedule/shifts")
      .then(setShifts)
      .catch(() => setError("Failed to load shifts."))
      .finally(() => setLoading(false));
  }, []);

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const shiftsForDate = (date: Date) => {
    return shifts.filter((shift) => {
      const shiftDate = new Date(shift.start_time);
      return (
        shiftDate.getFullYear() === date.getFullYear() &&
        shiftDate.getMonth() === date.getMonth() &&
        shiftDate.getDate() === date.getDate()
      );
    });
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(selectedDate);
    const firstDay = getFirstDayOfMonth(selectedDate);
    const days = [];

    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day));
    }

    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "1rem" }}>
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
          <div
            key={day}
            style={{
              textAlign: "center",
              fontSize: "12px",
              fontWeight: 700,
              color: "#ff6b35",
              padding: "1rem 0",
              borderBottom: "1px solid rgba(255, 107, 53, 0.2)",
            }}
          >
            {day}
          </div>
        ))}
        {days.map((date, idx) => {
          const dayShifts = date ? shiftsForDate(date) : [];
          const isToday =
            date &&
            new Date().toDateString() === date.toDateString();

          return (
            <div
              key={idx}
              onClick={() => date && router.push(`/fire/schedule/${date.toISOString().split("T")[0]}`)}
              style={{
                ...glassmorphism,
                padding: "1rem",
                minHeight: "120px",
                cursor: date ? "pointer" : "default",
                transition: "all 0.3s ease",
                border: isToday ? "2px solid rgba(255, 107, 53, 0.8)" : "1px solid rgba(255, 107, 53, 0.2)",
                opacity: date ? 1 : 0.3,
              } as React.CSSProperties}
              onMouseEnter={(e) => {
                if (date) {
                  (e.currentTarget as HTMLDivElement).style.background = "rgba(25, 25, 25, 0.9)";
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(-4px)";
                }
              }}
              onMouseLeave={(e) => {
                if (date) {
                  (e.currentTarget as HTMLDivElement).style.background = "rgba(17, 17, 17, 0.8)";
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
                }
              }}
            >
              {date && (
                <>
                  <div style={{ fontSize: "16px", fontWeight: 800, color: "#ff6b35", marginBottom: "0.5rem" }}>
                    {date.getDate()}
                  </div>
                  {dayShifts.length > 0 ? (
                    <div style={{ fontSize: "12px", color: "#aaa" }}>
                      <div style={{ color: "#6fc96f", fontWeight: 600, marginBottom: "4px" }}>
                        {dayShifts.length} shift{dayShifts.length > 1 ? "s" : ""}
                      </div>
                      {dayShifts.slice(0, 2).map((shift) => (
                        <div key={shift.shift_id} style={{ fontSize: "10px", color: "#888", marginBottom: "2px" }}>
                          {shift.shift_name}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: "12px", color: "#555" }}>No shifts</div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #000000 0%, #0a0a0a 100%)",
        color: "#f7f6f3",
        minHeight: "100vh",
        padding: "3rem 2rem",
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}
    >
      <div style={{ maxWidth: "1600px", margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "3rem",
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "3rem",
                fontWeight: 800,
                letterSpacing: "-1px",
                background: "linear-gradient(90deg, #ff6b35 0%, #c41e3a 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Fire Scheduling
            </h1>
            <p style={{ color: "#888", margin: "0.5rem 0 0 0", fontSize: "14px" }}>
              {shifts.length} shifts scheduled • Advanced crew management
            </p>
          </div>
          <div style={{ display: "flex", gap: "1rem" }}>
            <button
              onClick={() => setView("list")}
              style={{
                padding: "12px 24px",
                fontSize: "13px",
                fontWeight: 700,
                background: view === "list" ? "rgba(255, 107, 53, 0.2)" : "transparent",
                color: view === "list" ? "#ff6b35" : "#888",
                border: `1px solid ${view === "list" ? "rgba(255, 107, 53, 0.5)" : "rgba(255, 107, 53, 0.2)"}`,
                cursor: "pointer",
                transition: "all 0.3s ease",
              }}
              onMouseEnter={(e) => {
                if (view !== "list") {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255, 107, 53, 0.5)";
                  (e.currentTarget as HTMLButtonElement).style.color = "#ff6b35";
                }
              }}
              onMouseLeave={(e) => {
                if (view !== "list") {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255, 107, 53, 0.2)";
                  (e.currentTarget as HTMLButtonElement).style.color = "#888";
                }
              }}
            >
              List View
            </button>
            <button
              onClick={() => setView("calendar")}
              style={{
                padding: "12px 24px",
                fontSize: "13px",
                fontWeight: 700,
                background: view === "calendar" ? "rgba(255, 107, 53, 0.2)" : "transparent",
                color: view === "calendar" ? "#ff6b35" : "#888",
                border: `1px solid ${view === "calendar" ? "rgba(255, 107, 53, 0.5)" : "rgba(255, 107, 53, 0.2)"}`,
                cursor: "pointer",
                transition: "all 0.3s ease",
              }}
              onMouseEnter={(e) => {
                if (view !== "calendar") {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255, 107, 53, 0.5)";
                  (e.currentTarget as HTMLButtonElement).style.color = "#ff6b35";
                }
              }}
              onMouseLeave={(e) => {
                if (view !== "calendar") {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255, 107, 53, 0.2)";
                  (e.currentTarget as HTMLButtonElement).style.color = "#888";
                }
              }}
            >
              Calendar
            </button>
            <button
              onClick={() => router.push("/fire/schedule/create")}
              style={{
                background: "linear-gradient(135deg, #ff6b35 0%, #ff4500 100%)",
                color: "#000",
                border: "none",
                padding: "12px 24px",
                fontSize: "13px",
                fontWeight: 700,
                letterSpacing: "0.5px",
                cursor: "pointer",
                transition: "all 0.3s ease",
                boxShadow: "0 10px 30px rgba(255, 107, 53, 0.3)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 15px 45px rgba(255, 107, 53, 0.5)";
                (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 10px 30px rgba(255, 107, 53, 0.3)";
                (e.currentTarget as HTMLButtonElement).style.transform = "translateY(0)";
              }}
            >
              + New Shift
            </button>
          </div>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: "3rem", color: "#666" }}>
            Loading shifts...
          </div>
        )}

        {error && (
          <div
            style={{
              ...glassmorphism,
              borderColor: "rgba(196, 30, 58, 0.5)",
              padding: "1.5rem",
              marginBottom: "2rem",
              color: "#ff6b7a",
            }}
          >
            {error}
          </div>
        )}

        {!loading && view === "calendar" && (
          <div
            style={{
              ...glassmorphism,
              padding: "2rem",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "2rem",
              }}
            >
              <button
                onClick={() => setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() - 1))}
                style={{
                  background: "transparent",
                  color: "#ff6b35",
                  border: "1px solid rgba(255, 107, 53, 0.5)",
                  padding: "8px 16px",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: "13px",
                }}
              >
                ← Prev
              </button>
              <h2
                style={{
                  margin: 0,
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "#ff6b35",
                }}
              >
                {selectedDate.toLocaleString("default", { month: "long", year: "numeric" })}
              </h2>
              <button
                onClick={() => setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1))}
                style={{
                  background: "transparent",
                  color: "#ff6b35",
                  border: "1px solid rgba(255, 107, 53, 0.5)",
                  padding: "8px 16px",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: "13px",
                }}
              >
                Next →
              </button>
            </div>
            {renderCalendar()}
          </div>
        )}

        {!loading && view === "list" && (
          <div style={{ display: "grid", gap: "1rem" }}>
            {shifts.length === 0 ? (
              <div
                style={{
                  ...glassmorphism,
                  padding: "3rem",
                  textAlign: "center",
                  color: "#666",
                }}
              >
                No shifts scheduled.
              </div>
            ) : (
              shifts.map((shift) => (
                <div
                  key={shift.shift_id}
                  onClick={() => router.push(`/fire/schedule/${shift.shift_id}`)}
                  style={{
                    ...glassmorphism,
                    padding: "1.5rem",
                    cursor: "pointer",
                    transition: "all 0.3s ease",
                    display: "grid",
                    gridTemplateColumns: "2fr 1.5fr 1fr 1.5fr 1fr",
                    gap: "1.5rem",
                    alignItems: "center",
                  } as React.CSSProperties}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLDivElement).style.background = "rgba(25, 25, 25, 0.9)";
                    (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255, 107, 53, 0.4)";
                    (e.currentTarget as HTMLDivElement).style.transform = "translateX(8px)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLDivElement).style.background = "rgba(17, 17, 17, 0.8)";
                    (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255, 107, 53, 0.2)";
                    (e.currentTarget as HTMLDivElement).style.transform = "translateX(0)";
                  }}
                >
                  <div>
                    <div style={{ fontSize: "12px", color: "#888", marginBottom: "4px" }}>SHIFT</div>
                    <div style={{ fontSize: "15px", fontWeight: 600, color: "#ff6b35" }}>
                      {shift.shift_name}
                    </div>
                    <div style={{ fontSize: "12px", color: "#aaa", marginTop: "4px" }}>
                      {shift.station_name}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", color: "#888", marginBottom: "4px" }}>TIME</div>
                    <div style={{ fontSize: "13px", color: "#f7f6f3" }}>
                      {new Date(shift.start_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}{" "}
                      −{" "}
                      {new Date(shift.end_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", color: "#888", marginBottom: "4px" }}>TYPE</div>
                    <div style={{ fontSize: "13px", color: "#f7f6f3" }}>
                      {shift.shift_type}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: "12px", color: "#888", marginBottom: "4px" }}>CREW</div>
                    <div style={{ fontSize: "13px", color: "#6fc96f", fontWeight: 600 }}>
                      {shift.assigned_personnel.length}/{shift.capacity}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div
                      style={{
                        display: "inline-block",
                        padding: "8px 16px",
                        fontSize: "12px",
                        fontWeight: 700,
                        color: "#ff6b35",
                        border: "1px solid rgba(255, 107, 53, 0.5)",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLDivElement).style.background = "rgba(255, 107, 53, 0.1)";
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLDivElement).style.background = "transparent";
                      }}
                    >
                      View →
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
