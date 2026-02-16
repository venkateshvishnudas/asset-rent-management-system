import React, { useState, useEffect, useCallback } from 'react';
import { 
  getDashboardSummary, 
  getTenants, 
  createTenant, 
  recordPayment, 
  getTenantHistory 
} from './api';
import DashboardSummary from './components/DashboardSummary';
import TenantList from './components/TenantList';
import AddPaymentForm from './components/AddPaymentForm';
import TenantHistoryDrawer from './components/TenantHistoryDrawer';

function App() {
  const [summary, setSummary] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddTenantModal, setShowAddTenantModal] = useState(false);
  const [showAddPaymentModal, setShowAddPaymentModal] = useState(false);
  const [selectedTenantForPayment, setSelectedTenantForPayment] = useState(null);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [selectedTenantForHistory, setSelectedTenantForHistory] = useState(null);
  const [tenantHistory, setTenantHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, tenantsData] = await Promise.all([
        getDashboardSummary(),
        getTenants()
      ]);
      setSummary(summaryData);
      setTenants(tenantsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAddTenant = async (tenantData) => {
    try {
      await createTenant(tenantData);
      setShowAddTenantModal(false);
      fetchData(); // Refresh data
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRecordPayment = async (paymentData) => {
    try {
      await recordPayment(paymentData);
      setShowAddPaymentModal(false);
      setSelectedTenantForPayment(null);
      fetchData(); // Refresh data
    } catch (err) {
      setError(err.message);
    }
  };

  const viewTenantHistory = async (tenantId) => {
    setSelectedTenantForHistory(tenantId);
    setShowHistoryDrawer(true);
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const historyData = await getTenantHistory(tenantId);
      setTenantHistory(historyData);
    } catch (err) {
      setHistoryError(err.message);
    } finally {
      setHistoryLoading(false);
    }
  };

  if (loading) return <div className="container">Loading...</div>;
  if (error) return <div className="container error-message">Error: {error}</div>;

  return (
    <div className="container">
      <h1>Rent Management Dashboard</h1>

      {summary && <DashboardSummary summary={summary} />}

      <div className="section-header">
        <h2>Tenants</h2>
        <button className="btn" onClick={() => setShowAddTenantModal(true)}>Add New Tenant</button>
      </div>
      
      {tenants && 
        <TenantList 
          tenants={tenants} 
          onAddPayment={(tenant) => {
            setSelectedTenantForPayment(tenant);
            setShowAddPaymentModal(true);
          }}
          onViewHistory={(tenantId) => viewTenantHistory(tenantId)}
        />
      }

      {/* Add Tenant Modal */}
      {showAddTenantModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="modal-close-btn" onClick={() => setShowAddTenantModal(false)}>&times;</button>
            <h2>Add New Tenant</h2>
            <form onSubmit={async (e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              await handleAddTenant({
                name: formData.get('name'),
                monthly_rent: parseFloat(formData.get('monthly_rent')),
                contact_email: formData.get('contact_email'),
                move_in_date: formData.get('move_in_date'),
              });
            }}>
              <div className="form-group">
                <label htmlFor="name">Name:</label>
                <input type="text" id="name" name="name" required />
              </div>
              <div className="form-group">
                <label htmlFor="monthly_rent">Monthly Rent:</label>
                <input type="number" id="monthly_rent" name="monthly_rent" step="0.01" required />
              </div>
              <div className="form-group">
                <label htmlFor="contact_email">Email:</label>
                <input type="email" id="contact_email" name="contact_email" />
              </div>
              <div className="form-group">
                <label htmlFor="move_in_date">Move-in Date:</label>
                <input type="date" id="move_in_date" name="move_in_date" required />
              </div>
              <button type="submit" className="btn">Create Tenant</button>
            </form>
          </div>
        </div>
      )}

      {/* Add Payment Modal */}
      {showAddPaymentModal && selectedTenantForPayment && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="modal-close-btn" onClick={() => setShowAddPaymentModal(false)}>&times;</button>
            <h2>Record Payment for {selectedTenantForPayment.name}</h2>
            <AddPaymentForm 
              tenantId={selectedTenantForPayment.id}
              onPaymentRecorded={handleRecordPayment}
              onCancel={() => {
                setShowAddPaymentModal(false);
                setSelectedTenantForPayment(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Tenant History Drawer */}
      {showHistoryDrawer && selectedTenantForHistory && (
        <TenantHistoryDrawer
          tenantId={selectedTenantForHistory}
          tenantHistory={tenantHistory}
          loading={historyLoading}
          error={historyError}
          onClose={() => {
            setShowHistoryDrawer(false);
            setSelectedTenantForHistory(null);
            setTenantHistory(null);
          }}
        />
      )}
    </div>
  );
}

export default App;
