import React, { useState } from 'react';
import { Briefcase, MapPin, DollarSign, FileText, ChevronLeft, Sparkles, Loader2, CheckCircle2 } from 'lucide-react';
import { jobApi } from '../../api';

function CreateJob({ onBack, token }) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    company_name: '',
    location: '',
    description: '',
    skills_required: '',
    min_experience: '',
    is_active: true
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const authToken = token;
      if (!authToken) {
        throw new Error('Authentication token is missing. Please log in again.');
      }

      // Prepare data, ensuring min_experience is a number as per API requirements
      const payload = {
        ...formData,
        min_experience: parseInt(formData.min_experience, 10) || 0
      };

      console.log('Posting job to API...', payload);
      const response = await jobApi.createJob(payload, authToken);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('API Error Response:', errorData);
        throw new Error(errorData.detail || errorData.message || `Failed to post job (HTTP ${response.status})`);
      }

      const result = await response.json();
      console.log('Job posted successfully:', result);
      setSuccess(true);
      setTimeout(() => {
        onBack();
      }, 2000);
    } catch (err) {
      console.error('Submission Error:', err);
      setError(err.message || 'Could not post job. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="create-job-container" style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        background: 'var(--bg-color)'
      }}>
        <div style={{ textAlign: 'center', animation: 'fadeIn 0.5s ease-out' }}>
          <div style={{ 
            width: '100px', 
            height: '100px', 
            background: 'rgba(34, 211, 238, 0.1)', 
            borderRadius: '50%', 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            margin: '0 auto 30px',
            color: 'var(--accent-cyan)'
          }}>
            <CheckCircle2 size={60} />
          </div>
          <h2 style={{ fontSize: '2.5rem', fontWeight: '800', color: 'white', marginBottom: '15px' }}>Job Posted Successfully!</h2>
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.2rem' }}>Redirecting you back...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="create-job-container" style={{ 
      minHeight: '100vh', 
      background: 'var(--bg-color)', 
      color: 'white',
      padding: '60px 20px'
    }}>
      <div className="container" style={{ maxWidth: '800px', margin: '0 auto' }}>
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
            fontSize: '1.1rem',
            marginBottom: '40px',
            padding: '10px 0',
            fontWeight: '600',
            transition: 'transform 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'translateX(-5px)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'translateX(0)'}
        >
          <ChevronLeft size={24} />
          Back to Home
        </button>

        <div className="header" style={{ marginBottom: '50px' }}>
          <div className="badge" style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: '8px', 
            background: 'rgba(139, 92, 246, 0.15)', 
            color: '#a78bfa', 
            padding: '8px 20px', 
            borderRadius: '100px', 
            fontSize: '0.9rem', 
            fontWeight: '700', 
            marginBottom: '20px',
            border: '1px solid rgba(139, 92, 246, 0.3)'
          }}>
            <Sparkles size={16} />
            Recruiter Portal
          </div>
          <h1 style={{ fontSize: '3.5rem', fontWeight: '900', marginBottom: '15px', letterSpacing: '-2px', lineHeight: '1.1' }}>
            Post a New <span className="gradient-text">Job Opening</span>
          </h1>
          <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '1.25rem', maxWidth: '600px', lineHeight: '1.6' }}>
            Reach top talent by providing clear details about the role and requirements.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="form-container-card">
          <div className="form-row-grid">
            <div className="input-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600' }}>
                <Briefcase size={18} color="var(--accent-cyan)" />
                Job Title
              </label>
              <input 
                name="title"
                type="text" 
                required
                placeholder="e.g. Senior Frontend Engineer"
                value={formData.title}
                onChange={handleChange}
                style={inputStyle}
              />
            </div>
            <div className="input-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600' }}>
                <Sparkles size={18} color="var(--accent-cyan)" />
                Company Name
              </label>
              <input 
                name="company_name"
                type="text" 
                required
                placeholder="Your Company"
                value={formData.company_name}
                onChange={handleChange}
                style={inputStyle}
              />
            </div>
          </div>

          <div className="form-row-grid">
            <div className="input-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600' }}>
                <MapPin size={18} color="var(--accent-cyan)" />
                Location
              </label>
              <input 
                name="location"
                type="text" 
                required
                placeholder="e.g. Remote or Dhaka, BD"
                value={formData.location}
                onChange={handleChange}
                style={inputStyle}
              />
            </div>
            <div className="input-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600' }}>
                <DollarSign size={18} color="var(--accent-cyan)" />
                Min. Experience (Years)
              </label>
              <input 
                name="min_experience"
                type="number" 
                required
                min="0"
                placeholder="2"
                value={formData.min_experience}
                onChange={handleChange}
                style={inputStyle}
              />
            </div>
          </div>

          <div className="input-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600' }}>
              <FileText size={18} color="var(--accent-cyan)" />
              Skills Required (Comma separated)
            </label>
            <input 
              name="skills_required"
              type="text" 
              required
              placeholder="React, Node.js, Python..."
              value={formData.skills_required}
              onChange={handleChange}
              style={inputStyle}
            />
          </div>

          <div className="input-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '1rem', color: 'rgba(255, 255, 255, 0.8)', fontWeight: '600' }}>
              <FileText size={18} color="var(--accent-cyan)" />
              Job Description
            </label>
            <textarea 
              name="description"
              required
              placeholder="Detail the responsibilities and expectations..."
              value={formData.description}
              onChange={handleChange}
              style={{ ...inputStyle, minHeight: '150px', resize: 'vertical' }}
            />
          </div>

          {error && (
            <div style={{ color: '#ef4444', padding: '15px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.95rem' }}>
              {error}
            </div>
          )}

          <button 
            type="submit" 
            disabled={loading}
            className="btn-primary" 
            style={{ 
              marginTop: '10px',
              justify: 'center',
              padding: '18px',
              fontSize: '1.2rem',
              fontWeight: '700',
              borderRadius: '16px',
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? (
              <><Loader2 className="animate-spin" size={24} style={{ marginRight: '10px' }} /> Posting...</>
            ) : 'Post Job Now'}
          </button>
        </form>
      </div>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Responsive Form Classes */
        .form-container-card {
          background: rgba(255, 255, 255, 0.03); 
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 32px;
          padding: 40px;
          backdrop-filter: blur(20px);
          display: grid;
          gap: 30px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .form-row-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 25px;
        }

        @media (max-width: 768px) {
          .create-job-container {
            padding: 30px 16px !important;
          }
          .header h1 {
            font-size: 2.5rem !important;
          }
          .form-container-card {
            padding: 24px 20px !important;
            border-radius: 24px !important;
            gap: 20px !important;
          }
          .form-row-grid {
            grid-template-columns: 1fr !important; /* Force single column on mobile */
            gap: 20px !important;
          }
        }

        @media (max-width: 480px) {
          .header h1 {
            font-size: 2.2rem !important;
          }
          .input-group label {
            font-size: 0.95rem !important;
          }
        }
      `}</style>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  background: 'rgba(255, 255, 255, 0.05)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  padding: '16px 20px',
  borderRadius: '14px',
  color: 'white',
  outline: 'none',
  fontSize: '1rem',
  transition: 'all 0.3s'
};

export default CreateJob;
