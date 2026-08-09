import React from 'react';
import {
  Sparkles,
  Zap,
  ChevronRight,
  Target,
  Search,
  BarChart3,
  ShieldCheck,
  Clock,
  Users,
  CheckCircle2,
  Globe,
  Twitter,
  Linkedin,
  Github,
  Mail
} from 'lucide-react';
import { FeatureCard, TrustCard } from '../Common/Common';

function Home({ isLoggedIn, onStartShortlisting, onStartPersonalization, onFindJob, onCreateJob }) {
  return (
    <>
      {/* Hero Section */}
      <header className="hero">
        <div className="container hero-container">
          <div className="hero-content">
            <div className="badge">
              <Zap className="badge-icon" />
              Powered by advanced AI
            </div>
            <h1>
              CV Jachai <br />
              Advanced CV Screening <br />
              <span className="gradient-text">& HR Intelligence</span>
            </h1>
            <p className="hero-description">
              Empower your HR team with CV Jachai. Experience lightning-fast candidate screening, automated qualification matching, and AI-driven hiring insights.
            </p>
            <div className="hero-btns" style={{ display: 'flex', flexWrap: 'wrap', gap: '15px' }}>
              <button onClick={onStartShortlisting} className="btn-primary" style={{ border: 'none', cursor: 'pointer' }}>
                Resume Shortlisting
                <ChevronRight size={18} />
              </button>
              <button onClick={onStartPersonalization} className="btn-secondary" style={{ cursor: 'pointer' }}>
                Resume Personalization
              </button>
              <button 
                onClick={onFindJob} 
                className="btn-primary" 
                style={{ 
                  border: 'none', 
                  cursor: 'pointer', 
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%)',
                  boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)',
                  padding: '12px 30px',
                  fontSize: '1.1rem',
                  fontWeight: '600'
                }}
              >
                Find job
                <Search size={18} style={{ marginLeft: '8px' }} />
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat-item">
                <h3>95%</h3>
                <p>Accuracy</p>
              </div>
              <div className="stat-item">
                <h3>10x</h3>
                <p>Faster</p>
              </div>
              <div className="stat-item">
                <h3>50K+</h3>
                <p>Analyzed</p>
              </div>
            </div>
          </div>
          <div className="hero-image">
            <img src="/assets/Container.svg" alt="AI Resume Analysis Visualization" />
          </div>
        </div>
      </header>

      {/* Features Section */}
      <section className="features-section" id="features">
        <div className="container">
          <div className="section-header">
            <div className="badge">
              <Target className="badge-icon" />
              Advanced Features
            </div>
            <h2 className="section-title">Next-Gen Hiring Intelligence</h2>
            <p className="section-subtitle">
              Powerful AI-driven features to revolutionize your recruitment.
            </p>
          </div>

          <div className="features-grid">
            <FeatureCard
              icon={<Zap size={24} color="#f59e0b" />}
              bg="#fef3c7"
              title="Instant Analysis"
              description="AI-powered resume screening in seconds with deeper insights on qualifications."
            />
            <FeatureCard
              icon={<Search size={24} color="#06b6d4" />}
              bg="#ecfeff"
              title="Precision Matching"
              description="Advanced algorithms match candidates to job requirements with accuracy."
            />
            <FeatureCard
              icon={<BarChart3 size={24} color="#ec4899" />}
              bg="#fdf2f8"
              title="Smart Analytics"
              description="Comprehensive insights to make informed hiring decisions across your pipeline."
            />
            <FeatureCard
              icon={<ShieldCheck size={24} color="#10b981" />}
              bg="#ecfdf5"
              title="Bias Reduction"
              description="Fair evaluation process focused on skills and qualifications alone."
            />
            <FeatureCard
              icon={<Clock size={24} color="#ef4444" />}
              bg="#fef2f2"
              title="Time Saving"
              description="Reduce screening time by 90% while improving talent quality."
            />
            <FeatureCard
              icon={<Users size={24} color="#8b5cf6" />}
              bg="#f5f3ff"
              title="Team Collaboration"
              description="Share insights and collaborate with your hiring team seamlessly."
            />
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="trust-section">
        <div className="glow-purple" style={{ bottom: '0', left: '20%' }}></div>
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Trusted by Industry Leaders</h2>
            <p className="section-subtitle">Real metrics from real impact</p>
          </div>

          <div className="trust-grid">
            <TrustCard
              icon={<Users size={20} />}
              value="50,000+"
              label="Resumes Analyzed"
            />
            <TrustCard
              icon={<Target size={20} />}
              value="1,200+"
              label="Companies"
            />
            <TrustCard
              icon={<CheckCircle2 size={20} />}
              value="95%"
              label="Accuracy Rate"
            />
            <TrustCard
              icon={<Globe size={20} />}
              value="40+"
              label="Countries"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer>
        <div className="container">
          <div className="footer-grid">
            <div className="footer-info">
              <div className="logo">
                <div className="logo-icon">
                  <Sparkles size={18} color="white" fill="white" />
                </div>
                <span>CVJACHAI</span>
              </div>
              <p>AI-powered resume analysis platform for the future of hiring.</p>
              <div className="social-links">
                <a href="#" className="social-icon"><Twitter size={18} /></a>
                <a href="#" className="social-icon"><Linkedin size={18} /></a>
                <a href="#" className="social-icon"><Github size={18} /></a>
                <a href="#" className="social-icon"><Mail size={18} /></a>
              </div>
            </div>
            <div className="footer-links">
              <h4>Product</h4>
              <ul>
                <li><a href="#">Features</a></li>
                <li><a href="#">Pricing</a></li>
                <li><a href="#">Integrations</a></li>
                <li><a href="#">API</a></li>
              </ul>
            </div>
            <div className="footer-links">
              <h4>Company</h4>
              <ul>
                <li><a href="#">About</a></li>
                <li><a href="#">Careers</a></li>
                <li><a href="#">Blog</a></li>
                <li><a href="#">Contact</a></li>
              </ul>
            </div>
            <div className="footer-links">
              <h4>Legal</h4>
              <ul>
                <li><a href="#">Privacy</a></li>
                <li><a href="#">Terms</a></li>
                <li><a href="#">Cookies</a></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2026 CVJACHAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </>
  );
}

export default Home;
