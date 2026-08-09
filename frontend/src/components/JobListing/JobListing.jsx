import React, { useState, useEffect } from 'react';
import { Briefcase, MapPin, DollarSign, Clock, ChevronLeft, Sparkles, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { jobApi } from '../../api';

function JobListing({ onBack, onCreateJob }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [applyingJob, setApplyingJob] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '' });
  const [file, setFile] = useState(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async (attempt = 1) => {
    const MAX_RETRIES = 10;
    const RETRY_DELAY_MS = 5000;
    try {
      if (attempt === 1) setLoading(true);
      setError(null);
      console.log(`Fetching jobs from API (attempt ${attempt})...`);
      const response = await jobApi.getJobs();
      console.log('Response status:', response.status);

      if (!response.ok) {
        if (response.status === 504 || response.status === 502 || response.status === 503) {
          throw new Error('SERVER_TIMEOUT');
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const text = await response.text();
      let result;
      try {
        result = JSON.parse(text);
      } catch (e) {
        console.error('Expected JSON but received HTML or invalid text:', text.substring(0, 200));
        throw new Error('NOT_JSON');
      }

      console.log('Fetched jobs result:', result);

      if (Array.isArray(result)) {
        setJobs(result);
      } else if (result?.results && Array.isArray(result.results)) {
        setJobs(result.results);
      } else if (result?.data && Array.isArray(result.data)) {
        setJobs(result.data);
      } else {
        console.error('Unexpected API response format:', result);
        setJobs([]);
        setError('Received data in an unexpected format.');
      }
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error(`Error fetching jobs (attempt ${attempt}):`, err);
      if (attempt < MAX_RETRIES) {
        const isWakingUp = err.message === 'NOT_JSON' || err.message === 'SERVER_TIMEOUT';
        setError(isWakingUp
          ? `Server is waking up... retrying in ${RETRY_DELAY_MS / 1000}s (${attempt}/${MAX_RETRIES})`
          : `Connection failed. Retrying... (${attempt}/${MAX_RETRIES})`
        );
        setTimeout(() => fetchJobs(attempt + 1), RETRY_DELAY_MS);
      } else {
        setError("The server is taking too long to wake up. Please click 'Try Again' in a moment.");
        setLoading(false);
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Recent';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Recent';
      
      const now = new Date();
      const diffInMs = now - date;
      const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
      
      if (diffInHours < 1) {
        const diffInMins = Math.floor(diffInMs / (1000 * 60));
        return diffInMins <= 0 ? 'Just now' : `${diffInMins}m ago`;
      }
      if (diffInHours < 24) {
        return `${diffInHours}h ago`;
      }
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    } catch (e) {
      return 'Recent';
    }
  };

  const getRequirements = (skillsString) => {
    if (!skillsString) return [];
    try {
      return skillsString.split(',').map(s => s.trim()).filter(s => s !== '');
    } catch (e) {
      return [];
    }
  };

  const getJobColor = (id) => {
    const colors = ['#3b82f6', '#10b981', '#ec4899', '#8b5cf6', '#f59e0b', '#06b6d4'];
    const colorId = id || Math.floor(Math.random() * 100);
    return colors[colorId % colors.length];
  };

  const getJobLogo = (title) => {
    if (!title || typeof title !== 'string') return 'JB';
    try {
      const parts = title.split(' ').filter(p => p.length > 0);
      if (parts.length === 0) return 'JB';
      return parts.map(w => w[0]).join('').substring(0, 2).toUpperCase();
    } catch (e) {
      return 'JB';
    }
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleApplyClick = (e, job) => {
    e.stopPropagation();
    setApplyingJob(job);
    setIsSubmitted(false);
    setFile(null);
  };

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert("Please upload your resume first.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const data = new FormData();
      data.append("job", applyingJob.id); // Assuming applyingJob.id is the correct identifier
      data.append("candidate_name", formData.name);
      data.append("candidate_email", formData.email);
      data.append("resume_file", file);

      const response = await jobApi.applyForJob(data);
      
      if (!response.ok) {
        const errorResult = await response.json().catch(() => ({}));
        throw new Error(errorResult.detail || errorResult.message || `Submission failed (HTTP ${response.status})`);
      }

      console.log('Application submitted successfully');
      setIsSubmitted(true);
      setTimeout(() => {
        setApplyingJob(null);
        setIsSubmitted(false);
        setFormData({ name: '', email: '', phone: '' });
        setFile(null);
      }, 3000);
    } catch (err) {
      console.error('Submission error:', err);
      setSubmitError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="job-listing-container" style={{ 
      minHeight: '100vh', 
      background: 'var(--bg-color)', 
      color: 'white',
      padding: '40px 20px'
    }}>
      <div className="container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <button 
          onClick={onBack}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'none',
            border: 'none',
            color: 'var(--accent-cyan)',
            cursor: 'pointer',
            fontSize: '1rem',
            marginBottom: '30px',
            padding: '10px 0',
            fontWeight: '500'
          }}
        >
          <ChevronLeft size={20} />
          Back to Home
        </button>

        <div className="header" style={{ marginBottom: '50px' }}>
          <div>
            <div className="badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--accent-cyan)', padding: '6px 16px', borderRadius: '100px', fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '15px' }}>
              <Sparkles size={14} />
              Available Positions
            </div>
            <h1 style={{ fontSize: '3rem', fontWeight: '801', marginBottom: '15px', letterSpacing: '-1px' }}>
              Find Your Dream <span className="gradient-text">Job</span>
            </h1>
            <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '1.2rem', maxWidth: '600px' }}>
              Explore opportunities that match your skills. Our AI-driven platform connects top talent with innovative companies.
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '300px', gap: '20px' }}>
            <Loader2 className="animate-spin" size={48} color="var(--accent-cyan)" />
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.2rem' }}>Loading the best matches for you...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', background: 'rgba(239, 68, 68, 0.05)', borderRadius: '24px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <AlertCircle size={48} color="#ef4444" style={{ margin: '0 auto 20px' }} />
            <h3 style={{ fontSize: '1.5rem', marginBottom: '10px' }}>Connection Error</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '24px' }}>{error}</p>
            <button onClick={fetchJobs} className="btn-primary" style={{ margin: '0 auto', padding: '12px 24px' }}>Try Again</button>
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.2rem' }}>No job openings found at the moment.</p>
          </div>
        ) : (
          <div className="jobs-list" style={{ display: 'grid', gap: '20px' }}>
            {jobs.map((job) => {
              const isExpanded = expandedId === job.id;
              const jobColor = getJobColor(job.id);
              const jobLogo = getJobLogo(job.title);
              const requirements = getRequirements(job.skills_required);
              const postedTime = formatDate(job.created_at);

              return (
                <div 
                  key={job.id} 
                  className={`job-card ${isExpanded ? 'expanded' : ''}`}
                  onClick={() => toggleExpand(job.id)}
                >
                  <div className="job-card-header">
                    <div className="job-card-main">
                      <div className="job-card-logo" style={{ background: `linear-gradient(135deg, ${jobColor} 0%, rgba(0,0,0,0.3) 100%)`, boxShadow: `0 8px 16px ${jobColor}33` }}>
                        {jobLogo}
                      </div>
                      <div className="job-card-info">
                        <h3>{job.title}</h3>
                        <div className="job-meta-row">
                          <div className="job-meta-item">
                            <Briefcase size={16} color="var(--accent-cyan)" />
                            {job.company_name}
                          </div>
                          <div className="job-meta-item">
                            <MapPin size={16} color="var(--accent-cyan)" />
                            {job.location}
                          </div>
                          <div className="job-meta-item">
                            <DollarSign size={16} color="var(--accent-cyan)" />
                            {job.min_experience}+ Years Exp.
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="job-card-actions">
                      <div className="job-status-row">
                        <span className="job-badge-status">
                          {job.is_active ? 'Active' : 'Closed'}
                        </span>
                        <div className="job-time">
                          <Clock size={14} />
                          {postedTime}
                        </div>
                      </div>
                      {!isExpanded && (
                        <button 
                          className="btn-primary btn-apply-card" 
                          onClick={(e) => handleApplyClick(e, job)}
                        >
                          Apply Now
                        </button>
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="job-details" style={{ 
                      borderTop: '1px solid rgba(255, 255, 255, 0.08)', 
                      paddingTop: '24px',
                      animation: 'slideDown 0.4s ease-out'
                    }}>
                      <div style={{ marginBottom: '24px' }}>
                        <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px', fontSize: '1.2rem' }}>About the Role</h4>
                        <p style={{ color: 'rgba(255, 255, 255, 0.8)', lineHeight: '1.7', fontSize: '1.05rem', whiteSpace: 'pre-wrap' }}>
                          {job.description}
                        </p>
                      </div>

                      <div style={{ marginBottom: '32px' }}>
                        <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '12px', fontSize: '1.2rem' }}>Required Skills</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                          {requirements.map((req, index) => (
                            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'rgba(255, 255, 255, 0.7)' }}>
                              <CheckCircle2 size={16} color="var(--accent-cyan)" />
                              {req}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '16px' }}>
                        <button 
                          className="btn-primary" 
                          style={{ border: 'none', cursor: 'pointer', padding: '14px 40px', fontSize: '1.1rem', borderRadius: '10px' }}
                          onClick={(e) => handleApplyClick(e, job)}
                        >
                          Apply for this position
                        </button>
                        <button 
                          className="btn-secondary" 
                          style={{ border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', padding: '14px 20px', fontSize: '1.1rem', borderRadius: '10px', background: 'transparent' }}
                          onClick={(e) => { e.stopPropagation(); toggleExpand(job.id); }}
                        >
                          Close
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Application Modal */}
      {applyingJob && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#0F172A',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '24px',
            width: '100%',
            maxWidth: '550px',
            padding: '40px',
            position: 'relative',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            animation: 'modalEntrance 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
          }}>
            <button 
              onClick={() => setApplyingJob(null)}
              style={{
                position: 'absolute',
                top: '24px',
                right: '24px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: 'none',
                color: 'white',
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontSize: '20px'
              }}
            >
              ×
            </button>

            {!isSubmitted ? (
              <>
                <div style={{ marginBottom: '30px' }}>
                  <h2 style={{ fontSize: '1.8rem', fontWeight: '700', marginBottom: '8px' }}>Apply for Position</h2>
                  <p style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>{applyingJob.title}</p>
                  <p style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '0.9rem' }}>at {applyingJob.company_name}</p>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '20px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)' }}>Full Name</label>
                    <input 
                      type="text" 
                      required
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      style={{
                        width: '100%',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        padding: '12px 16px',
                        borderRadius: '10px',
                        color: 'white',
                        outline: 'none',
                        transition: 'border-color 0.3s'
                      }}
                      onFocus={(e) => e.target.style.borderColor = 'var(--accent-cyan)'}
                      onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)'}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)' }}>Email Address</label>
                    <input 
                      type="email" 
                      required
                      placeholder="john@example.com"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      style={{
                        width: '100%',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        padding: '12px 16px',
                        borderRadius: '10px',
                        color: 'white',
                        outline: 'none',
                        transition: 'border-color 0.3s'
                      }}
                       onFocus={(e) => e.target.style.borderColor = 'var(--accent-cyan)'}
                       onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)'}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)' }}>Upload CV / Resume</label>
                    <div 
                      style={{
                        border: '2px dashed rgba(255, 255, 255, 0.1)',
                        borderRadius: '12px',
                        padding: '30px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.3s',
                        background: file ? 'rgba(34, 211, 238, 0.05)' : 'transparent',
                        borderColor: file ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.1)'
                      }}
                      onClick={() => document.getElementById('cv-upload').click()}
                    >
                      <input 
                        id="cv-upload" 
                        type="file" 
                        accept=".pdf,.doc,.docx" 
                        style={{ display: 'none' }} 
                        onChange={(e) => setFile(e.target.files[0])}
                      />
                      <div style={{ color: 'var(--accent-cyan)', marginBottom: '8px' }}>
                        <Sparkles size={24} style={{ margin: '0 auto 10px', display: 'block' }} />
                      </div>
                      <p style={{ fontSize: '0.95rem', marginBottom: '4px' }}>
                        {file ? file.name : 'Click to upload your CV'}
                      </p>
                      <p style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.4)' }}>
                        PDF, DOC, DOCX up to 10MB
                      </p>
                    </div>
                  </div>

                  {submitError && (
                    <div style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '10px', fontSize: '0.9rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                      {submitError}
                    </div>
                  )}

                  <button 
                    type="submit" 
                    className="btn-primary" 
                    disabled={isSubmitting}
                    style={{ 
                      marginTop: '10px',
                      justifyContent: 'center',
                      padding: '16px',
                      fontSize: '1.1rem',
                      opacity: isSubmitting ? 0.7 : 1,
                      cursor: isSubmitting ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {isSubmitting ? (
                      <><Loader2 className="animate-spin" size={20} style={{ marginRight: '10px' }} /> Submitting...</>
                    ) : 'Submit Application'}
                  </button>
                </form>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <div style={{ 
                  width: '80px', 
                  height: '80px', 
                  background: 'rgba(34, 211, 238, 0.1)', 
                  borderRadius: '50%', 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  margin: '0 auto 24px',
                  color: 'var(--accent-cyan)'
                }}>
                  <CheckCircle2 size={48} />
                </div>
                <h2 style={{ fontSize: '1.8rem', fontWeight: '700', marginBottom: '16px' }}>Application Sent!</h2>
                <p style={{ color: 'rgba(255, 255, 255, 0.6)', lineHeight: '1.6' }}>
                  Your application for <strong style={{ color: 'white' }}>{applyingJob.title}</strong> has been successfully submitted. We'll be in touch soon.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes modalEntrance {
          from { opacity: 0; transform: scale(0.9) translateY(20px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Clean Modular Classes for Job Listing */
        .job-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 20px;
          padding: 28px;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
          backdrop-filter: blur(10px);
          position: relative;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .job-card:hover {
          transform: translateY(-5px);
          border-color: rgba(34, 211, 238, 0.3);
          background: rgba(255, 255, 255, 0.05);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        .job-card.expanded {
          border-color: rgba(34, 211, 238, 0.3);
        }

        .job-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 24px;
        }

        .job-card-main {
          display: flex;
          gap: 24px;
          align-items: center;
        }

        .job-card-logo {
          width: 64px;
          height: 64px;
          border-radius: 16px;
          display: flex;
          justify-content: center;
          align-items: center;
          font-size: 1.6rem;
          font-weight: bold;
          color: white;
          flex-shrink: 0;
        }

        .job-card-info h3 {
          font-size: 1.5rem;
          margin-bottom: 8px;
          font-weight: 700;
          color: #fff;
        }

        .job-meta-row {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
        }

        .job-meta-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.95rem;
          color: rgba(255, 255, 255, 0.6);
        }

        .job-card-actions {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 18px;
          flex-shrink: 0;
        }

        .job-status-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .job-badge-status {
          font-size: 0.85rem;
          background: rgba(255, 255, 255, 0.08);
          padding: 6px 14px;
          border-radius: 8px;
          color: rgba(255, 255, 255, 0.9);
          font-weight: 500;
        }

        .job-time {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.4);
        }

        .btn-apply-card {
          border: none;
          cursor: pointer;
          padding: 12px 28px;
          font-size: 1rem;
          border-radius: 10px;
        }

        /* Mobile & Tablet Responsiveness */
        @media (max-width: 768px) {
          .job-listing-container {
            padding: 30px 16px !important;
          }
          .header h1 {
            font-size: 2.4rem !important;
          }
          .job-card {
            padding: 24px 20px;
            gap: 20px;
          }
          .job-card-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 20px;
          }
          .job-card-main {
            gap: 16px;
            width: 100%;
          }
          .job-card-logo {
            width: 52px;
            height: 52px;
            font-size: 1.3rem;
            border-radius: 14px;
          }
          .job-card-info h3 {
            font-size: 1.3rem;
            margin-bottom: 6px;
          }
          .job-meta-row {
            gap: 12px;
          }
          .job-meta-item {
            font-size: 0.85rem;
          }
          .job-card-actions {
            width: 100%;
            flex-direction: row;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 16px;
          }
          .btn-apply-card {
            padding: 10px 20px;
            font-size: 0.95rem;
          }
          .job-details button {
            flex: 1;
            justify-content: center;
            text-align: center;
            padding: 12px !important;
            font-size: 0.95rem !important;
          }
        }

        @media (max-width: 480px) {
          .header h1 {
            font-size: 2rem !important;
          }
          .job-card-actions {
            flex-direction: column;
            align-items: stretch;
            gap: 16px;
          }
          .job-status-row {
            justify-content: space-between;
          }
          .btn-apply-card {
            width: 100%;
            justify-content: center;
          }
          .job-details {
            padding-top: 16px !important;
          }
        }
      `}</style>
    </div>
  );
}

export default JobListing;
