import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import { adminApi, type AuditLogEntry } from '../../../services/adminApi';

type ActionType = 'all' | 'MODIFY_HISTORICAL_LINEUP' | 'RECALCULATE_SCORE' | 'OVERRIDE_WEEKLY_MOVES' | 'GRANT_ADMIN_MOVES';

const AuditLogTab: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<ActionType>('all');
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [expandedEntries, setExpandedEntries] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadAuditLogs(true);
  }, [selectedAction, selectedTeam]);

  const loadAuditLogs = async (reset = false) => {
    try {
      setLoading(true);
      setError(null);

      const currentPage = reset ? 0 : page;
      const limit = 50;
      const offset = currentPage * limit;

      const teamId = selectedTeam ? parseInt(selectedTeam) : undefined;
      const newLogs = await adminApi.getAuditLog(teamId, limit, offset);

      // Filter by action type if specified
      const filteredLogs = selectedAction === 'all' 
        ? newLogs 
        : newLogs.filter(log => log.action === selectedAction);

      if (reset) {
        setAuditLogs(filteredLogs);
        setPage(0);
      } else {
        setAuditLogs(prev => [...prev, ...filteredLogs]);
      }

      setHasMore(newLogs.length === limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
      loadAuditLogs(false);
    }
  };

  const toggleExpanded = (entryId: number) => {
    setExpandedEntries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(entryId)) {
        newSet.delete(entryId);
      } else {
        newSet.add(entryId);
      }
      return newSet;
    });
  };

  const formatActionName = (action: string): string => {
    return action
      .split('_')
      .map(word => word.charAt(0) + word.slice(1).toLowerCase())
      .join(' ');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Admin Audit Log
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            Track all administrative actions performed in the system
          </p>
        </div>
        <button
          onClick={() => loadAuditLogs(true)}
          disabled={loading}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow border">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Action Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Action Type
            </label>
            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value as ActionType)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="all">All Actions</option>
              <option value="MODIFY_HISTORICAL_LINEUP">Lineup Modifications</option>
              <option value="RECALCULATE_SCORE">Score Recalculations</option>
              <option value="OVERRIDE_WEEKLY_MOVES">Move Overrides</option>
              <option value="GRANT_ADMIN_MOVES">Move Grants</option>
            </select>
          </div>

          {/* Team Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Team ID (Optional)
            </label>
            <input
              type="number"
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              placeholder="Filter by team ID..."
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {auditLogs.length} audit entries
            </span>
            <span>
              Filter: {selectedAction === 'all' ? 'All Actions' : formatActionName(selectedAction)}
            </span>
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Audit Logs List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {auditLogs.length === 0 ? (
          <div className="text-center py-12">
            {loading ? (
              <LoadingSpinner />
            ) : (
              <div>
                <span className="text-4xl">📋</span>
                <p className="mt-2 text-gray-500">No audit logs found</p>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {auditLogs.map((entry) => (
              <AuditLogEntry
                key={entry.id}
                entry={entry}
                isExpanded={expandedEntries.has(entry.id)}
                onToggleExpanded={() => toggleExpanded(entry.id)}
              />
            ))}
          </div>
        )}

        {/* Load More Button */}
        {hasMore && auditLogs.length > 0 && (
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <AuditStatCard
          title="Total Actions"
          value={auditLogs.length}
          icon="📊"
          color="bg-blue-50 text-blue-600"
        />
        <AuditStatCard
          title="Lineup Changes"
          value={auditLogs.filter(log => log.action === 'MODIFY_HISTORICAL_LINEUP').length}
          icon="✏️"
          color="bg-green-50 text-green-600"
        />
        <AuditStatCard
          title="Score Recalcs"
          value={auditLogs.filter(log => log.action === 'RECALCULATE_SCORE').length}
          icon="🔄"
          color="bg-yellow-50 text-yellow-600"
        />
        <AuditStatCard
          title="Move Grants"
          value={auditLogs.filter(log => 
            log.action === 'OVERRIDE_WEEKLY_MOVES' || log.action === 'GRANT_ADMIN_MOVES'
          ).length}
          icon="🎫"
          color="bg-purple-50 text-purple-600"
        />
      </div>
    </div>
  );
};

interface AuditLogEntryProps {
  entry: AuditLogEntry;
  isExpanded: boolean;
  onToggleExpanded: () => void;
}

const AuditLogEntry: React.FC<AuditLogEntryProps> = ({ entry, isExpanded, onToggleExpanded }) => {
  const details = parseDetails(entry.details);
  
  const getActionIcon = (action: string): string => {
    switch (action) {
      case 'MODIFY_HISTORICAL_LINEUP':
        return '✏️';
      case 'RECALCULATE_SCORE':
        return '🔄';
      case 'OVERRIDE_WEEKLY_MOVES':
      case 'GRANT_ADMIN_MOVES':
        return '🎫';
      default:
        return '📝';
    }
  };

  const getActionColor = (action: string): string => {
    switch (action) {
      case 'MODIFY_HISTORICAL_LINEUP':
        return 'bg-blue-100 text-blue-800';
      case 'RECALCULATE_SCORE':
        return 'bg-green-100 text-green-800';
      case 'OVERRIDE_WEEKLY_MOVES':
      case 'GRANT_ADMIN_MOVES':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatActionName = (action: string): string => {
    return action
      .split('_')
      .map(word => word.charAt(0) + word.slice(1).toLowerCase())
      .join(' ');
  };

  return (
    <div className="p-6 hover:bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-xl">{getActionIcon(entry.action)}</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getActionColor(entry.action)}`}>
              {formatActionName(entry.action)}
            </span>
            <span className="text-sm text-gray-500">
              by {entry.admin_email}
            </span>
            <span className="text-sm text-gray-400">
              {new Date(entry.timestamp).toLocaleString()}
            </span>
          </div>

          <div className="text-sm text-gray-700 mb-2">
            {typeof details === 'object' && details.details ? details.details : entry.details}
          </div>

          {isExpanded && typeof details === 'object' && (
            <div className="mt-3 p-3 bg-gray-50 rounded border">
              <h5 className="text-xs font-medium text-gray-700 mb-2">Details:</h5>
              <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-x-auto">
                {JSON.stringify(details, null, 2)}
              </pre>
            </div>
          )}

          <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
            {entry.method && (
              <span>Method: {entry.method}</span>
            )}
            {entry.path && (
              <span>Path: {entry.path}</span>
            )}
          </div>
        </div>

        <button
          onClick={onToggleExpanded}
          className="ml-4 text-sm text-indigo-600 hover:text-indigo-800"
        >
          {isExpanded ? 'Show less' : 'Show more'}
        </button>
      </div>
    </div>
  );
};

interface AuditStatCardProps {
  title: string;
  value: number;
  icon: string;
  color: string;
}

const AuditStatCard: React.FC<AuditStatCardProps> = ({ title, value, icon, color }) => {
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

// Helper function to parse details
const parseDetails = (details: string): any => {
  try {
    return JSON.parse(details);
  } catch {
    return { details };
  }
};

export default AuditLogTab;