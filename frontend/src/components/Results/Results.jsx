import React from 'react';
import { ArrowLeft, Sparkles, Download, CheckCircle2, Trophy, Medal, Star } from 'lucide-react';

function Results({ onBackToForm, onBackToHome, data }) {
  // Use data from props or fallback to empty array if no data yet
  const candidates = data?.top_candidates || [];
  const totalProcessed = data?.total_resumes_processed || 0;

  const getRankIcon = (rank) => {
    switch (rank) {
      case 1: return <Trophy size={20} color="#f59e0b" />;
      case 2: return <Medal size={20} color="#94a3b8" />;
      case 3: return <Star size={20} color="#b45309" />;
      default: return <CheckCircle2 size={20} color="#3b82f6" />;
    }
  };

  const getRankColor = (rank) => {
    switch (rank) {
      case 1: return "#fef3c7";
      case 2: return "#f1f5f9";
      case 3: return "#ffedd5";
      default: return "#eff6ff";
    }
  };

  return (
    <div className="results-screen">
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="#" onClick={(e) => { e.preventDefault(); onBackToForm(); }} className="back-link">
            <ArrowLeft size={18} />
            Back to Form
          </a>
          <div className="logo" onClick={onBackToHome}>
            <div className="logo-icon">
              <Sparkles size={18} color="white" fill="white" />
            </div>
            <span>CVJACHAI</span>
          </div>
        </div>

        <div className="results-header">
          <div className="badge">
            <CheckCircle2 className="badge-icon" />
            Analysis Complete
          </div>
          <h1>Top {candidates.length} Candidates</h1>
          <p className="section-subtitle">Processed {totalProcessed} resumes using AI</p>
        </div>

        <div className="candidates-list">
          {candidates.length > 0 ? (
            candidates.map((c, i) => (
              <div key={i} className="candidate-card">
                <div className="candidate-pct">
                  <div className="candidate-icon" style={{ backgroundColor: getRankColor(c.rank), margin: '0 auto 10px' }}>
                    {getRankIcon(c.rank)}
                  </div>
                  <span className="pct-value">{c.match_percentage}</span>
                  <span className="pct-label">Match</span>
                </div>
                <div className="candidate-info">
                  <h3>{c.candidate_name}</h3>
                  <div className="candidate-meta">
                    <span>{c.email}</span>
                    <span>•</span>
                    <span>{c.phone}</span>
                  </div>
                  <div className="candidate-verdict" style={{ margin: '10px 0', fontSize: '13px', color: 'rgba(255,255,255,0.7)', fontStyle: 'italic' }}>
                    <strong>Verdict: </strong> {c.verdict}
                  </div>
                  <div className="candidate-skills">
                    <strong>Key Strengths: </strong> {c.key_strengths?.join(", ")}
                  </div>
                </div>
                <a 
                  href={c.resume_url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="btn-download"
                  style={{ textDecoration: 'none' }}
                >
                  <Download size={18} />
                  View Resume
                </a>
              </div>
            ))
          ) : (
            <div className="no-data" style={{ textAlign: 'center', padding: '40px' }}>
              <p>No candidates found matching the criteria.</p>
            </div>
          )}
        </div>

        <div className="results-footer">
          <button className="btn-outline" onClick={onBackToForm}>New Analysis</button>
          <button className="btn-primary" onClick={onBackToHome} style={{ border: 'none', cursor: 'pointer' }}>Back to Home</button>
        </div>
      </div>
    </div>
  );
}

export default Results;
