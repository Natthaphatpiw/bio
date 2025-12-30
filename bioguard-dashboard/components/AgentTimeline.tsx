'use client';

import { useState } from 'react';

export interface TimelineEvent {
  id: string;
  timestamp: string;
  event: string;
  actor: string;
  type: 'decision' | 'signal' | 'case' | 'status' | 'tool';
  details?: Record<string, unknown>;
}

interface AgentTimelineProps {
  events: TimelineEvent[];
  sessionId: string;
  decision?: {
    decision: string;
    final_risk: number;
    reason_codes: string[];
    explanation: string;
  };
}

export default function AgentTimeline({ events, sessionId, decision }: AgentTimelineProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'decision':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'signal':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'case':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case 'tool':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getEventColor = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'decision':
        return 'bg-emerald-100 text-emerald-600 border-emerald-200';
      case 'signal':
        return 'bg-blue-100 text-blue-600 border-blue-200';
      case 'case':
        return 'bg-amber-100 text-amber-600 border-amber-200';
      case 'tool':
        return 'bg-purple-100 text-purple-600 border-purple-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'ALLOW':
        return 'bg-emerald-500';
      case 'STEP_UP':
        return 'bg-amber-500';
      case 'HOLD':
        return 'bg-orange-500';
      case 'BLOCK':
        return 'bg-rose-500';
      default:
        return 'bg-slate-500';
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk < 0.3) return 'text-emerald-600';
    if (risk < 0.5) return 'text-amber-600';
    if (risk < 0.7) return 'text-orange-600';
    return 'text-rose-600';
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center">
              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">AI Agent Timeline</h3>
              <p className="text-xs text-slate-500 font-mono">{sessionId}</p>
            </div>
          </div>
          {decision && (
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1 rounded-full text-white text-sm font-medium ${getDecisionColor(decision.decision)}`}>
                {decision.decision}
              </div>
              <div className={`text-sm font-medium ${getRiskColor(decision.final_risk)}`}>
                Risk: {(decision.final_risk * 100).toFixed(0)}%
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Decision Summary */}
      {decision && (
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50">
          <p className="text-sm text-slate-700 mb-3">{decision.explanation}</p>
          {decision.reason_codes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {decision.reason_codes.map((code, i) => (
                <span key={i} className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-xs font-mono">
                  {code}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Timeline */}
      <div className="px-6 py-4">
        <div className="space-y-4">
          {events.map((event, index) => (
            <div key={event.id} className="relative">
              {/* Connector line */}
              {index < events.length - 1 && (
                <div className="absolute left-4 top-10 w-0.5 h-full bg-slate-200" />
              )}

              <div className="flex gap-4">
                {/* Icon */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center border ${getEventColor(event.type)}`}>
                  {getEventIcon(event.type)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div
                    className="cursor-pointer"
                    onClick={() => setExpanded(expanded === event.id ? null : event.id)}
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-slate-900">{event.event}</p>
                      <span className="text-xs text-slate-500">{formatTime(event.timestamp)}</span>
                    </div>
                    <p className="text-xs text-slate-500">{event.actor}</p>
                  </div>

                  {/* Expanded details */}
                  {expanded === event.id && event.details && (
                    <div className="mt-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <pre className="text-xs text-slate-700 overflow-x-auto">
                        {JSON.stringify(event.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {events.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              No timeline events yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
