'use client';

import { Card, CardHeader } from '@/components/common/Card';
import type { PocEnvironment as PocEnvironmentType } from '@/types/poc';

interface PocEnvironmentProps {
  environment: PocEnvironmentType;
}

export function PocEnvironmentDisplay({ environment }: PocEnvironmentProps) {
  return (
    <Card>
      <CardHeader title="PoC Environment" />
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm lg:grid-cols-3">
        <div>
          <span className="text-gray-500">Target</span>
          <p className="font-mono text-gray-900">
            {environment.protocol}://{environment.targetHost}:{environment.targetPort}
          </p>
        </div>
        <div>
          <span className="text-gray-500">Tool</span>
          <p className="text-gray-900">{environment.tool}</p>
        </div>
        <div>
          <span className="text-gray-500">Network</span>
          <p className="text-gray-900">{environment.networkAccess}</p>
        </div>
        <div>
          <span className="text-gray-500">Test Date</span>
          <p className="text-gray-900">{environment.testDate}</p>
        </div>
        <div>
          <span className="text-gray-500">Analyst</span>
          <p className="text-gray-900">{environment.analystName}</p>
        </div>
        <div>
          <span className="text-gray-500">Scope</span>
          <p className="text-gray-900">{environment.scopeAuthorization}</p>
        </div>
      </div>
    </Card>
  );
}
