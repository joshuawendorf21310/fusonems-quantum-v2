import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MessageSquare, RefreshCw } from "lucide-react";

interface AgencyMessage {
  id: number;
  subject: string;
  preview: string;
  from: string;
  timestamp: string;
}

export const AgencyMessagingWidget = () => {
  const [messages, setMessages] = useState<AgencyMessage[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      // This endpoint is from the documentation.
      const response = await fetch('/api/agency/messages');
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error("Failed to fetch agency messages:", error);
      setMessages([]); // Clear messages on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center"><MessageSquare className="mr-2" /> Agency Messaging</CardTitle>
        <Button variant="ghost" size="sm" onClick={fetchMessages} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>
      <CardContent>
        {loading && <p className="text-sm text-gray-500">Loading messages...</p>}
        {!loading && messages.length === 0 && (
          <p className="text-sm text-gray-500">No new messages from agencies.</p>
        )}
        {!loading && messages.length > 0 && (
          <ul className="space-y-3">
            {messages.map((message) => (
              <li key={message.id} className="flex flex-col p-2 border-l-4 border-blue-500 rounded-r-md bg-gray-50 hover:bg-gray-100 transition-colors">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-sm">{message.subject}</span>
                  <span className="text-xs text-gray-400">{new Date(message.timestamp).toLocaleDateString()}</span>
                </div>
                <p className="text-sm text-gray-600 truncate">{message.preview}</p>
                <span className="text-xs text-gray-500 self-end mt-1">From: {message.from}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
};
