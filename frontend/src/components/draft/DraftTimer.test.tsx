import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import DraftTimer from './DraftTimer';

// Mock Jest timers
jest.useFakeTimers();

describe('DraftTimer', () => {
  it('renders initial time correctly', () => {
    render(<DraftTimer secondsRemainingFromState={60} draftStatus="active" />);
    expect(screen.getByText('1:00')).toBeInTheDocument();
  });

  it('counts down every second when active', () => {
    render(<DraftTimer secondsRemainingFromState={3} draftStatus="active" />);
    expect(screen.getByText('0:03')).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(screen.getByText('0:02')).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(screen.getByText('0:01')).toBeInTheDocument();
  });

  it('displays urgency class when time is low and active', () => {
    render(<DraftTimer secondsRemainingFromState={10} draftStatus="active" />);
    expect(screen.getByText('0:10')).toHaveClass('text-red-500');
  });

  it('does not display urgency class when time is high', () => {
    render(<DraftTimer secondsRemainingFromState={11} draftStatus="active" />);
    expect(screen.getByText('0:11')).not.toHaveClass('text-red-500');
  });

  it('displays Paused when draftStatus is paused', () => {
    render(<DraftTimer secondsRemainingFromState={60} draftStatus="paused" />);
    expect(screen.getByText('Paused')).toBeInTheDocument();
  });

  it('displays Ended when draftStatus is completed', () => {
    render(<DraftTimer secondsRemainingFromState={0} draftStatus="completed" />);
    expect(screen.getByText('Ended')).toBeInTheDocument();
  });

  it('displays - when draftStatus is pending', () => {
    render(<DraftTimer secondsRemainingFromState={60} draftStatus="pending" />);
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  it('calls onTimerExpire when timer reaches zero and active', () => {
    const handleExpire = jest.fn();
    render(<DraftTimer secondsRemainingFromState={1} draftStatus="active" onTimerExpire={handleExpire} />);
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(handleExpire).toHaveBeenCalledTimes(1);
  });

  it('does not count down if not active', () => {
    render(<DraftTimer secondsRemainingFromState={5} draftStatus="paused" />);
    expect(screen.getByText('Paused')).toBeInTheDocument(); // Initial state
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(screen.getByText('Paused')).toBeInTheDocument(); // Should not change
  });

  it('clears interval on unmount', () => {
    const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
    const { unmount } = render(<DraftTimer secondsRemainingFromState={5} draftStatus="active" />);
    unmount();
    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });
});

// Restore real timers
afterAll(() => {
  jest.useRealTimers();
});