'use client';

import { Sidebar } from '@/components/common/Sidebar';
import { useEngagement } from '@/hooks/useEngagement';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useWorkbenchStore } from '@/stores/workbenchStore';
import { useNotificationStore } from '@/stores/notificationStore';
import type { ReactNode } from 'react';

interface WorkbenchLayoutProps {
  children: ReactNode;
}

export function WorkbenchLayout({ children }: WorkbenchLayoutProps) {
  const activeEngagementId = useWorkbenchStore((s) => s.activeEngagementId);
  const unreadCount = useNotificationStore((s) => s.unreadCount);

  // Load engagements and connect WebSocket
  useEngagement(activeEngagementId);
  useWebSocket(activeEngagementId);

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
          <div />
          <div className="flex items-center gap-4">
            {unreadCount > 0 && (
              <span className="flex h-6 min-w-[1.5rem] items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-medium text-white">
                {unreadCount}
              </span>
            )}
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-medium text-white">
              A
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
