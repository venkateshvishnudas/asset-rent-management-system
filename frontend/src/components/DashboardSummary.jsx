import React from 'react';

const DashboardSummary = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="card-grid">
      <div className="card">
        <h3>Total Tenants</h3>
        <p>{summary.total_tenants}</p>
      </div>
      <div className="card">
        <h3>Expected Rent (Current Month)</h3>
        <p>${summary.total_expected_rent_current_month.toFixed(2)}</p>
      </div>
      <div className="card collected">
        <h3>Collected (Current Month)</h3>
        <p>${summary.total_collected_current_month.toFixed(2)}</p>
      </div>
      <div className="card pending">
        <h3>Pending (Current Month)</h3>
        <p>${summary.total_pending_current_month.toFixed(2)}</p>
      </div>
    </div>
  );
};

export default DashboardSummary;
