const API_BASE_URL = 'http://127.0.0.1:8000';

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Something went wrong');
  }
  return response.json();
};

export const getDashboardSummary = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard-summary`);
  return handleResponse(response);
};

export const getTenants = async () => {
  const response = await fetch(`${API_BASE_URL}/tenants`);
  return handleResponse(response);
};

export const createTenant = async (tenantData) => {
  const response = await fetch(`${API_BASE_URL}/tenants`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(tenantData),
  });
  return handleResponse(response);
};

export const recordPayment = async (paymentData) => {
  const response = await fetch(`${API_BASE_URL}/payments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(paymentData),
  });
  return handleResponse(response);
};

export const getTenantHistory = async (tenantId, month = null) => {
  const url = month 
    ? `${API_BASE_URL}/tenant/${tenantId}/history?month=${month}` 
    : `${API_BASE_URL}/tenant/${tenantId}/history`;
  const response = await fetch(url);
  return handleResponse(response);
};
