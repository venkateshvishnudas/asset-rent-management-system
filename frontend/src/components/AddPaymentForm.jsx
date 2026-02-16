import React, { useState } from 'react';

const AddPaymentForm = ({ tenantId, onPaymentRecorded, onCancel }) => {
  const [amount, setAmount] = useState('');
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const paymentData = {
        tenant_id: tenantId,
        amount: parseFloat(amount),
        payment_date: paymentDate,
        notes: notes,
      };
      await onPaymentRecorded(paymentData);
      setSuccess('Payment recorded successfully!');
      // Optionally reset form or close modal after a short delay
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="amount">Amount:</label>
        <input 
          type="number" 
          id="amount" 
          step="0.01" 
          value={amount} 
          onChange={(e) => setAmount(e.target.value)} 
          required 
        />
      </div>
      <div className="form-group">
        <label htmlFor="paymentDate">Payment Date:</label>
        <input 
          type="date" 
          id="paymentDate" 
          value={paymentDate} 
          onChange={(e) => setPaymentDate(e.target.value)} 
          required 
        />
      </div>
      <div className="form-group">
        <label htmlFor="notes">Notes (Optional):</label>
        <textarea 
          id="notes" 
          value={notes} 
          onChange={(e) => setNotes(e.target.value)} 
          rows="3"
        ></textarea>
      </div>
      {error && <p className="error-message">{error}</p>}
      {success && <p className="success-message">{success}</p>}
      <button type="submit" className="btn">Record Payment</button>
      <button type="button" className="btn secondary" onClick={onCancel} style={{marginLeft: '10px'}}>Cancel</button>
    </form>
  );
};

export default AddPaymentForm;
