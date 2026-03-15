import { useEffect, useRef } from 'react';
import { getWebSocketManager } from '@/lib/ws-client';
import { useNotificationStore } from '@/stores/notificationStore';

export function useWebSocket(engagementId: string | null) {
  const addNotification = useNotificationStore((s) => s.addNotification);
  const connectedRef = useRef(false);

  useEffect(() => {
    if (!engagementId || connectedRef.current) return;

    const ws = getWebSocketManager();
    const token = sessionStorage.getItem('access_token');
    if (!token) return;

    ws.connect(token);
    connectedRef.current = true;

    const unsubFinding = ws.subscribe(`engagement.${engagementId}.findings`, (event) => {
      try {
        const data = JSON.parse(event.data as string);
        addNotification({
          type: 'info',
          title: 'Finding Update',
          message: data.message || 'A finding was updated',
          findingId: data.findingId,
        });
      } catch {
        // ignore parse errors
      }
    });

    const unsubScan = ws.subscribe(`engagement.${engagementId}.scans`, (event) => {
      try {
        const data = JSON.parse(event.data as string);
        addNotification({
          type: 'info',
          title: 'Scan Update',
          message: data.message || 'Scan status changed',
        });
      } catch {
        // ignore parse errors
      }
    });

    return () => {
      unsubFinding();
      unsubScan();
      connectedRef.current = false;
    };
  }, [engagementId, addNotification]);
}
