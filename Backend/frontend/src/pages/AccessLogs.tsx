import React from 'react';

const AccessLogs: React.FC = () => {

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Access Logs</h1>
      <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 shadow">
        <p className="text-zinc-600 dark:text-zinc-400">
          Access logs module. Connect to your backend audit API to display user access history.
        </p>
      </div>
    </div>
  );
};

export default AccessLogs;
