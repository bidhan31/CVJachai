import React from 'react';
import { Sparkles, Briefcase, PlusCircle, LogOut } from 'lucide-react';

function Navbar({ isLoggedIn, onLogout, onLogin, onSignUp, onCreateJob, onJobManagement }) {
  return (
    <nav className="main-nav">
      <div className="container nav-container">
        <div className="logo" onClick={() => window.location.href = '/'}>
          <div className="logo-icon">
            <Sparkles size={18} color="white" fill="white" />
          </div>
          <span className="logo-text-brand">CVJACHAI</span>
        </div>
        
        <div className="nav-auth-btns">
          {isLoggedIn ? (
            <>
              <button onClick={onJobManagement} className="btn-nav btn-manage">
                <Briefcase size={16} />
                <span className="btn-text">Job Management</span>
                <span className="btn-text-mobile">Manage</span>
              </button>
              <button onClick={onCreateJob} className="btn-nav btn-create">
                <PlusCircle size={16} />
                <span className="btn-text">Create Job</span>
                <span className="btn-text-mobile">Create</span>
              </button>
              <button onClick={onLogout} className="btn-nav btn-logout-custom" title="Logout">
                <LogOut size={16} />
                <span className="btn-text">Logout</span>
              </button>
            </>
          ) : (
            <>
              <a href="#" onClick={(e) => { e.preventDefault(); onLogin(); }} className="btn-login">Login</a>
              <a href="#" onClick={(e) => { e.preventDefault(); onSignUp(); }} className="btn-signup">Sign Up</a>
            </>
          )}
        </div>
      </div>
      <style>{`
        .main-nav {
          position: sticky;
          top: 0;
          z-index: 100;
          background: rgba(10, 15, 28, 0.85);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          padding: 1rem 0;
        }
        .nav-container {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
        }
        .logo {
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
        }
        .logo-text-brand {
          font-weight: 800;
          font-size: 1.3rem;
          letter-spacing: 1px;
          color: white;
        }
        .nav-auth-btns {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .btn-nav {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.95rem;
          transition: all 0.3s ease;
          cursor: pointer;
          font-family: inherit;
        }
        .btn-manage {
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: white;
          background: rgba(255, 255, 255, 0.05);
        }
        .btn-manage:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.4);
        }
        .btn-create {
          border: 1px solid var(--accent-cyan);
          color: var(--accent-cyan);
          background: transparent;
        }
        .btn-create:hover {
          background: rgba(34, 211, 238, 0.1);
          box-shadow: 0 0 15px rgba(34, 211, 238, 0.2);
        }
        .btn-logout-custom {
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #ef4444;
          background: transparent;
          padding: 10px 16px;
        }
        .btn-logout-custom:hover {
          background: rgba(239, 68, 68, 0.1);
          border-color: #ef4444;
        }
        .btn-text-mobile {
          display: none;
        }

        /* Mobile & Tablet Responsiveness */
        @media (max-width: 850px) {
          .main-nav {
            padding: 0.8rem 0;
          }
          .logo-text-brand {
            font-size: 1.1rem;
          }
          .nav-auth-btns {
            gap: 8px;
          }
          .btn-nav {
            padding: 8px 12px;
            font-size: 0.85rem;
            border-radius: 10px;
          }
          .btn-text {
            display: none;
          }
          .btn-text-mobile {
            display: inline;
          }
        }

        @media (max-width: 480px) {
          .logo {
            gap: 8px;
          }
          .logo-text-brand {
            display: none; /* Hide brand text on very small screens to keep navbar super clean */
          }
          .nav-auth-btns {
            gap: 6px;
          }
          .btn-nav {
            padding: 8px 12px;
            font-size: 0.8rem;
            gap: 6px;
          }
          .btn-logout-custom {
            padding: 8px 10px;
          }
        }
      `}</style>
    </nav>
  );
}

export default Navbar;
