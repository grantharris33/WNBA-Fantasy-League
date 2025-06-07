/**
 * Utility functions for working with ISO weeks and converting them to human-readable date ranges
 */

/**
 * Get the date range for an ISO week
 * @param isoWeek - Week in format YYYYWW (e.g., 202503 for 2025 week 3)
 * @returns Object with start and end dates of the week
 */
export function getWeekDateRange(isoWeek: number): { start: Date; end: Date } {
  const year = Math.floor(isoWeek / 100);
  const week = isoWeek % 100;
  
  // Find the first Monday of the ISO year
  // ISO week 1 is the first week with at least 4 days in the new year
  const jan4 = new Date(year, 0, 4); // January 4th is always in week 1
  const jan4WeekDay = jan4.getDay(); // 0 = Sunday, 1 = Monday, etc.
  const jan4Monday = new Date(jan4);
  jan4Monday.setDate(jan4.getDate() - (jan4WeekDay === 0 ? 6 : jan4WeekDay - 1));
  
  // Calculate the start of the requested week
  const weekStart = new Date(jan4Monday);
  weekStart.setDate(jan4Monday.getDate() + (week - 1) * 7);
  
  // Calculate the end of the week (Sunday)
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  
  return { start: weekStart, end: weekEnd };
}

/**
 * Format an ISO week as a human-readable string
 * @param isoWeek - Week in format YYYYWW (e.g., 202503)
 * @returns Formatted string like "202503 (Jan 13th - Jan 19th)"
 */
export function formatWeekWithDates(isoWeek: number): string {
  const { start, end } = getWeekDateRange(isoWeek);
  
  const formatDate = (date: Date): string => {
    const month = date.toLocaleDateString('en-US', { month: 'short' });
    const day = date.getDate();
    const suffix = getDaySuffix(day);
    return `${month} ${day}${suffix}`;
  };
  
  return `${isoWeek} (${formatDate(start)} - ${formatDate(end)})`;
}

/**
 * Get the ordinal suffix for a day (st, nd, rd, th)
 */
function getDaySuffix(day: number): string {
  if (day >= 11 && day <= 13) {
    return 'th';
  }
  switch (day % 10) {
    case 1: return 'st';
    case 2: return 'nd';
    case 3: return 'rd';
    default: return 'th';
  }
}

/**
 * Get the current ISO week
 */
export function getCurrentISOWeek(): number {
  const now = new Date();
  const year = now.getFullYear();
  
  // Find which week of the year we're in
  const jan4 = new Date(year, 0, 4);
  const jan4WeekDay = jan4.getDay();
  const jan4Monday = new Date(jan4);
  jan4Monday.setDate(jan4.getDate() - (jan4WeekDay === 0 ? 6 : jan4WeekDay - 1));
  
  const currentMonday = new Date(now);
  const currentWeekDay = now.getDay();
  currentMonday.setDate(now.getDate() - (currentWeekDay === 0 ? 6 : currentWeekDay - 1));
  
  const weeksDiff = Math.floor((currentMonday.getTime() - jan4Monday.getTime()) / (7 * 24 * 60 * 60 * 1000));
  const isoWeek = weeksDiff + 1;
  
  return year * 100 + isoWeek;
}

/**
 * Convert a date to its ISO week number
 */
export function dateToISOWeek(date: Date): number {
  const year = date.getFullYear();
  const jan4 = new Date(year, 0, 4);
  const jan4WeekDay = jan4.getDay();
  const jan4Monday = new Date(jan4);
  jan4Monday.setDate(jan4.getDate() - (jan4WeekDay === 0 ? 6 : jan4WeekDay - 1));
  
  const targetMonday = new Date(date);
  const targetWeekDay = date.getDay();
  targetMonday.setDate(date.getDate() - (targetWeekDay === 0 ? 6 : targetWeekDay - 1));
  
  const weeksDiff = Math.floor((targetMonday.getTime() - jan4Monday.getTime()) / (7 * 24 * 60 * 60 * 1000));
  const isoWeek = weeksDiff + 1;
  
  return year * 100 + isoWeek;
}