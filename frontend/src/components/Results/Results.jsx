import React, { useState } from 'react';
import { ArrowLeft, Sparkles, Download, CheckCircle2, Trophy, Medal, Star, X, Eye, FileText, User, Mail, Phone, Briefcase } from 'lucide-react';

function Results({ onBackToForm, onBackToHome, data }) {
  const candidates = data?.top_candidates || [];
  const totalProcessed = data?.total_resumes_processed || 0;
  
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  const handleCloseModal = () => {
    setSelectedCandidate(null);
  };

  // Download: fetch as blob and force download to device
  const handleDownload = async () => {
    if (!selectedCandidate?.resume_url) return;
    
    try {
      const downloadUrl = selectedCandidate.resume_url.includes('?')
        ? `${selectedCandidate.resume_url}&download=1`
        : `${selectedCandidate.resume_url}?download=1`;
        
      const response = await fetch(downloadUrl);
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      
      // Determine filename from header or fallback
      let filename = 'resume.pdf';
      const disposition = response.headers.get('Content-Disposition');
      if (disposition && disposition.includes('filename=')) {
        const matches = /filename="([^"]+)"/.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }
      
      // Create local URL and trigger forced download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed, falling back to new tab:', err);
      // Fallback
      window.open(selectedCandidate.resume_url + '?download=1', '_blank');
    }
  };

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

  // Parse resume text into structured sections for a professional preview
  const parseResumeText = (text) => {
    if (!text) return [];
    
    const lines = text.split('\n').filter(l => l.trim());
    const sections = [];
    let currentSection = { title: '', lines: [] };

    for (const line of lines) {
      const trimmed = line.trim();
      // Detect section headers: ALL CAPS lines, or lines ending with ':'
      const isHeader = (
        (trimmed.length > 2 && trimmed.length < 60 && trimmed === trimmed.toUpperCase() && /[A-Z]/.test(trimmed)) ||
        (trimmed.endsWith(':') && trimmed.length < 60)
      );

      if (isHeader) {
        if (currentSection.title || currentSection.lines.length > 0) {
          sections.push({ ...currentSection });
        }
        currentSection = { title: trimmed.replace(/:$/, ''), lines: [] };
      } else {
        currentSection.lines.push(trimmed);
      }
    }
    if (currentSection.title || currentSection.lines.length > 0) {
      sections.push(currentSection);
    }
    return sections;
  };

  // Render the resume text content in a professional layout
  const renderResumePreview = () => {
    if (!selectedCandidate) return null;

    const resumeText = selectedCandidate.resume_text;
    
    if (!resumeText) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
          height: '100%', gap: '16px', color: '#64748b', padding: '40px', textAlign: 'center'
        }}>
          <FileText size={56} color="#3b82f6" />
          <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>
            Resume preview not available
          </p>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#94a3b8' }}>
            Click <strong>"Download Resume"</strong> below to save the original file.
          </p>
        </div>
      );
    }

    const sections = parseResumeText(resumeText);

    return (
      <div style={{
        padding: '40px 48px',
        height: '100%',
        overflowY: 'auto',
        fontFamily: "'Georgia', 'Times New Roman', serif",
        color: '#1e293b',
        lineHeight: '1.7',
        maxWidth: '800px',
        margin: '0 auto',
      }}>
        {/* Candidate Header */}
        <div style={{
          textAlign: 'center',
          paddingBottom: '20px',
          marginBottom: '24px',
          borderBottom: '2px solid #0ea5e9',
        }}>
          <h2 style={{
            margin: '0 0 8px',
            fontSize: '1.6rem',
            fontWeight: 700,
            color: '#0f172a',
            letterSpacing: '1px',
            textTransform: 'uppercase',
          }}>
            {selectedCandidate.candidate_name}
          </h2>
          <div style={{
            display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap',
            fontSize: '0.85rem', color: '#475569',
          }}>
            {selectedCandidate.email !== 'N/A' && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Mail size={14} /> {selectedCandidate.email}
              </span>
            )}
            {selectedCandidate.phone !== 'N/A' && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Phone size={14} /> {selectedCandidate.phone}
              </span>
            )}
          </div>
        </div>

        {/* Resume Sections */}
        {sections.map((section, idx) => (
          <div key={idx} style={{ marginBottom: '20px' }}>
            {section.title && (
              <h3 style={{
                fontSize: '0.85rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '1.5px',
                color: '#0ea5e9',
                borderBottom: '1px solid #e2e8f0',
                paddingBottom: '6px',
                marginBottom: '10px',
                fontFamily: "'Arial', 'Helvetica', sans-serif",
              }}>
                {section.title}
              </h3>
            )}
            {section.lines.map((line, lineIdx) => (
              <p key={lineIdx} style={{
                margin: '0 0 4px',
                fontSize: '0.9rem',
                color: '#334155',
              }}>
                {line.startsWith('•') || line.startsWith('-') || line.startsWith('–') ? (
                  <span style={{ display: 'flex', gap: '8px' }}>
                    <span style={{ color: '#0ea5e9', fontWeight: 'bold' }}>•</span>
                    <span>{line.replace(/^[•\-–]\s*/, '')}</span>
                  </span>
                ) : line}
              </p>
            ))}
          </div>
        ))}
      </div>
    );
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
                <button 
                  onClick={() => setSelectedCandidate(c)} 
                  className="btn-download"
                  style={{ border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <Eye size={18} />
                  View Resume
                </button>
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

      {/* Resume Preview Modal */}
      {selectedCandidate && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, width: '100%', height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          zIndex: 1000,
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          padding: '20px',
          backdropFilter: 'blur(5px)'
        }}>
          <div style={{
            backgroundColor: '#0f172a',
            borderRadius: '16px',
            width: '100%', maxWidth: '1000px',
            height: '90vh',
            display: 'flex', flexDirection: 'column',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#fff' }}>{selectedCandidate.candidate_name}'s Resume</h3>
                <p style={{ margin: '4px 0 0', fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)' }}>
                  {selectedCandidate.match_percentage} Match • {selectedCandidate.email}
                </p>
              </div>
              <button 
                onClick={handleCloseModal}
                style={{
                  background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%',
                  width: '36px', height: '36px', display: 'flex', justifyContent: 'center', alignItems: 'center',
                  color: '#fff', cursor: 'pointer'
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body (Resume Text Preview) */}
            <div style={{ flex: 1, backgroundColor: '#ffffff', position: 'relative', overflow: 'hidden' }}>
              {renderResumePreview()}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '20px 24px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex', justifyContent: 'flex-end', gap: '15px'
            }}>
              <button 
                onClick={handleCloseModal}
                className="btn-outline" 
                style={{ padding: '10px 20px', margin: 0 }}
              >
                Close Preview
              </button>
              <button 
                onClick={handleDownload}
                className="btn-primary"
                style={{ 
                  display: 'flex', alignItems: 'center', gap: '8px', 
                  padding: '10px 20px', border: 'none', cursor: 'pointer' 
                }}
              >
                <Download size={18} />
                Download Resume
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Results;
