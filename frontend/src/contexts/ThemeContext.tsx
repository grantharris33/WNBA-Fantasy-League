import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../lib/api';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  actualTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  accentColor?: string;
  setAccentColor: (color: string) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>('system');
  const [accentColor, setAccentColorState] = useState<string>('#3B82F6');
  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>('light');

  // Detect system preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const updateActualTheme = () => {
      if (theme === 'system') {
        setActualTheme(mediaQuery.matches ? 'dark' : 'light');
      } else {
        setActualTheme(theme as 'light' | 'dark');
      }
    };

    updateActualTheme();
    mediaQuery.addEventListener('change', updateActualTheme);

    return () => mediaQuery.removeEventListener('change', updateActualTheme);
  }, [theme]);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    
    if (actualTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Apply accent color as CSS variable
    if (accentColor) {
      root.style.setProperty('--accent-color', accentColor);
    }
  }, [actualTheme, accentColor]);

  // Load user preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await api.get('/api/v1/profile/preferences') as any;
        if (response.data) {
          setThemeState(response.data.theme || 'system');
          setAccentColorState(response.data.accent_color || '#3B82F6');
        }
      } catch {
        // If not logged in or preferences not found, use defaults
        console.log('Using default theme preferences');
      }
    };

    loadPreferences();
  }, []);

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);
    
    // Save to backend if user is logged in
    try {
      await api.put<unknown>('/api/v1/profile/preferences', { theme: newTheme });
    } catch (error) {
      // Silently fail if not logged in
      console.error('Failed to save theme preference:', error);
    }
  };

  const setAccentColor = async (color: string) => {
    setAccentColorState(color);
    
    // Save to backend if user is logged in
    try {
      await api.put<unknown>('/api/v1/profile/preferences', { accent_color: color });
    } catch (error) {
      // Silently fail if not logged in
      console.error('Failed to save accent color preference:', error);
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        actualTheme,
        setTheme,
        accentColor,
        setAccentColor,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};