export function canAccessRoute(role: string, route: string): boolean {
  if (route.startsWith("/founder")) {
    return role === "founder";
  }
  if (route.startsWith("/billing")) {
    return ["billing", "admin", "founder"].includes(role);
  }
  if (route.startsWith("/clinical")) {
    return ["crew", "admin", "founder"].includes(role);
  }
  if (route.startsWith("/compliance")) {
    return role === "compliance";
  }
  return true;
}
