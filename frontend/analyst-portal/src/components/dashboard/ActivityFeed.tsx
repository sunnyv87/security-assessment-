'use client';

import { Card, CardHeader } from '@/components/common/Card';
import { formatDistanceToNow } from 'date-fns';
import type { ActivityEvent } from '@/types/api';

interface ActivityFeedProps {
  events: ActivityEvent[];
}

const typeIcons: Record<ActivityEvent['type'], string> = {
  validation: '\u2713',
  poc: '\u25CF',
  severity_change: '\u25B2',
  assignment: '\u2192',
  note: '\u270E',
  status_change: '\u25CB',
};

export function ActivityFeed({ events }: ActivityFeedProps) {
  return (
    <Card>
      <CardHeader title="Recent Activity" />
      <div className="mt-4 space-y-3">
        {events.map((event) => (
          <div key={event.id} className="flex items-start gap-3 rounded-md p-2 hover:bg-gray-50">
            <span className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-xs">
              {typeIcons[event.type]}
            </span>
            <div className="flex-1 text-sm">
              <p className="text-gray-900">{event.description}</p>
              <p className="mt-0.5 text-xs text-gray-500">
                {event.actorName} &middot; {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
              </p>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <p className="text-sm text-gray-500">No recent activity</p>
        )}
      </div>
    </Card>
  );
}
