import React from 'react';

const TenantHistoryDrawer = ({ tenantId, tenantHistory, loading, error, onClose }) => {
  if (!tenantId) return null;

  return (
    <div className="drawer-overlay">
      <div className="drawer-content">
        <button className="drawer-close-btn" onClick={onClose}>&times;</button>
        {loading && <h2>Loading History...</h2>}
        {error && <h2 className="error-message">Error loading history: {error}</h2>}
        {tenantHistory && (
          <>
            <h2>Payment History for {tenantHistory.tenant.name}</h2>
            <p>Monthly Rent: ${tenantHistory.tenant.monthly_rent.toFixed(2)}</p>
            
            <h3>Monthly Due Status:</h3>
            {tenantHistory.monthly_due_status.length > 0 ? (
              tenantHistory.monthly_due_status.map((status) => (
                <div key={status.month} className={`history-item ${status.is_paid_in_full ? 'paid' : 'pending'}`}>
                  <strong>Month: {status.month}</strong><br />
                  Expected: ${status.expected_rent.toFixed(2)}<br />
                  Paid: ${status.paid_amount.toFixed(2)}<br />
                  Pending: ${status.pending_amount.toFixed(2)}<br />
                  Status: {status.is_paid_in_full ? 'Paid in Full' : 'Pending'}
                </div>
              ))
            ) : (
              <p>No monthly due records found.</p>
            )}

            <h3>Recent Payments:</h3>
            {tenantHistory.payments.length > 0 ? (
              tenantHistory.payments.map((payment) => (
                <div key={payment.payment_id} className="history-item">
                  <strong>Date: {new Date(payment.payment_date).toLocaleDateString()}</strong><br />
                  Amount: ${payment.amount.toFixed(2)}<br />
                  Notes: {payment.notes || 'N/A'}
                </div>
              ))
            ) : (
              <p>No payments recorded for this tenant.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TenantHistoryDrawer;
