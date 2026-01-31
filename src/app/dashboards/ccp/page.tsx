"use client";
import { PageShell } from "@/components/PageShell";
import { DashboardRenderer } from "@/lib/dashboards/widgets";
import { paramedic } from "@/lib/dashboards/dashboard-schema";
export default function CcpDashboard() {
  const ccpSchema = { ...paramedic, title: "CCP Dashboard", description: "Critical Care Paramedic metrics" };
  return (
    <PageShell title="Community Care Paramedic Dashboard" requireAuth={true}>
      <DashboardRenderer schema={ccpSchema} title={ccpSchema.title} description={ccpSchema.description} />
    </PageShell>
  );
}
