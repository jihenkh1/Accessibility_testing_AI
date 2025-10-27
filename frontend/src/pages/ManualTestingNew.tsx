import React from 'react';
import { ChecklistWizard } from '../components/ChecklistWizard';

export default function ManualTestingNew() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Create Manual Testing Session</h1>
        <p className="text-muted-foreground mt-1">
          Generate a checklist and start testing your application
        </p>
      </div>
      <ChecklistWizard />
    </div>
  );
}
