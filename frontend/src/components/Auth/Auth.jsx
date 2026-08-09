import React, { useState, useEffect } from 'react';
import { Users, Mail, ShieldCheck, Eye, EyeOff, FileText, Zap } from 'lucide-react';
import { authApi } from '../../api';
import AlertModal from '../Common/AlertModal';
import { useGoogleLogin, GoogleLogin } from '@react-oauth/google';

function Auth({ mode, onToggleMode, onSuccess, onBack }) {
  const handleGoogleSuccess = async (credentialResponse) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await authApi.googleLogin(credentialResponse.credential);
      if (data && (data.access || data.token || data.refresh || data.status === 'success')) {
        onSuccess(data);
      } else {
        setError(data.message || data.error || 'Google login failed');
      }
    } catch (err) {
      setError('Unable to connect to the server');
    } finally {
      setIsLoading(false);
    }
  };
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [modalConfig, setModalConfig] = useState({ isOpen: false, title: '', message: '', type: 'success' });

  const showAlert = (title, message, type = 'success') => {
    setModalConfig({ isOpen: true, title, message, type });
  };

  useEffect(() => {
    const savedEmail = localStorage.getItem('cvjachai_remembered_email');
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  const validateForm = () => {
    if (mode === 'signup') {
      if (!firstName.trim()) {
        setError('First name is required');
        return false;
      }
      if (!lastName.trim()) {
        setError('Last name is required');
        return false;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return false;
      }
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsLoading(true);
    setError('');

    try {
      console.log('Attempting Auth with:', { mode, email, firstName, lastName });
      
      let data;
      if (mode === 'login') {
        data = await authApi.signin(email, password);
      } else {
        data = await authApi.signup(firstName, lastName, email, password);
      }

      console.log('Auth API Response:', data);

      // Enhanced success check for both login (access/token) and signup (message/user)
      const isSignupSuccess = mode === 'signup' && (data.message?.toLowerCase().includes('success') || data.user);
      const isLoginSuccess = mode === 'login' && (data.access || data.token || data.refresh);

      if (data && (isLoginSuccess || isSignupSuccess || data.status === 'success')) {
        if (mode === 'signup') {
          // If it was a signup, show success message and switch to login mode
          setError(''); // Clear any previous errors
          showAlert('Account Created', 'Registration successful! Please login with your credentials.', 'success');
          onToggleMode(); // Switch to login screen
        } else {
          // If it was a login, proceed as normal
          if (rememberMe) {
            localStorage.setItem('cvjachai_remembered_email', email);
          } else {
            localStorage.removeItem('cvjachai_remembered_email');
          }
          onSuccess(data);
        }
      } else {
        // More robust error message extraction
        let errorMsg = data.msg || data.message || data.detail || data.error;
        if (!errorMsg && typeof data === 'object' && Object.keys(data).length > 0) {
          // Handle DRF field errors like {"email": ["User with this email already exists."]}
          const firstKey = Object.keys(data)[0];
          if (Array.isArray(data[firstKey])) {
            errorMsg = `${firstKey.charAt(0).toUpperCase() + firstKey.slice(1)}: ${data[firstKey][0]}`;
          } else if (typeof data[firstKey] === 'string') {
            errorMsg = data[firstKey];
          }
        }
        errorMsg = errorMsg || (typeof data === 'string' ? data : null) || 'Authentication failed. Please check your credentials.';
        setError(String(errorMsg));
      }
    } catch (err) {
      console.error('Auth Request Error:', err);
      setError('Unable to connect to the server. Please check your internet connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const [otpCode, setOtpCode] = useState('');
  const [forgotStep, setForgotStep] = useState(1); // 1: Email, 2: OTP + New Password

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (forgotStep === 1) {
      if (!email) {
        setError('Please enter your email address');
        return;
      }
      
      setIsLoading(true);
      setError('');
      
      try {
        const data = await authApi.requestOtp(email);
        if (data && (data.status === 'success' || data.message)) {
          showAlert('OTP Sent', data.message || 'OTP has been sent to your email.', 'info');
          setForgotStep(2);
        } else {
          setError(data.message || data.error || 'Failed to send OTP.');
        }
      } catch (err) {
        setError('Unable to connect to the server.');
      } finally {
        setIsLoading(false);
      }
    } else {
      if (!otpCode || !password || !confirmPassword) {
        setError('Please fill in all fields');
        return;
      }
      
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      
      setIsLoading(true);
      setError('');
      
      try {
        const data = await authApi.resetPassword(email, otpCode, password);
        if (data && (data.status === 'success' || data.message?.toLowerCase().includes('success'))) {
          showAlert('Password Updated', 'Password reset successful! Please login with your new password.', 'success');
          setIsForgotMode(false);
          setForgotStep(1);
          setPassword('');
          setOtpCode('');
        } else {
          setError(data.message || data.error || 'Failed to reset password.');
        }
      } catch (err) {
        setError('Unable to connect to the server.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const [isForgotMode, setIsForgotMode] = useState(false);

  return (
    <div className="auth-screen">
      <div className="auth-main">
        {/* Left Side: Form */}
        <div className="auth-left">
          <div className="auth-form-container">
            <div className="auth-brand" onClick={onBack} style={{ cursor: 'pointer' }}>
              <h1 className="logo-text">CVJACHAI</h1>
              <p>{isForgotMode ? (forgotStep === 1 ? 'Reset your password' : 'Enter OTP & New Password') : (mode === 'login' ? 'Welcome back to intelligent hiring' : 'Join the future of recruitment')}</p>
            </div>

            {isForgotMode ? (
              <form className="auth-form-fields" onSubmit={handleForgotPassword}>
                {error && <div className="auth-error-message">{error}</div>}
                
                {forgotStep === 1 ? (
                  <div className="form-group-modern">
                    <label>Email Address</label>
                    <div className="input-box">
                      <Mail size={18} className="input-icon-left" />
                      <input
                        type="email"
                        placeholder="name@company.com"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={isLoading}
                      />
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="form-group-modern">
                      <label>OTP Code</label>
                      <div className="input-box">
                        <Zap size={18} className="input-icon-left" />
                        <input
                          type="text"
                          placeholder="123456"
                          required
                          value={otpCode}
                          onChange={(e) => setOtpCode(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    <div className="form-group-modern">
                      <label>New Password</label>
                      <div className="input-box">
                        <ShieldCheck size={18} className="input-icon-left" />
                        <input
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••••"
                          required
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          disabled={isLoading}
                        />
                        <button
                          type="button"
                          className="password-toggle"
                          onClick={() => setShowPassword(!showPassword)}
                          disabled={isLoading}
                        >
                          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>
                    <div className="form-group-modern">
                      <label>Confirm New Password</label>
                      <div className="input-box">
                        <ShieldCheck size={18} className="input-icon-left" />
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          placeholder="••••••••"
                          required
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          disabled={isLoading}
                        />
                        <button
                          type="button"
                          className="password-toggle"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          disabled={isLoading}
                        >
                          {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>
                  </>
                )}
                
                <button type="submit" className="btn-login-gradient" disabled={isLoading}>
                  {isLoading ? 'Processing...' : (forgotStep === 1 ? 'Send OTP' : 'Reset Password')}
                </button>
                
                <div className="forgot-back-link">
                  <a href="#" onClick={(e) => { e.preventDefault(); setIsForgotMode(false); setForgotStep(1); }}>
                    Back to Login
                  </a>
                </div>
              </form>
            ) : (
              <form className="auth-form-fields" onSubmit={handleSubmit}>
                {error && <div className="auth-error-message">{error}</div>}
                {mode === 'signup' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div className="form-group-modern">
                      <label>First Name</label>
                      <div className="input-box">
                        <Users size={18} className="input-icon-left" />
                        <input
                          type="text"
                          placeholder="John"
                          required
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    <div className="form-group-modern">
                      <label>Last Name</label>
                      <div className="input-box">
                        <Users size={18} className="input-icon-left" />
                        <input
                          type="text"
                          placeholder="Doe"
                          required
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                  </div>
                )}

                <div className="form-group-modern">
                  <label>Email Address</label>
                  <div className="input-box">
                    <Mail size={18} className="input-icon-left" />
                    <input
                      type="email"
                      placeholder="name@company.com"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div className="form-group-modern">
                  <label>Password</label>
                  <div className="input-box">
                    <ShieldCheck size={18} className="input-icon-left" />
                    <input
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={isLoading}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={isLoading}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {mode === 'signup' && (
                  <div className="form-group-modern">
                    <label>Confirm Password</label>
                    <div className="input-box">
                      <ShieldCheck size={18} className="input-icon-left" />
                      <input
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="••••••••"
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        disabled={isLoading}
                      >
                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                )}

                <div className="form-options">
                  <label className="checkbox-container">
                    <input 
                      type="checkbox" 
                      disabled={isLoading} 
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                    />
                    <span className="checkmark"></span>
                    Remember me
                  </label>
                  {mode === 'login' && (
                    <a href="#" className="forgot-link" onClick={(e) => { e.preventDefault(); setIsForgotMode(true); }}>
                      Forgot password?
                    </a>
                  )}
                </div>

                <button type="submit" className="btn-login-gradient" disabled={isLoading}>
                  {isLoading ? (
                    <span className="loader-container">
                      <span className="loader"></span>
                      Processing...
                    </span>
                  ) : (
                    mode === 'login' ? 'Login' : 'Sign Up'
                  )}
                </button>

                <div className="auth-divider">OR</div>

                <div className="google-login-container" style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => setError('Google Login Failed')}
                    useOneTap
                    theme="filled_black"
                    shape="rectangular"
                    width="340"
                    text={mode === 'login' ? 'signin_with' : 'signup_with'}
                  />
                </div>
              </form>
            )}

            <AlertModal 
              isOpen={modalConfig.isOpen}
              onClose={() => setModalConfig({ ...modalConfig, isOpen: false })}
              title={modalConfig.title}
              message={modalConfig.message}
              type={modalConfig.type}
            />


            <div className="auth-switch">
              {isForgotMode ? (
                <>
                  <span>Don't have an account?</span>
                  <button onClick={() => { setIsForgotMode(false); onToggleMode(); }}>Sign Up</button>
                </>
              ) : (
                <>
                  <span>{mode === 'login' ? "Don't have an account?" : "Already have an account?"}</span>
                  <button onClick={onToggleMode}>{mode === 'login' ? 'Sign Up' : 'Login'}</button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Visual */}
        <div className="auth-right">
          <div className="visual-wrapper">
            <div className="visual-card">
              <div className="card-header-cv">
                <div className="cv-icon"><FileText size={16} /></div>
                <div className="cv-details">
                  <span className="cv-label">CANDIDATE CV</span>
                  <span className="cv-name">Alex Rivers.pdf</span>
                </div>
              </div>
              <div className="cv-progress-bar">
                <div className="progress-fill"></div>
              </div>

              <div className="ai-chip-visual">
                <div className="chip-rect">
                  <span className="chip-text">AI</span>
                  <span className="chip-sub">INTERNVACE</span>
                </div>
                <div className="pulse-circle"></div>
              </div>

              <div className="match-score-card">
                <span className="match-label">MATCH SCORE</span>
                <span className="match-value">95%</span>
                <div className="match-badge">
                  <Zap size={10} fill="currentColor" />
                  EXCELLENT FIT
                </div>
              </div>

              <div className="skill-tags">
                <span className="tag">AI Engineering</span>
                <span className="tag">PyTorch</span>
              </div>
            </div>

            <div className="visual-text">
              <h2>Architecting the future of recruitment.</h2>
              <p>Leverage our deep neural networks to identify top 1% talent in seconds, not weeks.</p>
            </div>
          </div>
        </div>
      </div>

      <footer className="auth-footer-modern">
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="footer-left-modern">
            <span className="footer-brand-name">CVJACHAI</span>
            <span className="copyright">© 2026 CVJACHAI. Architecting the future of recruitment.</span>
          </div>
          <div className="footer-right-modern">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Security</a>
            <a href="#">Status</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Auth;
