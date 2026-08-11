import React, { useState } from 'react';
import { ArrowLeft, Sparkles, FileText, Upload } from 'lucide-react';
import { resumeApi } from '../../api';

function Optimization({ onBack, onAnalyze, onStartAnalysis, token, onError }) {
  const [formData, setFormData] = useState({
    job_description: '',
    resume_file: null
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleInput = (e) => {
    setFormData(prev => ({ ...prev, job_description: e.target.value }));
  };

  const handleFile = (e) => {
    setFormData(prev => ({ ...prev, resume_file: e.target.files[0] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.resume_file) {
      alert("Please upload your CV first.");
      return;
    }

    setIsAnalyzing(true);
    onStartAnalysis();

    try {
      const data = new FormData();
      data.append("resume_file", formData.resume_file);
      data.append("job_description", formData.job_description || "");

      const result = await resumeApi.optimize(data, token);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      console.log('Optimization Result:', result);
      onAnalyze(result);
    } catch (error) {
      console.error('Optimization failed:', error);
      alert('Optimization failed: ' + error.message);
      if (onError) onError();
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="personalization-screen">
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="#" onClick={(e) => { e.preventDefault(); onBack(); }} className="back-link">
            <ArrowLeft size={18} />
            Back to Home
          </a>
          <div className="logo" onClick={onBack}>
            <div className="logo-icon">
              <Sparkles size={18} color="white" fill="white" />
            </div>
            <span>CVJACHAI</span>
          </div>
        </div>

        <div className="form-header">
          <h1>Resume Optimization</h1>
          <p className="section-subtitle">Optimize your CV for high ATS scores and job-ready formatting</p>
        </div>

        <form className="form-container" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Job Description (Optional)</label>
            <textarea 
              name="job_description"
              className="form-control" 
              placeholder="Paste the job description here to target the optimization..."
              value={formData.job_description}
              onChange={handleInput}
              disabled={isAnalyzing}
              style={{ minHeight: '120px' }}
            ></textarea>
          </div>

          <div className="form-group">
            <label>Upload Your CV</label>
            <input 
              type="file" 
              id="resume-optimize-upload" 
              style={{ display: 'none' }} 
              onChange={handleFile}
              accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.tiff,.tif"
              disabled={isAnalyzing}
            />
            <div 
              className="upload-area" 
              onClick={() => !isAnalyzing && document.getElementById('resume-optimize-upload').click()}
              style={{ 
                border: formData.resume_file ? '2px solid var(--accent-cyan)' : '',
                opacity: isAnalyzing ? 0.6 : 1,
                cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                padding: '40px'
              }}
            >
              <div className="upload-icon">
                <FileText size={32} />
              </div>
              <p>{formData.resume_file ? formData.resume_file.name : 'Click to upload your CV'}</p>
              <span>PDF, DOCX, JPG, PNG, or other image files</span>
            </div>
          </div>

          <button type="submit" className="btn-submit" disabled={isAnalyzing} style={{ width: '100%', maxWidth: '100%' }}>
            {isAnalyzing ? 'Processing...' : 'Optimize My CV'}
          </button>

          <div className="stats-row" style={{ marginTop: '40px' }}>
            <div className="mini-stat-card">
              <h3>ATS-Ready</h3>
              <p>Format Check</p>
            </div>
            <div className="mini-stat-card">
              <h3>Instant</h3>
              <p>Optimization</p>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Optimization;
