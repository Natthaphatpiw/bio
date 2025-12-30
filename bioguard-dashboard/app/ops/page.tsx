'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import CaseList, { FraudCase } from '@/components/CaseList';
import AgentTimeline, { TimelineEvent } from '@/components/AgentTimeline';

// Demo data for fraud cases
const demoCases: FraudCase[] = [
  {
    id: 'case_abc123def456',
    session_id: 'sess_injection_001',
    status: 'OPEN',
    severity: 'CRITICAL',
    summary: 'Injection attack detected: Hooking framework found and LightSync verification failed (0/3 rounds). Device shows signs of tampering.',
    evidence_refs: ['ENV_HOOKING', 'LS_FAIL_ALL', 'LS_INJECTION_DETECTED'],
    created_at: new Date(Date.now() - 1800000).toISOString(),
    updated_at: new Date(Date.now() - 1800000).toISOString(),
    timeline_count: 4,
    notes_count: 1,
  },
  {
    id: 'case_xyz789ghi012',
    session_id: 'sess_ato_002',
    status: 'INVESTIGATING',
    severity: 'HIGH',
    summary: 'Potential ATO attempt: High-value transfer to new payee with behavioral anomaly score of 0.75.',
    evidence_refs: ['BEH_ANOMALY_HIGH', 'CTX_NEW_PAYEE_HIGH', 'CTX_HIGH_VALUE'],
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 1200000).toISOString(),
    assigned_to: 'fraud_analyst_1',
    timeline_count: 6,
    notes_count: 3,
  },
  {
    id: 'case_mno345pqr678',
    session_id: 'sess_rooted_003',
    status: 'OPEN',
    severity: 'MEDIUM',
    summary: 'Rooted device detected during eKYC. User attempting to verify identity on compromised device.',
    evidence_refs: ['ENV_ROOTED', 'POLICY_ROOT_EKYC'],
    created_at: new Date(Date.now() - 7200000).toISOString(),
    updated_at: new Date(Date.now() - 7200000).toISOString(),
    timeline_count: 2,
    notes_count: 0,
  },
  {
    id: 'case_stu901vwx234',
    session_id: 'sess_false_004',
    status: 'FALSE_POSITIVE',
    severity: 'LOW',
    summary: 'Developer mode detected but user is a verified developer. Resolved as false positive.',
    evidence_refs: ['ENV_DEV_MODE'],
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 43200000).toISOString(),
    assigned_to: 'fraud_analyst_2',
    timeline_count: 5,
    notes_count: 2,
  },
];

// Demo timeline events
const demoTimelineEvents: TimelineEvent[] = [
  {
    id: 'evt_1',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    event: 'Session signals received',
    actor: 'system',
    type: 'signal',
    details: { signals: ['integrity', 'lightsync', 'liveness'] },
  },
  {
    id: 'evt_2',
    timestamp: new Date(Date.now() - 1799000).toISOString(),
    event: 'Tool: score_integrity executed',
    actor: 'orchestrator',
    type: 'tool',
    details: { score: 0.95, reason_codes: ['ENV_HOOKING'] },
  },
  {
    id: 'evt_3',
    timestamp: new Date(Date.now() - 1798000).toISOString(),
    event: 'Tool: score_lightsync executed',
    actor: 'orchestrator',
    type: 'tool',
    details: { score: 1.0, reason_codes: ['LS_FAIL_ALL', 'LS_INJECTION_DETECTED'] },
  },
  {
    id: 'evt_4',
    timestamp: new Date(Date.now() - 1797000).toISOString(),
    event: 'Policy floor triggered: BLOCK',
    actor: 'policy_engine',
    type: 'decision',
    details: { triggered_rules: ['BLOCK_HOOKING'] },
  },
  {
    id: 'evt_5',
    timestamp: new Date(Date.now() - 1796000).toISOString(),
    event: 'Case created automatically',
    actor: 'orchestrator',
    type: 'case',
    details: { case_id: 'case_abc123def456', severity: 'CRITICAL' },
  },
];

interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggested_actions?: string[];
}

export default function OpsConsolePage() {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [cases, setCases] = useState<FraudCase[]>(demoCases);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>(demoTimelineEvents);
  const [copilotMessages, setCopilotMessages] = useState<CopilotMessage[]>([]);
  const [copilotInput, setCopilotInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const selectedCase = cases.find((c) => c.id === selectedCaseId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [copilotMessages]);

  const handleSendMessage = async () => {
    if (!copilotInput.trim() || !selectedCaseId) return;

    const userMessage: CopilotMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: copilotInput,
      timestamp: new Date().toISOString(),
    };

    setCopilotMessages((prev) => [...prev, userMessage]);
    setCopilotInput('');
    setIsLoading(true);

    // Simulate API call to copilot
    setTimeout(() => {
      const assistantMessage: CopilotMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: getCopilotResponse(copilotInput, selectedCase),
        timestamp: new Date().toISOString(),
        suggested_actions: getCopilotActions(selectedCase),
      };
      setCopilotMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const getCopilotResponse = (input: string, fraudCase?: FraudCase): string => {
    const inputLower = input.toLowerCase();

    if (inputLower.includes('explain') || inputLower.includes('why')) {
      return `Based on my analysis of case ${fraudCase?.id}:

**Summary**: ${fraudCase?.summary}

**Key Findings**:
- Severity Level: ${fraudCase?.severity}
- The decision was made based on multiple signals indicating ${fraudCase?.severity === 'CRITICAL' ? 'a serious' : 'potential'} fraud risk
- Evidence collected: ${fraudCase?.evidence_refs.join(', ')}

**Analysis**:
The session showed concerning patterns. The combination of ${fraudCase?.evidence_refs[0]} and ${fraudCase?.evidence_refs[1] || 'other indicators'} strongly suggests ${fraudCase?.severity === 'CRITICAL' ? 'an active injection attack' : 'suspicious activity'}.`;
    }

    if (inputLower.includes('action') || inputLower.includes('recommend')) {
      if (fraudCase?.severity === 'CRITICAL') {
        return `For this **CRITICAL** severity case, I recommend:

1. **Immediate Action**: Block the device/account temporarily
2. **Investigation**: Review all recent sessions from this device fingerprint
3. **Verification**: Do NOT contact user through this device - use alternative channel
4. **Documentation**: Document all findings and add to case timeline
5. **Escalation**: Consider escalating to security team

Would you like me to help draft the device block notification?`;
      }
      return `For this **${fraudCase?.severity}** severity case, I recommend:

1. **Review**: Examine the evidence timeline carefully
2. **Compare**: Look at similar resolved cases for patterns
3. **Verify**: Consider contacting the user through verified channels
4. **Decide**: Mark as CONFIRMED_FRAUD or FALSE_POSITIVE based on investigation`;
    }

    if (inputLower.includes('similar')) {
      return `I found 3 similar cases based on the evidence patterns:

1. **case_sim_001** (CONFIRMED_FRAUD) - Same injection pattern, resolved 2 days ago
2. **case_sim_002** (CONFIRMED_FRAUD) - Similar device fingerprint anomaly
3. **case_sim_003** (FALSE_POSITIVE) - Similar flags but was legitimate developer

Based on historical patterns, cases with ${fraudCase?.evidence_refs[0]} are confirmed as fraud **78% of the time**.`;
    }

    return `I'm the Fraud Copilot assistant for case ${fraudCase?.id}.

I can help you:
- **Explain** the decision and evidence in detail
- **Recommend** investigation actions based on severity
- **Compare** with similar resolved cases
- **Analyze** patterns and risk indicators

What would you like to know about this case?`;
  };

  const getCopilotActions = (fraudCase?: FraudCase): string[] => {
    if (!fraudCase) return [];

    const actions = [];

    if (fraudCase.status === 'OPEN') {
      actions.push('Start investigation - Mark as INVESTIGATING');
    }

    if (fraudCase.severity === 'CRITICAL') {
      actions.push('Block device temporarily');
      actions.push('Escalate to security team');
    } else if (fraudCase.severity === 'HIGH') {
      actions.push('Contact user via verified channel');
      actions.push('Review related sessions');
    }

    actions.push('View similar resolved cases');

    return actions;
  };

  const handleQuickAction = (action: string) => {
    setCopilotInput(action);
  };

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary-900 flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-900">BioGuard Nexus</h1>
                <p className="text-xs text-slate-500">Fraud Ops Console</p>
              </div>
            </Link>
            <div className="h-8 w-px bg-slate-200 mx-2" />
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
              <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span className="text-sm font-medium text-amber-700">AI Agent Active</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Sessions
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <span className="text-sm font-medium text-slate-700">Fraud Analyst</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-[1600px] mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Case List - Left Panel */}
          <div className="col-span-4">
            <CaseList
              cases={cases}
              onSelectCase={setSelectedCaseId}
              selectedCaseId={selectedCaseId || undefined}
            />
          </div>

          {/* Main Panel - Timeline & Copilot */}
          <div className="col-span-8 space-y-6">
            {selectedCase ? (
              <>
                {/* Agent Timeline */}
                <AgentTimeline
                  events={timelineEvents}
                  sessionId={selectedCase.session_id}
                  decision={{
                    decision: selectedCase.severity === 'CRITICAL' ? 'BLOCK' : selectedCase.severity === 'HIGH' ? 'HOLD' : 'STEP_UP',
                    final_risk: selectedCase.severity === 'CRITICAL' ? 0.95 : selectedCase.severity === 'HIGH' ? 0.75 : 0.5,
                    reason_codes: selectedCase.evidence_refs,
                    explanation: selectedCase.summary,
                  }}
                />

                {/* Fraud Copilot */}
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-primary-50 to-purple-50">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">Fraud Copilot</h3>
                        <p className="text-xs text-slate-500">AI-powered investigation assistant</p>
                      </div>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="h-80 overflow-y-auto px-6 py-4 space-y-4">
                    {copilotMessages.length === 0 && (
                      <div className="text-center py-8">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
                          <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                          </svg>
                        </div>
                        <p className="text-slate-500 mb-4">Ask me anything about this case</p>
                        <div className="flex flex-wrap justify-center gap-2">
                          <button
                            onClick={() => handleQuickAction('Explain why this was flagged')}
                            className="px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                          >
                            Explain the decision
                          </button>
                          <button
                            onClick={() => handleQuickAction('What actions do you recommend?')}
                            className="px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                          >
                            Recommend actions
                          </button>
                          <button
                            onClick={() => handleQuickAction('Show me similar cases')}
                            className="px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                          >
                            Find similar cases
                          </button>
                        </div>
                      </div>
                    )}

                    {copilotMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-xl px-4 py-3 ${
                            message.role === 'user'
                              ? 'bg-primary-600 text-white'
                              : 'bg-slate-100 text-slate-900'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          {message.suggested_actions && message.suggested_actions.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-slate-200">
                              <p className="text-xs font-medium text-slate-500 mb-2">Suggested Actions:</p>
                              <div className="flex flex-wrap gap-2">
                                {message.suggested_actions.map((action, i) => (
                                  <button
                                    key={i}
                                    className="px-2 py-1 text-xs bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded transition-colors"
                                    onClick={() => handleQuickAction(action)}
                                  >
                                    {action}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-slate-100 rounded-xl px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={copilotInput}
                        onChange={(e) => setCopilotInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="Ask about this case..."
                        className="flex-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={!copilotInput.trim() || isLoading}
                        className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-slate-100 flex items-center justify-center">
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">Select a Case</h3>
                <p className="text-slate-500">Choose a fraud case from the left panel to view details and use the AI Copilot</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
