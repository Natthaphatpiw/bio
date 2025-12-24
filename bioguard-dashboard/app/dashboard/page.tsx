'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Session {
  id: string;
  created_at: string;
  merchant_name: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  result?: {
    environment?: { isSafe: boolean };
    lightSync?: { pass: boolean; confidence: number };
    faceLiveness?: { isReal: boolean; confidence: number };
  };
}

// Demo data for prototype
const demoSessions: Session[] = [
  {
    id: 'demo-001',
    created_at: new Date().toISOString(),
    merchant_name: 'Demo Bank',
    status: 'COMPLETED',
    result: {
      environment: { isSafe: true },
      lightSync: { pass: true, confidence: 0.92 },
      faceLiveness: { isReal: true, confidence: 0.95 },
    },
  },
  {
    id: 'demo-002',
    created_at: new Date(Date.now() - 300000).toISOString(),
    merchant_name: 'Demo Bank',
    status: 'FAILED',
    result: {
      environment: { isSafe: true },
      lightSync: { pass: false, confidence: 0.3 },
      faceLiveness: { isReal: false, confidence: 0.2 },
    },
  },
  {
    id: 'demo-003',
    created_at: new Date(Date.now() - 600000).toISOString(),
    merchant_name: 'Demo Bank',
    status: 'PENDING',
  },
];

export default function Dashboard() {
  const [sessions, setSessions] = useState<Session[]>(demoSessions);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'COMPLETED' | 'FAILED'>('ALL');

  const filteredSessions = sessions.filter((session) => {
    if (filter === 'ALL') return true;
    return session.status === filter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-500/20 text-green-400';
      case 'FAILED':
        return 'bg-red-500/20 text-red-400';
      default:
        return 'bg-yellow-500/20 text-yellow-400';
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <header className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">BioGuard Nexus</h1>
                <p className="text-sm text-gray-400">Verification Dashboard</p>
              </div>
            </Link>
          </div>
          <Link
            href="/"
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            New Link
          </Link>
        </div>
      </header>

      {/* Stats */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="grid grid-cols-4 gap-4">
          <div className="glass rounded-xl p-4">
            <p className="text-sm text-gray-400">Total Sessions</p>
            <p className="text-2xl font-bold">{sessions.length}</p>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-sm text-gray-400">Pending</p>
            <p className="text-2xl font-bold text-yellow-400">
              {sessions.filter((s) => s.status === 'PENDING').length}
            </p>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-sm text-gray-400">Completed</p>
            <p className="text-2xl font-bold text-green-400">
              {sessions.filter((s) => s.status === 'COMPLETED').length}
            </p>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-sm text-gray-400">Failed</p>
            <p className="text-2xl font-bold text-red-400">
              {sessions.filter((s) => s.status === 'FAILED').length}
            </p>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="max-w-6xl mx-auto mb-6">
        <div className="flex gap-2">
          {(['ALL', 'PENDING', 'COMPLETED', 'FAILED'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filter === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-800 text-gray-400 hover:bg-slate-700'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Sessions Table */}
      <div className="max-w-6xl mx-auto">
        <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="px-6 py-4 text-left text-sm text-gray-400 font-medium">Session ID</th>
                <th className="px-6 py-4 text-left text-sm text-gray-400 font-medium">Time</th>
                <th className="px-6 py-4 text-left text-sm text-gray-400 font-medium">Status</th>
                <th className="px-6 py-4 text-left text-sm text-gray-400 font-medium">Environment</th>
                <th className="px-6 py-4 text-left text-sm text-gray-400 font-medium">Light-Sync</th>
                <th className="px-6 py-4 text-left text-sm text-gray-400 font-medium">Face Liveness</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.map((session) => (
                <tr key={session.id} className="border-b border-slate-700/50 hover:bg-slate-800/50">
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm">{session.id.slice(0, 8)}...</span>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm">{formatTime(session.created_at)}</p>
                      <p className="text-xs text-gray-500">{formatDate(session.created_at)}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(session.status)}`}>
                      {session.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {session.result?.environment ? (
                      <span className={session.result.environment.isSafe ? 'text-green-400' : 'text-red-400'}>
                        {session.result.environment.isSafe ? 'Safe' : 'Threat'}
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {session.result?.lightSync ? (
                      <div className="flex items-center gap-2">
                        <span className={session.result.lightSync.pass ? 'text-green-400' : 'text-red-400'}>
                          {session.result.lightSync.pass ? 'Pass' : 'Fail'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {(session.result.lightSync.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {session.result?.faceLiveness ? (
                      <div className="flex items-center gap-2">
                        <span className={session.result.faceLiveness.isReal ? 'text-green-400' : 'text-red-400'}>
                          {session.result.faceLiveness.isReal ? 'Real' : 'Spoof'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {(session.result.faceLiveness.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredSessions.length === 0 && (
            <div className="py-12 text-center text-gray-500">
              No sessions found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
