import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import { adminApi, type IngestLogEntry } from '../../../services/adminApi';

type LogLevel = 'all' | 'INFO' | 'ERROR';
type LogProvider = 'all' | 'rapidapi' | 'data_quality' | 'scheduler';

const JobLogsTab: React.FC = () => {
  const [logs, setLogs] = useState<IngestLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<LogLevel>('all');
  const [selectedProvider, setSelectedProvider] = useState<LogProvider>('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadLogs(true);
  }, [selectedLevel, selectedProvider]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        loadLogs(true);
      }, 5000); // Refresh every 5 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, selectedLevel, selectedProvider]);

  const loadLogs = async (reset = false) => {
    try {
      setLoading(true);
      setError(null);

      const currentPage = reset ? 0 : page;
      const limit = 50;
      const offset = currentPage * limit;

      const provider = selectedProvider === 'all' ? undefined : selectedProvider;
      const newLogs = await adminApi.getIngestLogs(limit, offset, provider);

      if (reset) {
        setLogs(newLogs);
        setPage(0);
      } else {
        setLogs(prev => [...prev, ...newLogs]);
      }

      setHasMore(newLogs.length === limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
      loadLogs(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    if (selectedLevel === 'all') return true;
    return log.message.startsWith(selectedLevel);
  });

  const getLogLevelColor = (message: string): string => {
    if (message.startsWith('ERROR')) return 'text-red-600 bg-red-50 border-red-200';
    if (message.startsWith('WARN')) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    if (message.startsWith('INFO')) return 'text-blue-600 bg-blue-50 border-blue-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getLogIcon = (message: string): string => {
    if (message.startsWith('ERROR')) return '❌';
    if (message.startsWith('WARN')) return '⚠️';
    if (message.startsWith('INFO')) return 'ℹ️';
    return '📝';
  };

  const getProviderColor = (provider: string): string => {
    switch (provider) {
      case 'rapidapi':
        return 'bg-blue-100 text-blue-800';
      case 'data_quality':
        return 'bg-green-100 text-green-800';
      case 'scheduler':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            System Logs
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            View logs from data ingestion, quality checks, and system operations
          </p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Auto-refresh toggle */}
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">Auto-refresh</span>
          </label>

          {/* Manual refresh button */}
          <button
            onClick={() => loadLogs(true)}
            disabled={loading}
            className="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Log Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Log Level
            </label>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value as LogLevel)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="all">All Levels</option>
              <option value="INFO">Info</option>
              <option value="ERROR">Error</option>
            </select>
          </div>

          {/* Provider Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value as LogProvider)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="all">All Providers</option>
              <option value="rapidapi">RapidAPI</option>
              <option value="data_quality">Data Quality</option>
              <option value="scheduler">Scheduler</option>
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {filteredLogs.length} of {logs.length} logs
            </span>
            <span>
              {autoRefresh && (
                <span className="inline-flex items-center text-green-600">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                  Auto-refreshing
                </span>
              )}
            </span>
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Logs List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            {loading ? (
              <LoadingSpinner />
            ) : (
              <div>
                <span className="text-4xl">📋</span>
                <p className="mt-2 text-gray-500">No logs found</p>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredLogs.map((log) => (
              <LogEntry key={log.id} log={log} />
            ))}
          </div>
        )}

        {/* Load More Button */}
        {hasMore && filteredLogs.length > 0 && (
          <div className="border-t border-gray-200 p-4 text-center">
            <button
              onClick={loadMore}
              disabled={loading}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md text-sm hover:bg-gray-200 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Load More'}
            </button>
          </div>
        )}
      </div>

      {/* Log Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <LogStatCard
          title="Total Logs"
          value={logs.length}
          icon="📊"
          color="bg-blue-50 text-blue-600"
        />
        <LogStatCard
          title="Error Logs"
          value={logs.filter(log => log.message.startsWith('ERROR')).length}
          icon="❌"
          color="bg-red-50 text-red-600"
        />
        <LogStatCard
          title="Recent Activity"
          value={logs.filter(log => {
            const logTime = new Date(log.timestamp);
            const hourAgo = new Date(Date.now() - 60 * 60 * 1000);
            return logTime > hourAgo;
          }).length}
          icon="⏰"
          color="bg-green-50 text-green-600"
        />
      </div>
    </div>
  );
};

interface LogEntryProps {
  log: IngestLogEntry;
}

const LogEntry: React.FC<LogEntryProps> = ({ log }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Clean up the message by removing the log level prefix
  const cleanMessage = log.message.replace(/^(INFO|ERROR|WARN):\s*/, '');
  const logLevel = log.message.match(/^(INFO|ERROR|WARN)/)?.[0] || 'INFO';
  
  return (
    <div className={`p-4 border-l-4 ${getLogLevelColor(log.message)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <span className="text-lg">{getLogIcon(log.message)}</span>
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getProviderColor(log.provider)}`}>
                  {log.provider}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
              <p className={`mt-1 text-sm ${expanded ? 'whitespace-pre-wrap' : 'line-clamp-2'}`}>
                {cleanMessage}
              </p>
            </div>
          </div>
        </div>
        
        {cleanMessage.length > 100 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-2 text-xs text-indigo-600 hover:text-indigo-800"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>
    </div>
  );
};

interface LogStatCardProps {
  title: string;
  value: number;
  icon: string;
  color: string;
}

const LogStatCard: React.FC<LogStatCardProps> = ({ title, value, icon, color }) => {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className={`flex-shrink-0 rounded-md p-3 ${color}`}>
            <span className="text-xl">{icon}</span>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="text-lg font-medium text-gray-900">
                {value.toLocaleString()}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper functions (moved here since they're used multiple times)
const getLogLevelColor = (message: string): string => {
  if (message.startsWith('ERROR')) return 'border-red-400 bg-red-50';
  if (message.startsWith('WARN')) return 'border-yellow-400 bg-yellow-50';
  if (message.startsWith('INFO')) return 'border-blue-400 bg-blue-50';
  return 'border-gray-400 bg-gray-50';
};

const getLogIcon = (message: string): string => {
  if (message.startsWith('ERROR')) return '❌';
  if (message.startsWith('WARN')) return '⚠️';
  if (message.startsWith('INFO')) return 'ℹ️';
  return '📝';
};

const getProviderColor = (provider: string): string => {
  switch (provider) {
    case 'rapidapi':
      return 'bg-blue-100 text-blue-800';
    case 'data_quality':
      return 'bg-green-100 text-green-800';
    case 'scheduler':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default JobLogsTab;