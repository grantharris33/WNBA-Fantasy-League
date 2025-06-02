import React, { useEffect, useState, useRef } from 'react';

interface DraftTimerProps {
  secondsRemainingFromState: number;
  draftStatus: 'pending' | 'active' | 'paused' | 'completed';
  onTimerExpire?: () => void; // Optional: callback when timer reaches zero
}

const DraftTimer: React.FC<DraftTimerProps> = ({ secondsRemainingFromState, draftStatus, onTimerExpire }) => {
  const [timeLeft, setTimeLeft] = useState(secondsRemainingFromState);
  const hasExpiredRef = useRef(false);

  useEffect(() => {
    // Update timer when the state from props changes (e.g., after a pick, pause, resume, or sync)
    console.log(`[DraftTimer] Timer sync: ${timeLeft} -> ${secondsRemainingFromState} (status: ${draftStatus})`);
    setTimeLeft(secondsRemainingFromState);
    // Reset expiration flag when timer resets
    hasExpiredRef.current = false;
  }, [secondsRemainingFromState]);

  useEffect(() => {
    if (draftStatus !== 'active' || timeLeft <= 0) {
      // If timer is already at 0 or draft is not active, ensure no interval is running.
      // If it reached 0 and was active, call onTimerExpire (but only once).
      if (draftStatus === 'active' && timeLeft <= 0 && !hasExpiredRef.current) {
        hasExpiredRef.current = true;
        onTimerExpire?.();
      }
      return; // Don't start an interval if not active or time is up
    }

    const intervalId = setInterval(() => {
      setTimeLeft(prevTime => {
        if (prevTime <= 1) {
          clearInterval(intervalId); // Clear interval when time is about to hit 0
          if (!hasExpiredRef.current) {
            hasExpiredRef.current = true;
            onTimerExpire?.();
          }
          return 0;
        }

        // Always decrement locally - backend sync events will override when needed
        return prevTime - 1;
      });
    }, 1000);

    return () => clearInterval(intervalId); // Cleanup interval on unmount or when deps change

  }, [timeLeft, draftStatus, onTimerExpire]);

  const displayTime = () => {
    if (draftStatus === 'pending') return "-";
    if (draftStatus === 'completed') return "Ended";
    if (draftStatus === 'paused') return "Paused";

    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  const urgencyClass = timeLeft <= 10 && draftStatus === 'active' ? 'text-red-500 font-bold' : 'text-gray-700';

  return (
    <div className="p-3 bg-gray-50 border rounded shadow-sm text-center">
      <div className="text-sm text-gray-500 mb-1">Time Left</div>
      <div className={`text-3xl ${urgencyClass}`}>
        {displayTime()}
      </div>
    </div>
  );
};

export default DraftTimer;