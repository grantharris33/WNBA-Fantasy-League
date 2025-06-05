import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../../common/LoadingSpinner';
import ErrorMessage from '../../common/ErrorMessage';
import ConfirmationModal from '../../common/ConfirmationModal';
import { adminApi, type DataQualityDashboard, type QualityCheck, type AnomalyEntry, type CreateQualityCheckRequest } from '../../../services/adminApi';

type QualityTab = 'dashboard' | 'checks' | 'anomalies' | 'create-check';

const DataQualityTab: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<QualityTab>('dashboard');
  const [dashboard, setDashboard] = useState<DataQualityDashboard | null>(null);
  const [checks, setChecks] = useState<QualityCheck[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [activeSubTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (activeSubTab === 'dashboard') {
        const dashboardData = await adminApi.getDataQualityDashboard();
        setDashboard(dashboardData);
      } else if (activeSubTab === 'checks') {
        const checksData = await adminApi.getQualityChecks();
        setChecks(checksData);
      } else if (activeSubTab === 'anomalies') {
        const anomaliesData = await adminApi.getAnomalies();
        setAnomalies(anomaliesData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: '📊' },
    { id: 'checks' as const, label: 'Quality Checks', icon: '✅' },
    { id: 'anomalies' as const, label: 'Anomalies', icon: '⚠️' },
    { id: 'create-check' as const, label: 'Create Check', icon: '➕' }
  ];

  return (
    <div className="space-y-6">
      {/* Sub-navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeSubTab === tab.id
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

      {loading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {error && <ErrorMessage message={error} />}

      {!loading && !error && (
        <>
          {activeSubTab === 'dashboard' && (
            <DashboardView dashboard={dashboard} onRefresh={loadData} />
          )}
          {activeSubTab === 'checks' && (
            <ChecksView checks={checks} onRefresh={loadData} />
          )}
          {activeSubTab === 'anomalies' && (
            <AnomaliesView anomalies={anomalies} onRefresh={loadData} />
          )}
          {activeSubTab === 'create-check' && (
            <CreateCheckView onSuccess={() => setActiveSubTab('checks')} />
          )}
        </>
      )}
    </div>
  );
};

interface DashboardViewProps {
  dashboard: DataQualityDashboard | null;
  onRefresh: () => void;
}

const DashboardView: React.FC<DashboardViewProps> = ({ dashboard, onRefresh }) => {
  if (!dashboard) return null;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">✅</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Passed Checks
                  </dt>
                  <dd className="text-lg font-medium text-green-600">
                    {dashboard.checks_summary.passed || 0}
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
                <span className="text-2xl">❌</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Failed Checks
                  </dt>
                  <dd className="text-lg font-medium text-red-600">
                    {dashboard.checks_summary.failed || 0}
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
                    Unresolved Issues
                  </dt>
                  <dd className="text-lg font-medium text-yellow-600">
                    {dashboard.total_unresolved_anomalies}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Severity Breakdown */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Anomaly Severity Breakdown
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(dashboard.severity_breakdown).map(([severity, count]) => (
              <div key={severity} className="text-center">
                <div className={`text-2xl font-bold ${getSeverityColor(severity)}`}>
                  {count}
                </div>
                <div className="text-sm text-gray-500 capitalize">{severity}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Anomalies */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Recent Anomalies
            </h3>
            <button
              onClick={onRefresh}
              className="bg-indigo-600 text-white px-3 py-2 rounded-md text-sm hover:bg-indigo-700"
            >
              Refresh
            </button>
          </div>
          <div className="space-y-3">
            {dashboard.recent_anomalies.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No recent anomalies</p>
            ) : (
              dashboard.recent_anomalies.slice(0, 5).map((anomaly) => (
                <div key={anomaly.id} className="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded">
                  <div className="flex">
                    <div className="ml-3">
                      <p className="text-sm text-yellow-800">
                        <span className="font-medium">{anomaly.anomaly_type}:</span> {anomaly.description}
                      </p>
                      <p className="text-xs text-yellow-600 mt-1">
                        {new Date(anomaly.detected_at).toLocaleString()} • {anomaly.severity}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface ChecksViewProps {
  checks: QualityCheck[];
  onRefresh: () => void;
}

const ChecksView: React.FC<ChecksViewProps> = ({ checks, onRefresh }) => {
  const [runningCheck, setRunningCheck] = useState<number | null>(null);

  const handleRunCheck = async (checkId: number) => {
    try {
      setRunningCheck(checkId);
      await adminApi.runQualityCheck(checkId);
      onRefresh();
    } catch (error) {
      console.error('Failed to run check:', error);
    } finally {
      setRunningCheck(null);
    }
  };

  const handleRunAllChecks = async () => {
    try {
      await adminApi.runAllQualityChecks();
      onRefresh();
    } catch (error) {
      console.error('Failed to run all checks:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Quality Checks ({checks.length})
        </h3>
        <div className="space-x-3">
          <button
            onClick={handleRunAllChecks}
            className="bg-green-600 text-white px-4 py-2 rounded-md text-sm hover:bg-green-700"
          >
            Run All Checks
          </button>
          <button
            onClick={onRefresh}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm hover:bg-indigo-700"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {checks.map((check) => (
            <li key={check.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600 truncate">
                      {check.check_name}
                    </p>
                    <div className="ml-2 flex-shrink-0 flex">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        check.status === 'passed' 
                          ? 'bg-green-100 text-green-800'
                          : check.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {check.status}
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        Type: {check.check_type} • Table: {check.target_table}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      <p>
                        Last run: {check.last_run 
                          ? new Date(check.last_run).toLocaleString()
                          : 'Never'
                        }
                      </p>
                    </div>
                  </div>
                  {check.consecutive_failures > 0 && (
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {check.consecutive_failures} consecutive failures
                      </span>
                    </div>
                  )}
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => handleRunCheck(check.id)}
                    disabled={runningCheck === check.id}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                  >
                    {runningCheck === check.id ? 'Running...' : 'Run'}
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

interface AnomaliesViewProps {
  anomalies: AnomalyEntry[];
  onRefresh: () => void;
}

const AnomaliesView: React.FC<AnomaliesViewProps> = ({ anomalies, onRefresh }) => {
  const [resolvingAnomaly, setResolvingAnomaly] = useState<number | null>(null);
  const [showResolveModal, setShowResolveModal] = useState<number | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const handleResolveAnomaly = async (anomalyId: number) => {
    try {
      setResolvingAnomaly(anomalyId);
      await adminApi.resolveAnomaly(anomalyId, resolutionNotes);
      setShowResolveModal(null);
      setResolutionNotes('');
      onRefresh();
    } catch (error) {
      console.error('Failed to resolve anomaly:', error);
    } finally {
      setResolvingAnomaly(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Anomalies ({anomalies.length})
        </h3>
        <button
          onClick={onRefresh}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm hover:bg-indigo-700"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-4">
        {anomalies.map((anomaly) => (
          <div
            key={anomaly.id}
            className={`border-l-4 p-4 rounded ${
              anomaly.severity === 'critical'
                ? 'border-red-400 bg-red-50'
                : anomaly.severity === 'high'
                ? 'border-orange-400 bg-orange-50'
                : anomaly.severity === 'medium'
                ? 'border-yellow-400 bg-yellow-50'
                : 'border-blue-400 bg-blue-50'
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-medium text-gray-900">
                    {anomaly.anomaly_type}
                  </h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    anomaly.severity === 'critical'
                      ? 'bg-red-100 text-red-800'
                      : anomaly.severity === 'high'
                      ? 'bg-orange-100 text-orange-800'
                      : anomaly.severity === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {anomaly.severity}
                  </span>
                  {anomaly.is_resolved && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Resolved
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-700 mt-1">{anomaly.description}</p>
                <div className="text-xs text-gray-500 mt-2">
                  Entity: {anomaly.entity_type} • ID: {anomaly.entity_id} • 
                  Detected: {new Date(anomaly.detected_at).toLocaleString()}
                </div>
                {anomaly.is_resolved && anomaly.resolution_notes && (
                  <div className="mt-2 p-2 bg-green-50 rounded border">
                    <p className="text-xs text-green-700">
                      <strong>Resolution:</strong> {anomaly.resolution_notes}
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      Resolved: {anomaly.resolved_at ? new Date(anomaly.resolved_at).toLocaleString() : 'Unknown'}
                    </p>
                  </div>
                )}
              </div>
              {!anomaly.is_resolved && (
                <button
                  onClick={() => setShowResolveModal(anomaly.id)}
                  className="ml-4 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                >
                  Resolve
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Resolve Modal */}
      {showResolveModal && (
        <ConfirmationModal
          isOpen={true}
          title="Resolve Anomaly"
          message="Please provide resolution notes for this anomaly:"
          onConfirm={() => handleResolveAnomaly(showResolveModal)}
          onCancel={() => {
            setShowResolveModal(null);
            setResolutionNotes('');
          }}
          confirmText={resolvingAnomaly === showResolveModal ? 'Resolving...' : 'Resolve'}
          isLoading={resolvingAnomaly === showResolveModal}
        >
          <textarea
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded mt-2"
            rows={3}
            placeholder="Enter resolution notes..."
            required
          />
        </ConfirmationModal>
      )}
    </div>
  );
};

interface CreateCheckViewProps {
  onSuccess: () => void;
}

const CreateCheckView: React.FC<CreateCheckViewProps> = ({ onSuccess }) => {
  const [formData, setFormData] = useState<CreateQualityCheckRequest>({
    check_name: '',
    check_type: 'completeness',
    target_table: '',
    check_query: '',
    expected_result: '',
    failure_threshold: 1
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      setError(null);
      
      const submitData = { ...formData };
      if (!submitData.expected_result) {
        delete submitData.expected_result;
      }
      
      await adminApi.createQualityCheck(submitData);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create check');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
        Create New Quality Check
      </h3>

      {error && <ErrorMessage message={error} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">Check Name</label>
          <input
            type="text"
            required
            value={formData.check_name}
            onChange={(e) => setFormData({ ...formData, check_name: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="e.g., Player Position Completeness"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Check Type</label>
          <select
            value={formData.check_type}
            onChange={(e) => setFormData({ ...formData, check_type: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="completeness">Completeness</option>
            <option value="accuracy">Accuracy</option>
            <option value="consistency">Consistency</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Target Table</label>
          <input
            type="text"
            required
            value={formData.target_table}
            onChange={(e) => setFormData({ ...formData, target_table: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="e.g., player, stat_line, game"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Check Query</label>
          <textarea
            required
            value={formData.check_query}
            onChange={(e) => setFormData({ ...formData, check_query: e.target.value })}
            rows={4}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="SELECT COUNT(*) FROM player WHERE position IS NULL"
          />
          <p className="mt-1 text-sm text-gray-500">
            SQL query to run. Should return a single value.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Expected Result (Optional)</label>
          <input
            type="text"
            value={formData.expected_result || ''}
            onChange={(e) => setFormData({ ...formData, expected_result: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="e.g., 0 (for no missing data)"
          />
          <p className="mt-1 text-sm text-gray-500">
            Leave empty if any result is acceptable.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Failure Threshold</label>
          <input
            type="number"
            min="1"
            required
            value={formData.failure_threshold}
            onChange={(e) => setFormData({ ...formData, failure_threshold: parseInt(e.target.value) })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
          <p className="mt-1 text-sm text-gray-500">
            Number of consecutive failures before alerting.
          </p>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => onSuccess()}
            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={creating}
            className="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {creating ? 'Creating...' : 'Create Check'}
          </button>
        </div>
      </form>
    </div>
  );
};

const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return 'text-red-600';
    case 'high':
      return 'text-orange-600';
    case 'medium':
      return 'text-yellow-600';
    case 'low':
      return 'text-blue-600';
    default:
      return 'text-gray-600';
  }
};

export default DataQualityTab;