import React, { useState, useEffect } from 'react';
import {
  Brain,
  Zap,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock,
  Layers,
  ArrowRight,
  Database,
  ShieldCheck,
  Send,
  HelpCircle
} from 'lucide-react';

const FAILURE_SIGNATURES = [
  'npm_install_timeout',
  'npm_dependency_conflict',
  'python_package_install_failure',
  'test_failure',
  'compilation_failure',
  'docker_build_failure',
  'missing_environment_variable',
  'authentication_failure',
  'lint_failure',
  'deployment_failure'
];

export default function App() {
  // Global State
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [healthStatus, setHealthStatus] = useState({
    connected: false,
    bank: 'checking...',
    hindsightConnected: false
  });

  // Current Failure Form State
  const [failureForm, setFailureForm] = useState({
    repository: 'acme/payment-service',
    workflow: 'CI / Build',
    failure_signature: 'npm_install_timeout',
    error_type: 'FetchError',
    error_message: 'npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/payment-sdk',
    environment: 'Node.js 20 / Ubuntu',
    suspected_cause: 'npm package registry timeout'
  });

  // Analysis State
  const [isAnalysing, setIsAnalysing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Record Outcome Form State
  const [outcomeForm, setOutcomeForm] = useState({
    action_result: 'success',
    action_taken: 'Verified npm registry configuration and pointed to the accessible internal registry mirror.',
    resolution: 'npm installation succeeded without timeout delays.',
    lesson_learned: 'When npm registry requests repeatedly timeout, verify registry/network configuration before repeatedly retrying.'
  });
  const [isSavingOutcome, setIsSavingOutcome] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);

  // Learning History State
  const [experiences, setExperiences] = useState([]);
  const [isLoadingExperiences, setIsLoadingExperiences] = useState(false);

  // Check health and load experiences on mount
  useEffect(() => {
    checkHealth();
    loadExperiences();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealthStatus({
          connected: true,
          bank: data.active_bank,
          hindsightConnected: data.hindsight?.status === 'connected'
        });
      } else {
        setHealthStatus(prev => ({ ...prev, connected: false }));
      }
    } catch (e) {
      setHealthStatus(prev => ({ ...prev, connected: false }));
    }
  };

  const loadExperiences = async () => {
    setIsLoadingExperiences(true);
    try {
      const res = await fetch('/api/experiences');
      if (res.ok) {
        const data = await res.json();
        setExperiences(data);
      }
    } catch (e) {
      console.error('Failed to load experiences', e);
    } finally {
      setIsLoadingExperiences(false);
    }
  };

  // Run Analysis
  const handleAnalyse = async () => {
    setIsAnalysing(true);
    setErrorMsg(null);
    setSaveSuccessMsg(null);

    try {
      const res = await fetch('/api/analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          failure: failureForm,
          memory_enabled: memoryEnabled
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to analyse failure');
      }

      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsAnalysing(false);
    }
  };

  // Save new experience / outcome
  const handleSaveOutcome = async (e) => {
    e.preventDefault();
    setIsSavingOutcome(true);
    setSaveSuccessMsg(null);
    setErrorMsg(null);

    const newExpId = `exp-npm-${String(experiences.length + 1).padStart(3, '0')}`;
    const newExperience = {
      experience_id: newExpId,
      timestamp: new Date().toISOString(),
      repository: failureForm.repository,
      workflow: failureForm.workflow,
      failure_signature: failureForm.failure_signature,
      error_type: failureForm.error_type || 'FetchError',
      error_message: failureForm.error_message,
      environment: failureForm.environment,
      suspected_cause: failureForm.suspected_cause,
      action_taken: outcomeForm.action_taken,
      action_result: outcomeForm.action_result,
      resolution: outcomeForm.resolution,
      lesson_learned: outcomeForm.lesson_learned
    };

    try {
      const res = await fetch('/api/experience', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newExperience)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to save experience');
      }

      setSaveSuccessMsg(`Experience [${newExpId}] successfully retained into Hindsight memory!`);
      await loadExperiences();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsSavingOutcome(false);
    }
  };

  // Demo Presets
  const applyPreset = (step) => {
    setErrorMsg(null);
    setSaveSuccessMsg(null);
    if (step === 1) {
      setMemoryEnabled(false);
      setFailureForm({
        repository: 'acme/web-portal',
        workflow: 'ci-build-and-test',
        failure_signature: 'npm_install_timeout',
        error_type: 'FetchError',
        error_message: 'npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/core',
        environment: 'node:18-alpine / ubuntu-latest',
        suspected_cause: 'Network latency or transient registry timeout'
      });
      setOutcomeForm({
        action_result: 'failure',
        action_taken: 'Retry npm install',
        resolution: 'Retry did not solve the issue. Registry request timed out repeatedly.',
        lesson_learned: 'Repeated retries are ineffective when the npm registry/network path itself is unavailable.'
      });
    } else if (step === 2) {
      setMemoryEnabled(true);
      setFailureForm({
        repository: 'acme/payment-service',
        workflow: 'ci-pipeline',
        failure_signature: 'npm_install_timeout',
        error_type: 'FetchError',
        error_message: 'npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/payment-sdk',
        environment: 'node:18-alpine / ubuntu-latest',
        suspected_cause: 'Registry timeout'
      });
      setOutcomeForm({
        action_result: 'success',
        action_taken: 'Verified npm registry configuration and switched to the accessible registry route.',
        resolution: 'npm installation completed successfully after configuring the accessible registry URL.',
        lesson_learned: 'When npm registry requests repeatedly timeout, verify registry/network configuration before repeatedly retrying.'
      });
    } else if (step === 3) {
      setMemoryEnabled(true);
      setFailureForm({
        repository: 'acme/notification-service',
        workflow: 'ci-build',
        failure_signature: 'npm_install_timeout',
        error_type: 'FetchError',
        error_message: 'npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/common-lib',
        environment: 'node:18-alpine / ubuntu-latest',
        suspected_cause: 'Outdated npm registry setting in CI job'
      });
      setOutcomeForm({
        action_result: 'success',
        action_taken: 'Checked registry configuration upfront and pointed to internal mirror without retrying.',
        resolution: 'Build succeeded immediately without timeout delays.',
        lesson_learned: 'Proactively checking registry configuration saves CI build time by avoiding failed retries.'
      });
    }
  };

  return (
    <div className="app-container">
      {/* SECTION A: HEADER */}
      <header className="app-header">
        <div className="header-title-area">
          <h1>Experience-Driven CI Failure Resolution Agent</h1>
          <p>"An incident-resolution agent that remembers what worked — and what failed."</p>
        </div>

        <div className="header-controls">
          {/* Backend / Hindsight / Bank Status */}
          <div className="status-badge" style={{ gap: 10 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className={`status-dot ${healthStatus.connected ? '' : 'disconnected'}`} />
              Backend: <strong>{healthStatus.connected ? 'Connected' : 'Disconnected'}</strong>
            </span>
            <span style={{ color: 'var(--border-color)' }}>|</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className={`status-dot ${healthStatus.hindsightConnected ? '' : 'disconnected'}`} />
              Hindsight: <strong>{healthStatus.hindsightConnected ? 'Connected' : 'Unavailable'}</strong>
            </span>
            <span style={{ color: 'var(--border-color)' }}>|</span>
            <span>Bank: <strong style={{ color: '#58a6ff' }}>{healthStatus.bank}</strong></span>
          </div>

          {/* Memory Toggle */}
          <div className="memory-toggle-container">
            <button
              className={`toggle-btn ${memoryEnabled ? 'active on' : ''}`}
              onClick={() => setMemoryEnabled(true)}
            >
              <Zap size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: -2 }} />
              MEMORY ON
            </button>
            <button
              className={`toggle-btn ${!memoryEnabled ? 'active off' : ''}`}
              onClick={() => setMemoryEnabled(false)}
            >
              MEMORY OFF
            </button>
          </div>
        </div>
      </header>

      {/* QUICK PRESET BAR */}
      <div className="preset-bar">
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Demo Scenarios:</span>
        <button className="preset-btn" onClick={() => applyPreset(1)}>
          Scenario 1: Baseline (Memory OFF)
        </button>
        <button className="preset-btn" onClick={() => applyPreset(2)}>
          Scenario 2: Learn from Failed Retry
        </button>
        <button className="preset-btn" onClick={() => applyPreset(3)}>
          Scenario 3: Prioritize Proven Fix
        </button>
      </div>

      {errorMsg && (
        <div className="notice-box warning">
          <AlertTriangle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {saveSuccessMsg && (
        <div className="notice-box info">
          <CheckCircle2 size={18} color="#3fb950" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* MAIN TWO-COLUMN WORKSPACE */}
      <div className="main-grid">
        {/* LEFT COLUMN: Input & Record Outcome */}
        <div className="col-left">
          {/* SECTION B: CURRENT CI FAILURE */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                <Layers size={18} color="#58a6ff" />
                Current CI Failure
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Live Incident</span>
            </div>

            <div className="form-group">
              <label className="form-label">Repository</label>
              <input
                className="form-input"
                type="text"
                value={failureForm.repository}
                onChange={(e) => setFailureForm({ ...failureForm, repository: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Workflow</label>
              <input
                className="form-input"
                type="text"
                value={failureForm.workflow}
                onChange={(e) => setFailureForm({ ...failureForm, workflow: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Failure Signature</label>
              <select
                className="form-select"
                value={failureForm.failure_signature}
                onChange={(e) => setFailureForm({ ...failureForm, failure_signature: e.target.value })}
              >
                {FAILURE_SIGNATURES.map((sig) => (
                  <option key={sig} value={sig}>
                    {sig}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Error Output</label>
              <textarea
                className="form-textarea"
                rows={3}
                value={failureForm.error_message}
                onChange={(e) => setFailureForm({ ...failureForm, error_message: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Environment</label>
              <input
                className="form-input"
                type="text"
                value={failureForm.environment}
                onChange={(e) => setFailureForm({ ...failureForm, environment: e.target.value })}
              />
            </div>

            <button
              className="btn-primary"
              onClick={handleAnalyse}
              disabled={isAnalysing}
            >
              {isAnalysing ? (
                <>
                  <RefreshCw className="spin" size={16} />
                  Analysing with Hindsight...
                </>
              ) : (
                <>
                  <Brain size={16} />
                  Analyse Failure
                </>
              )}
            </button>
          </div>

          {/* SECTION E: RECORD OUTCOME */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                <Database size={18} color="#3fb950" />
                Record Engineer Action & Outcome
              </span>
            </div>

            <form onSubmit={handleSaveOutcome}>
              <div className="form-group">
                <label className="form-label">Action Outcome</label>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    type="button"
                    className={`preset-btn ${outcomeForm.action_result === 'success' ? 'active-success' : ''}`}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      background: outcomeForm.action_result === 'success' ? 'var(--success-bg)' : 'var(--bg-tertiary)',
                      borderColor: outcomeForm.action_result === 'success' ? '#3fb950' : 'var(--border-color)',
                      color: outcomeForm.action_result === 'success' ? '#3fb950' : 'var(--text-primary)',
                      fontWeight: 600
                    }}
                    onClick={() => setOutcomeForm({ ...outcomeForm, action_result: 'success' })}
                  >
                    ✓ Success
                  </button>
                  <button
                    type="button"
                    className={`preset-btn ${outcomeForm.action_result === 'failure' ? 'active-failure' : ''}`}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      background: outcomeForm.action_result === 'failure' ? 'var(--failure-bg)' : 'var(--bg-tertiary)',
                      borderColor: outcomeForm.action_result === 'failure' ? '#f85149' : 'var(--border-color)',
                      color: outcomeForm.action_result === 'failure' ? '#f85149' : 'var(--text-primary)',
                      fontWeight: 600
                    }}
                    onClick={() => setOutcomeForm({ ...outcomeForm, action_result: 'failure' })}
                  >
                    ✕ Failed
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Action Taken</label>
                <input
                  className="form-input"
                  type="text"
                  value={outcomeForm.action_taken}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, action_taken: e.target.value })}
                  placeholder="e.g. Retry npm install or Verified registry config"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Resolution Details</label>
                <input
                  className="form-input"
                  type="text"
                  value={outcomeForm.resolution}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, resolution: e.target.value })}
                  placeholder="e.g. Build succeeded without timeout"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Lesson Learned</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={outcomeForm.lesson_learned}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, lesson_learned: e.target.value })}
                  placeholder="e.g. Verify registry config before repeatedly retrying"
                  required
                />
              </div>

              <button
                type="submit"
                className="btn-primary"
                style={{ background: '#238636' }}
                disabled={isSavingOutcome}
              >
                {isSavingOutcome ? (
                  <>
                    <RefreshCw className="spin" size={16} />
                    Retaining in Hindsight...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Save Experience to Hindsight
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* RIGHT COLUMN: Recommendation, Recalled Memories & History */}
        <div className="col-right">
          {/* SECTION D: RECOMMENDATION */}
          {analysisResult && (
            <div className={`card recommendation-card ${analysisResult.influencing_experiences.length > 0 ? 'has-learning' : ''}`}>
              <div className="card-header">
                <span className="card-title">
                  <ShieldCheck size={18} color={analysisResult.influencing_experiences.length > 0 ? '#3fb950' : '#58a6ff'} />
                  Recommended Resolution
                </span>
                <span className={`status-tag ${analysisResult.memory_enabled ? 'used' : 'low'}`}>
                  {analysisResult.memory_enabled ? 'Experience-Driven' : 'Memory Disabled'}
                </span>
              </div>

              <div className="rec-action-box">
                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 4, fontWeight: 700 }}>
                  Recommended Action:
                </div>
                <div className="rec-action-text">
                  {analysisResult.recommendation}
                </div>
              </div>

              <div className="reasoning-box">
                <strong style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontSize: '0.8rem', textTransform: 'uppercase' }}>
                  Why? (Outcome Analysis):
                </strong>
                {analysisResult.reasoning}
              </div>

              {analysisResult.influencing_experiences && analysisResult.influencing_experiences.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem', textTransform: 'uppercase', marginBottom: 8 }}>
                    Influencing Experiences:
                  </strong>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {Array.from(new Set(analysisResult.influencing_experiences)).map((id, idx) => {
                      // Match against known experiences or relevant items
                      const match = experiences.find(e => e.experience_id === id) ||
                                    analysisResult.relevant_experiences.find(r => r.experience_id === id || r.id === id);
                      const action = match?.action_taken || match?.extracted_action || (id.includes('001') ? 'Retry npm install' : id.includes('002') ? 'Registry configuration' : 'Checked registry configuration');
                      const isFailure = match?.action_result === 'failure' || match?.extracted_result === 'failure' || id.includes('001');

                      return (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--bg-tertiary)', borderRadius: 4, border: '1px solid var(--border-color)', fontSize: '0.82rem' }}>
                          <span style={{ fontFamily: 'JetBrains Mono', color: '#79c0ff' }}>{id}</span>
                          <span style={{ color: 'var(--text-primary)' }}>{action}</span>
                          <span className={`outcome-badge ${isFailure ? 'failure' : 'success'}`}>
                            {isFailure ? '✕ FAILED' : '✓ SUCCESS'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SECTION C: HINDSIGHT MEMORY */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                <Brain size={18} color="#a371f7" />
                Hindsight Memory Retrieval
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {memoryEnabled ? 'Active TEMPR Search' : 'Disabled'}
              </span>
            </div>

            {!memoryEnabled ? (
              <div className="notice-box info" style={{ margin: 0 }}>
                <Clock size={16} />
                <span>Memory disabled — recommendation uses only the current failure baseline.</span>
              </div>
            ) : !analysisResult ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontStyle: 'italic' }}>
                Click "Analyse Failure" to query Hindsight memory and evaluate past incident outcomes.
              </p>
            ) : analysisResult.recalled_experiences.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                No prior experiences found in memory for this failure signature.
              </p>
            ) : (
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
                  Showing {analysisResult.recalled_experiences.length} recalled memories (
                  <strong style={{ color: '#3fb950' }}>{analysisResult.relevant_experiences.length} relevant</strong>,{' '}
                  <strong style={{ color: '#d29922' }}>{analysisResult.low_relevance_experiences.length} low relevance</strong>):
                </div>

                {analysisResult.recalled_experiences.map((item, idx) => {
                  const isUsed = item.relevance_status === 'Used for recommendation';
                  const isRelevant = item.relevance_status === 'Relevant';
                  const isLow = item.relevance_status === 'Low relevance';

                  return (
                    <div key={idx} className={`memory-item ${isUsed ? 'used' : ''} ${isLow ? 'low' : ''}`}>
                      <div className="memory-item-header">
                        <span className={`status-tag ${isUsed ? 'used' : isRelevant ? 'relevant' : 'low'}`}>
                          {item.relevance_status}
                        </span>

                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          {item.extracted_result && (
                            <span className={`outcome-badge ${item.extracted_result === 'success' ? 'success' : 'failure'}`}>
                              {item.extracted_result === 'success' ? '✓ SUCCESS' : '✕ FAILED'}
                            </span>
                          )}
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Score: {Math.round(item.relevance_score * 100)}%
                          </span>
                        </div>
                      </div>

                      <div style={{ color: 'var(--text-primary)', marginBottom: 6, lineHeight: 1.4 }}>
                        {item.text}
                      </div>

                      <div style={{ fontSize: '0.78rem', color: isLow ? '#d29922' : 'var(--text-secondary)', fontStyle: 'italic' }}>
                        Relevance: {item.relevance_reason}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* SECTION F: LEARNING HISTORY TIMELINE */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                <Clock size={18} color="#e3b341" />
                Experience Progression Timeline
              </span>
              <button
                className="preset-btn"
                onClick={loadExperiences}
                disabled={isLoadingExperiences}
                title="Refresh from Hindsight store"
              >
                <RefreshCw size={12} className={isLoadingExperiences ? 'spin' : ''} />
              </button>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 10 }}>
              Chronological log of retained CI experiences demonstrating learning over time:
            </p>

            <div className="timeline-container">
              {experiences.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No experiences recorded yet.</p>
              ) : (
                experiences.map((exp, idx) => {
                  const isSuccess = exp.action_result === 'success';
                  return (
                    <div key={exp.experience_id || idx} className="timeline-step">
                      <div className={`step-marker ${isSuccess ? 'success' : 'failure'}`}>
                        {idx + 1}
                      </div>
                      <div className="step-body">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span className="step-title">
                            {exp.experience_id}: {exp.failure_signature}
                          </span>
                          <span className={`outcome-badge ${isSuccess ? 'success' : 'failure'}`}>
                            {isSuccess ? '✓ SUCCESS' : '✕ FAILED'}
                          </span>
                        </div>
                        <div className="step-desc">
                          <strong>Action:</strong> {exp.action_taken}
                        </div>
                        <div className="step-desc">
                          <strong>Resolution:</strong> {exp.resolution}
                        </div>
                        <div className="step-desc" style={{ color: 'var(--text-muted)' }}>
                          <strong>Lesson:</strong> {exp.lesson_learned}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* FINAL DEMO MESSAGE */}
      <footer style={{ marginTop: 40, textAlign: 'center', padding: '20px 0', borderTop: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '0.95rem', fontStyle: 'italic', letterSpacing: '0.01em' }}>
        "Every resolved failure becomes experience for the next incident."
      </footer>
    </div>
  );
}
