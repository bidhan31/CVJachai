import React, { useState } from 'react';
import { ArrowLeft, Sparkles, Upload } from 'lucide-react';
import { resumeApi } from '../../api';

function Shortlisting({ onBack, onAnalyze, token, onStartAnalysis, onError }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [formData, setFormData] = useState({
    job_circular: '',
    skills: '',
    min_experience: '',
    top_k: '',
    resume_files: null
  });

  const handleInput = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFile = (e) => {
    setFormData(prev => ({ ...prev, resume_files: e.target.files[0] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.resume_files) {
      alert("Please upload at least one resume file.");
      return;
    }

    console.log('Sending request with token:', token);
    setIsAnalyzing(true);
    onStartAnalysis(); // Switch to the analyzing screen immediately

    try {
      const data = new FormData();
      data.append("job_circular", formData.job_circular);
      data.append("resume_files", formData.resume_files);
      data.append("top_k", formData.top_k || "5");
      data.append("skills", formData.skills || "");
      data.append("min_experience", formData.min_experience || "0");

      const result = await resumeApi.classify(data, token);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      console.log('Analysis Result:', result);
      onAnalyze(result);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed: ' + error.message);
      if (onError) onError();
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="shortlisting-screen">
      <div className="container">
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '30px' }}>
          <a href="#" onClick={(e) => { e.preventDefault(); onBack(); }} className="back-link" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: '500' }}>
            <ArrowLeft size={18} />
            Back to Home
          </a>
        </div>

        <div className="form-header">
          <h1>Resume Shortlisting</h1>
          <p className="section-subtitle">Fill in the details to find the perfect candidates</p>
        </div>

        <form className="form-container" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Job Circular (Description)</label>
            <textarea 
              name="job_circular"
              className="form-control" 
              placeholder="Tell us about the job..."
              required
              value={formData.job_circular}
              onChange={handleInput}
              disabled={isAnalyzing}
            ></textarea>
          </div>

          <div className="form-group">
            <label>Must-Have Skills (Optional)</label>
            <input 
              type="text" 
              name="skills"
              className="form-control" 
              placeholder="e.g. React, Node.js, Python (comma separated)" 
              value={formData.skills}
              onChange={handleInput}
              disabled={isAnalyzing}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Minimum Experience (Optional)</label>
              <input 
                type="number" 
                name="min_experience"
                className="form-control" 
                placeholder="e.g. 2" 
                min="0"
                value={formData.min_experience}
                onChange={handleInput}
                disabled={isAnalyzing}
              />
            </div>
            <div className="form-group">
              <label>Top Candidates to Scan</label>
              <input 
                type="number" 
                name="top_k"
                className="form-control" 
                placeholder="e.g. 5" 
                min="1"
                required
                value={formData.top_k}
                onChange={handleInput}
                disabled={isAnalyzing}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Upload Resumes</label>
            <input 
              type="file" 
              id="resume-upload" 
              style={{ display: 'none' }} 
              onChange={handleFile}
              accept=".zip,.pdf,.docx,.doc,.jpg,.jpeg,.png,.webp"
              disabled={isAnalyzing}
            />
            <div 
              className="upload-area" 
              onClick={() => !isAnalyzing && document.getElementById('resume-upload').click()}
              style={{ 
                border: formData.resume_files ? '2px solid var(--accent-cyan)' : '',
                opacity: isAnalyzing ? 0.6 : 1,
                cursor: isAnalyzing ? 'not-allowed' : 'pointer'
              }}
            >
              <div className="upload-icon">
                <Upload size={24} />
              </div>
              <p>{formData.resume_files ? formData.resume_files.name : 'Click to upload or drag and drop'}</p>
              <span>ZIP, PDF, DOCX, or image files</span>
            </div>
          </div>

          <button type="submit" className="btn-submit" disabled={isAnalyzing}>
            {isAnalyzing ? (
              <span className="loader-container">
                <span className="loader"></span>
                Analyzing...
              </span>
            ) : (
              'Analyze Resumes'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Shortlisting;
