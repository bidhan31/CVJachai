import React from 'react';
import { Sparkles, CheckCircle2, AlertCircle, X } from 'lucide-react';

const AlertModal = ({ isOpen, onClose, title, message, type = 'success' }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose}>
          <X size={20} />
        </button>
        
        <div className={`modal-icon ${type}`}>
          {type === 'success' ? <CheckCircle2 size={32} /> : 
           type === 'error' ? <AlertCircle size={32} /> : 
           <Sparkles size={32} />}
        </div>
        
        <h3 className="modal-title">{title}</h3>
        <p className="modal-message">{message}</p>
        
        <button className="btn-modal" onClick={onClose}>
          Got it
        </button>
      </div>
    </div>
  );
};

export default AlertModal;
