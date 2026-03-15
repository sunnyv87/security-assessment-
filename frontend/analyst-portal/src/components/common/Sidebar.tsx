'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useWorkbenchStore } from '@/stores/workbenchStore';

const navItems = [
  { href: '/workbench', label: 'Dashboard', icon: 'grid' },
  { href: '/workbench/triage', label: 'Finding Triage', icon: 'filter' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { engagements, activeEngagementId, setActiveEngagement } = useWorkbenchStore();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50">
      {/* Logo */}
      <div className="flex h-14 items-center border-b border-gray-200 px-4">
        <span className="text-lg font-bold text-gray-900">VAPT Workbench</span>
      </div>

      {/* Engagement selector */}
      <div className="border-b border-gray-200 p-4">
        <label htmlFor="engagement-select" className="block text-xs font-medium text-gray-500">
          Engagement
        </label>
        <select
          id="engagement-select"
          value={activeEngagementId || ''}
          onChange={(e) => setActiveEngagement(e.target.value)}
          className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">Select engagement...</option>
          {engagements.map((eng) => (
            <option key={eng.id} value={eng.id}>
              {eng.customerName} - {eng.name}
            </option>
          ))}
        </select>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-200',
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Filters placeholder */}
      <div className="border-t border-gray-200 p-4">
        <p className="text-xs font-medium text-gray-500">Quick Filters</p>
        <div className="mt-2 space-y-1">
          <button type="button" className="block w-full rounded px-2 py-1 text-left text-sm text-gray-600 hover:bg-gray-200">
            My Assigned
          </button>
          <button type="button" className="block w-full rounded px-2 py-1 text-left text-sm text-gray-600 hover:bg-gray-200">
            Needs Review
          </button>
          <button type="button" className="block w-full rounded px-2 py-1 text-left text-sm text-gray-600 hover:bg-gray-200">
            Critical Only
          </button>
        </div>
      </div>
    </aside>
  );
}
