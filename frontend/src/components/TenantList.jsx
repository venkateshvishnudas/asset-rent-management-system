import React from 'react';

const TenantList = ({ tenants, onAddPayment, onViewHistory }) => {
  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Monthly Rent</th>
            <th>Email</th>
            <th>Move-in Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {tenants.map((tenant) => (
            <tr key={tenant.id}>
              <td>{tenant.name}</td>
              <td>${tenant.monthly_rent.toFixed(2)}</td>
              <td>{tenant.contact_email || 'N/A'}</td>
              <td>{new Date(tenant.move_in_date).toLocaleDateString()}</td>
              <td>
                <button className="btn secondary" onClick={() => onAddPayment(tenant)}>Record Payment</button>
                <button className="btn secondary" onClick={() => onViewHistory(tenant.id)} style={{ marginLeft: '10px' }}>View History</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TenantList;
