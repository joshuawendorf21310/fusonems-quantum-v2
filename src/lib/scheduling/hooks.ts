import { useState, useEffect, useCallback, useRef, useMemo } from "react";

export interface SchedulingEvent {
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export type SchedulingEventHandler = (event: SchedulingEvent) => void;

export interface UseSchedulingWebSocketOptions {
  token: string;
  onShiftCreated?: (data: Record<string, unknown>) => void;
  onShiftUpdated?: (data: Record<string, unknown>) => void;
  onShiftDeleted?: (data: { shift_id: number }) => void;
  onAssignmentCreated?: (data: Record<string, unknown>) => void;
  onAssignmentRemoved?: (data: { assignment_id: number }) => void;
  onYouWereAssigned?: (data: Record<string, unknown>) => void;
  onYourAssignmentRemoved?: (data: { assignment_id: number }) => void;
  onSchedulePublished?: (data: Record<string, unknown>) => void;
  onTimeOffStatusChanged?: (data: Record<string, unknown>) => void;
  onSwapRequestReceived?: (data: Record<string, unknown>) => void;
  onSchedulingAlert?: (data: Record<string, unknown>) => void;
  onConnected?: (data: { user_id: number; org_id: number }) => void;
  onDisconnected?: () => void;
  onError?: (error: Event) => void;
}

export interface UseSchedulingWebSocketReturn {
  isConnected: boolean;
  lastEvent: SchedulingEvent | null;
  connectionAttempts: number;
  reconnect: () => void;
}

export const useSchedulingWebSocket = (
  options: UseSchedulingWebSocketOptions
): UseSchedulingWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SchedulingEvent | null>(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const optionsRef = useRef(options);

  // Keep options ref up to date without causing re-renders
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  // Memoize stable callback references
  const callbacksRef = useMemo(() => ({
    onShiftCreated: options.onShiftCreated,
    onShiftUpdated: options.onShiftUpdated,
    onShiftDeleted: options.onShiftDeleted,
    onAssignmentCreated: options.onAssignmentCreated,
    onAssignmentRemoved: options.onAssignmentRemoved,
    onYouWereAssigned: options.onYouWereAssigned,
    onYourAssignmentRemoved: options.onYourAssignmentRemoved,
    onSchedulePublished: options.onSchedulePublished,
    onTimeOffStatusChanged: options.onTimeOffStatusChanged,
    onSwapRequestReceived: options.onSwapRequestReceived,
    onSchedulingAlert: options.onSchedulingAlert,
    onConnected: options.onConnected,
    onDisconnected: options.onDisconnected,
    onError: options.onError,
  }), [
    options.onShiftCreated,
    options.onShiftUpdated,
    options.onShiftDeleted,
    options.onAssignmentCreated,
    options.onAssignmentRemoved,
    options.onYouWereAssigned,
    options.onYourAssignmentRemoved,
    options.onSchedulePublished,
    options.onTimeOffStatusChanged,
    options.onSwapRequestReceived,
    options.onSchedulingAlert,
    options.onConnected,
    options.onDisconnected,
    options.onError,
  ]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/scheduling/ws?token=${optionsRef.current.token}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setConnectionAttempts(0);
    };

    ws.onclose = () => {
      setIsConnected(false);
      callbacksRef.onDisconnected?.();

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      setConnectionAttempts((prev) => {
        const delay = Math.min(1000 * Math.pow(2, prev), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
        return prev + 1;
      });
    };

    ws.onerror = (error) => {
      callbacksRef.onError?.(error);
    };

    ws.onmessage = (event) => {
      try {
        const message: SchedulingEvent = JSON.parse(event.data);
        setLastEvent(message);

        switch (message.type) {
          case "connected":
            callbacksRef.onConnected?.(message.data as { user_id: number; org_id: number });
            break;
          case "shift_created":
            callbacksRef.onShiftCreated?.(message.data);
            break;
          case "shift_updated":
            callbacksRef.onShiftUpdated?.(message.data);
            break;
          case "shift_deleted":
            callbacksRef.onShiftDeleted?.(message.data as { shift_id: number });
            break;
          case "assignment_created":
            callbacksRef.onAssignmentCreated?.(message.data);
            break;
          case "assignment_removed":
            callbacksRef.onAssignmentRemoved?.(message.data as { assignment_id: number });
            break;
          case "you_were_assigned":
            callbacksRef.onYouWereAssigned?.(message.data);
            break;
          case "your_assignment_removed":
            callbacksRef.onYourAssignmentRemoved?.(message.data as { assignment_id: number });
            break;
          case "schedule_published":
            callbacksRef.onSchedulePublished?.(message.data);
            break;
          case "time_off_status_changed":
            callbacksRef.onTimeOffStatusChanged?.(message.data);
            break;
          case "swap_request_received":
            callbacksRef.onSwapRequestReceived?.(message.data);
            break;
          case "scheduling_alert":
            callbacksRef.onSchedulingAlert?.(message.data);
            break;
        }
      } catch (err) {
        console.error("Failed to parse scheduling WebSocket message:", err);
      }
    };
  }, [callbacksRef]);

  useEffect(() => {
    if (options.token) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect on manual close
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [options.token, connect]);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  return {
    isConnected,
    lastEvent,
    connectionAttempts,
    reconnect,
  };
};

export const useSchedulingData = () => {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [shifts, setShifts] = useState<Record<string, unknown>[]>([]);
  const [mySchedule, setMySchedule] = useState<Record<string, unknown>[]>([]);
  const [alerts, setAlerts] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/scheduling/dashboard/stats", {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch stats");
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchShifts = useCallback(async (startDate?: string, endDate?: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      const response = await fetch(`/api/v1/scheduling/shifts?${params}`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch shifts");
      const data = await response.json();
      setShifts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMySchedule = useCallback(async (startDate?: string, endDate?: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      const response = await fetch(`/api/v1/scheduling/my-schedule?${params}`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch schedule");
      const data = await response.json();
      setMySchedule(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/scheduling/alerts?active_only=true", {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch alerts");
      const data = await response.json();
      setAlerts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    stats,
    shifts,
    mySchedule,
    alerts,
    loading,
    error,
    fetchStats,
    fetchShifts,
    fetchMySchedule,
    fetchAlerts,
    setShifts,
    setAlerts,
  };
};
