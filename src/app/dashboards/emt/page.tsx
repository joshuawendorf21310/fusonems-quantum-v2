"use client";
import { PageShell } from "@/components/PageShell";
import { DashboardRenderer } from "@/lib/dashboards/widgets";
import { paramedic } from "@/lib/dashboards/dashboard-schema";
export default function EmtDashboard() {
  const emtSchema = { ...paramedic, title: "EMT Dashboard", description: "EMT performance metrics" };
  return (
    <PageShell title="EMT Dashboard" requireAuth={true}>
      <DashboardRenderer schema={emtSchema} title={emtSchema.title} description={emtSchema.description} />
    </PageShell>
  );
}
