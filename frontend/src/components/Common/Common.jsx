import React from 'react';

export const FeatureCard = ({ icon, title, description, bg }) => {
  return (
    <div className="feature-card">
      <div
        className="feature-icon-wrapper"
        style={{ backgroundColor: bg }}
      >
        {icon}
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
};

export const TrustCard = ({ icon, value, label }) => {
  return (
    <div className="trust-card">
      <div className="icon-small">{icon}</div>
      <h2>{value}</h2>
      <p>{label}</p>
    </div>
  );
};
