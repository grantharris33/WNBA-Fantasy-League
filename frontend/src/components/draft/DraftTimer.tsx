import React, { useEffect, useState, useRef } from 'react';

interface DraftTimerProps {
  secondsRemainingFromState: number;
  draftStatus: 'pending' | 'active' | 'paused' | 'completed';
  draftDate?: string | null; // ISO datetime string for when draft is scheduled
  onTimerExpire?: () => void; // Optional: callback when timer reaches zero
}

const DraftTimer: React.FC<DraftTimerProps> = ({
  secondsRemainingFromState,
  draftStatus,
  draftDate,
  onTimerExpire
}) => {
  const [timeLeft, setTimeLeft] = useState(secondsRemainingFromState);
  const [countdownToStart, setCountdownToStart] = useState<number | null>(null);
  const hasExpiredRef = useRef(false);

  // Calculate countdown to draft start
  useEffect(() => {
    if (draftStatus === 'pending' && draftDate) {
      const draftTime = new Date(draftDate).getTime();
      const now = new Date().getTime();
      const secondsUntilStart = Math.max(0, Math.floor((draftTime - now) / 1000));
      setCountdownToStart(secondsUntilStart);
    } else {
      setCountdownToStart(null);
    }
  }, [draftStatus, draftDate]);

  useEffect(() => {
    // Update timer when the state from props changes (e.g., after a pick, pause, resume, or sync)
    console.log(`[DraftTimer] Timer sync: ${timeLeft} -> ${secondsRemainingFromState} (status: ${draftStatus})`);
    setTimeLeft(secondsRemainingFromState);
    // Reset expiration flag when timer resets
    hasExpiredRef.current = false;
  }, [secondsRemainingFromState]);

  // Handle countdown to draft start
  useEffect(() => {
    if (draftStatus === 'pending' && countdownToStart !== null && countdownToStart > 0) {
      const intervalId = setInterval(() => {
        setCountdownToStart(prev => {
          if (prev === null || prev <= 1) {
            clearInterval(intervalId);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(intervalId);
    }
  }, [draftStatus, countdownToStart]);

  // Handle active draft timer
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

  const formatTime = (seconds: number) => {
    if (seconds <= 0) return "0:00";

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes < 10 ? '0' : ''}${minutes}:${secs < 10 ? '0' : ''}${secs}`;
    }
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const displayTime = () => {
    if (draftStatus === 'pending') {
      if (countdownToStart !== null && countdownToStart > 0) {
        return formatTime(countdownToStart);
      } else if (draftDate) {
        return "Starting Soon";
      } else {
        return "Not Scheduled";
      }
    }
    if (draftStatus === 'completed') return "Ended";
    if (draftStatus === 'paused') return "Paused";

    return formatTime(timeLeft);
  };

  const getTimerLabel = () => {
    if (draftStatus === 'pending') {
      if (countdownToStart !== null && countdownToStart > 0) {
        return "Draft Starts In";
      } else if (draftDate) {
        return "Draft Status";
      } else {
        return "Draft Status";
      }
    }
    return "Time Left";
  };

  const urgencyClass = () => {
    if (draftStatus === 'pending' && countdownToStart !== null && countdownToStart <= 60) {
      return 'text-orange-500 font-bold animate-pulse';
    }
    if (timeLeft <= 10 && draftStatus === 'active') {
      return 'text-red-500 font-bold animate-pulse';
    }
    return 'text-gray-700';
  };

  return (
    <div className="p-3 bg-gray-50 border rounded shadow-sm text-center">
      <div className="text-sm text-gray-500 mb-1">{getTimerLabel()}</div>
      <div className={`text-3xl ${urgencyClass()}`}>
        {displayTime()}
      </div>
      {draftStatus === 'pending' && countdownToStart !== null && countdownToStart <= 300 && countdownToStart > 0 && (
        <div className="text-xs text-orange-600 mt-1 animate-pulse">
          Get ready! Draft starting soon!
        </div>
      )}
    </div>
  );
};

export default DraftTimer;