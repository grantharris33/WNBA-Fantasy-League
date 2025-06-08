import React, { useState, useEffect } from 'react';

const WaiverCountdown: React.FC = () => {
  const [timeUntilProcessing, setTimeUntilProcessing] = useState<string>('');

  useEffect(() => {
    const calculateTimeUntilProcessing = () => {
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(3, 0, 0, 0); // 3:00 AM UTC next day

      // If it's already past 3 AM today, use tomorrow's 3 AM
      if (now.getHours() >= 3) {
        tomorrow.setDate(tomorrow.getDate() + 1);
      }

      const diffMs = tomorrow.getTime() - now.getTime();
      
      if (diffMs <= 0) {
        setTimeUntilProcessing('Processing...');
        return;
      }

      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);

      setTimeUntilProcessing(`${hours}h ${minutes}m ${seconds}s`);
    };

    // Update immediately
    calculateTimeUntilProcessing();

    // Update every second
    const interval = setInterval(calculateTimeUntilProcessing, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-right">
      <div className="text-sm text-gray-500">Next waiver processing:</div>
      <div className="text-lg font-bold text-indigo-600">
        {timeUntilProcessing}
      </div>
      <div className="text-xs text-gray-400">
        Daily at 3:00 AM UTC
      </div>
    </div>
  );
};

export default WaiverCountdown;