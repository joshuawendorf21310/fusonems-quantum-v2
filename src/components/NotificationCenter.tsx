'use client';

import { useState, useEffect, useRef } from 'react';
import { Bell, X, Check, AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export default function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchNotifications();
    // WebSocket placeholder for real-time updates
    // const ws = new WebSocket('ws://localhost:3000/notifications');
    // ws.onmessage = (event) => {
    //   const newNotification = JSON.parse(event.data);
    //   setNotifications(prev => [newNotification, ...prev]);
    // };
    // return () => ws.close();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/notifications');
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: string) => {
    try {
      const response = await fetch(`/api/notifications/${id}/read`, {
        method: 'POST',
      });
      if (response.ok) {
        setNotifications(prev =>
          prev.map(notif =>
            notif.id === id ? { ...notif, read: true } : notif
          )
        );
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const getTypeIcon = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return <Info className="w-5 h-5 text-blue-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'critical':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getTypeBorder = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return 'border-l-blue-400';
      case 'warning':
        return 'border-l-orange-500';
      case 'critical':
        return 'border-l-red-500';
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-300 hover:text-orange-500 transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl z-50 max-h-[600px] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">
              Notifications
              {unreadCount > 0 && (
                <span className="ml-2 text-sm text-orange-500">
                  ({unreadCount} unread)
                </span>
              )}
            </h3>
            {notifications.length > 0 && (
              <button
                onClick={clearAll}
                className="text-sm text-gray-400 hover:text-orange-500 transition-colors"
              >
                Clear all
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto flex-1">
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 text-gray-500">
                <Bell className="w-12 h-12 mb-2 opacity-50" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-800">
                {notifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`p-4 border-l-4 ${getTypeBorder(notification.type)} ${
                      !notification.read ? 'bg-gray-800/50' : 'bg-transparent'
                    } hover:bg-gray-800/30 transition-colors`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        {getTypeIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4
                            className={`text-sm font-semibold ${
                              !notification.read ? 'text-white' : 'text-gray-300'
                            }`}
                          >
                            {notification.title}
                          </h4>
                          {!notification.read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="flex-shrink-0 text-orange-500 hover:text-orange-400"
                              aria-label="Mark as read"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        <p className="text-sm text-gray-400 mt-1">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(notification.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
