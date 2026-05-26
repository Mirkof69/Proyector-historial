import React from 'react';

const Statistics: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Statistics</h1>
      <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 shadow">
        <p className="text-zinc-600 dark:text-zinc-400">
          Statistics dashboard. Connect to your backend analytics API to display metrics.
        </p>
      </div>
    </div>
  );
};

export default Statistics;
