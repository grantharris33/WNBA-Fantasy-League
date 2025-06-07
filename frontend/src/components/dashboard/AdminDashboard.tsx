import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { useAuth } from '../../contexts/AuthContext';
import { adminApi } from '../../services/adminApi';
import DataQualityTab from './admin/DataQualityTab';
import JobLogsTab from './admin/JobLogsTab';
import TeamManagementTab from './admin/TeamManagementTab';
import AuditLogTab from './admin/AuditLogTab';

type AdminTab = 'overview' | 'data-quality' | 'logs' | 'teams' | 'audit';

interface SystemStats {
  totalUsers: number;
  totalTeams: number;
  totalLeagues: number;
  activeDataIssues: number;
  lastIngestTime?: string;
}

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);

  useEffect(() => {
    if (!user?.is_admin) {
      setError('Access denied. Admin privileges required.');
      setLoading(false);
      return;
    }
    
    loadSystemStats();
  }, [user]);

  const loadSystemStats = async () => {
    try {
      setLoading(true);
      // Load system statistics from the new API endpoint
      const stats = await adminApi.getSystemStats();
      setSystemStats(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system statistics');
    } finally {
      setLoading(false);
    }
  };

  const tabs: Array<{ id: AdminTab; label: string; icon: string }> = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'data-quality', label: 'Data Quality', icon: '🔍' },
    { id: 'logs', label: 'System Logs', icon: '📝' },
    { id: 'teams', label: 'Team Management', icon: '👥' },
    { id: 'audit', label: 'Audit Log', icon: '🔒' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <ErrorMessage message={error} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="mt-1 text-sm text-gray-600">
                  System administration and monitoring
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500">
                  Welcome back, {user?.email}
                </div>
                <div className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center">
                  <span className="text-sm font-medium text-white">A</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <OverviewTab systemStats={systemStats} onRefresh={loadSystemStats} />
        )}
        {activeTab === 'data-quality' && <DataQualityTab />}
        {activeTab === 'logs' && <JobLogsTab />}
        {activeTab === 'teams' && <TeamManagementTab />}
        {activeTab === 'audit' && <AuditLogTab />}
      </div>
    </div>
  );
};

interface OverviewTabProps {
  systemStats: SystemStats | null;
  onRefresh: () => void;
}

const OverviewTab: React.FC<OverviewTabProps> = ({ systemStats, onRefresh }) => {
  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">👥</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Users
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {systemStats?.totalUsers?.toLocaleString() || 'N/A'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">🏀</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Teams
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {systemStats?.totalTeams?.toLocaleString() || 'N/A'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">🏆</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Leagues
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {systemStats?.totalLeagues?.toLocaleString() || 'N/A'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">⚠️</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Data Issues
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {systemStats?.activeDataIssues?.toLocaleString() || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            System Status
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border-l-4 border-green-400 pl-4">
              <p className="text-sm font-medium text-gray-500">Database</p>
              <p className="text-lg font-semibold text-green-600">Healthy</p>
            </div>
            <div className="border-l-4 border-green-400 pl-4">
              <p className="text-sm font-medium text-gray-500">API Services</p>
              <p className="text-lg font-semibold text-green-600">Operational</p>
            </div>
            <div className="border-l-4 border-blue-400 pl-4">
              <p className="text-sm font-medium text-gray-500">Last Data Ingest</p>
              <p className="text-lg font-semibold text-gray-900">
                {systemStats?.lastIngestTime ? new Date(systemStats.lastIngestTime).toLocaleString() : 'N/A'}
              </p>
            </div>
            <div className="border-l-4 border-blue-400 pl-4">
              <p className="text-sm font-medium text-gray-500">Scheduler</p>
              <p className="text-lg font-semibold text-green-600">Running</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <button
              onClick={onRefresh}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              🔄 Refresh Stats
            </button>
            <button
              onClick={() => adminApi.runAllQualityChecks()}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              🔍 Run Quality Checks
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;