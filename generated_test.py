import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
import uuid

# Import the FastAPI app and in-memory databases from your main.py
from backend.main import app, tenants_db, payments_db, get_tenant_by_id, calculate_monthly_dues_for_tenant, Tenant

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db_before_each_test():
    """Fixture to clear the in-memory databases before each test."""
    tenants_db.clear()
    payments_db.clear()
    yield
    tenants_db.clear()
    payments_db.clear()

# --- Root Endpoint Test ---

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Asset/Rent Management System API. Visit /docs for API documentation."
}

# --- Tenant Endpoints ---

def test_create_tenant():
    tenant_data = {
        "name": "Alice Smith",
        "monthly_rent": 1200.00,
        "contact_email": "alice@example.com",
        "move_in_date": "2023-01-15"
    }
    response = client.post("/tenants", json=tenant_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == tenant_data["name"]
    assert data["monthly_rent"] == tenant_data["monthly_rent"]
    assert data["contact_email"] == tenant_data["contact_email"]
    assert data["move_in_date"] == tenant_data["move_in_date"]
    assert "created_at" in data
    
    assert len(tenants_db) == 1
    assert tenants_db[0]["id"] == data["id"]

def test_create_tenant_missing_required_field():
    tenant_data = {
        "name": "Bob",
        "monthly_rent": 1000.00,
        "move_in_date": "2023-03-01"
        # contact_email is optional, but if rent is missing, it should fail
    }
    # Remove monthly_rent to trigger error
    del tenant_data["monthly_rent"]
    response = client.post("/tenants", json=tenant_data)
    assert response.status_code == 422 # Unprocessable Entity
    assert "monthly_rent" in response.json()["detail"][0]["loc"]

def test_create_tenant_invalid_rent():
    tenant_data = {
        "name": "Charlie",
        "monthly_rent": -500.00, # Invalid rent
        "move_in_date": "2023-04-01"
    }
    response = client.post("/tenants", json=tenant_data)
    assert response.status_code == 422
    assert "monthly_rent" in response.json()["detail"][0]["loc"]
    assert "greater than 0" in response.json()["detail"][0]["msg"]

def test_get_all_tenants_empty():
    response = client.get("/tenants")
    assert response.status_code == 200
    assert response.json() == []

def test_get_all_tenants_multiple():
    tenant_data1 = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": "2023-01-01"}
    tenant_data2 = {"name": "Bob", "monthly_rent": 1500.00, "move_in_date": "2023-02-01"}
    
    client.post("/tenants", json=tenant_data1)
    client.post("/tenants", json=tenant_data2)
    
    response = client.get("/tenants")
    assert response.status_code == 200
    tenants = response.json()
    assert len(tenants) == 2
    assert any(t["name"] == "Alice" for t in tenants)
    assert any(t["name"] == "Bob" for t in tenants)

# --- Payment Endpoints ---

def test_record_payment_success():
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": "2023-01-01"}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    payment_data = {
        "tenant_id": tenant_id,
        "amount": 500.00,
        "payment_date": "2024-06-10",
        "notes": "Partial rent for June"
    }
    response = client.post("/payments", json=payment_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["tenant_id"] == tenant_id
    assert data["amount"] == payment_data["amount"]
    assert data["payment_date"] == payment_data["payment_date"]
    assert "recorded_at" in data

    assert len(payments_db) == 1
    assert payments_db[0]["id"] == data["id"]

def test_record_payment_tenant_not_found():
    payment_data = {
        "tenant_id": str(uuid.uuid4()), # Non-existent ID
        "amount": 1000.00,
        "payment_date": "2024-06-10"
    }
    response = client.post("/payments", json=payment_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Tenant not found"}

def test_record_payment_invalid_amount():
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": "2023-01-01"}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    payment_data = {
        "tenant_id": tenant_id,
        "amount": -100.00, # Invalid amount
        "payment_date": "2024-06-10"
    }
    response = client.post("/payments", json=payment_data)
    assert response.status_code == 422
    assert "amount" in response.json()["detail"][0]["loc"]
    assert "greater than 0" in response.json()["detail"][0]["msg"]

# --- Dashboard Summary Endpoints ---

def test_get_dashboard_summary_empty():
    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    expected_summary = {
        "total_expected_rent_current_month": 0.0,
        "total_collected_current_month": 0.0,
        "total_pending_current_month": 0.0,
        "total_tenants": 0
    }
    assert response.json() == expected_summary

def test_get_dashboard_summary_one_tenant_no_payment():
    today = date.today()
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": (today - timedelta(days=30)).strftime('%Y-%m-%d')}
    client.post("/tenants", json=tenant_data)

    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    expected_summary = {
        "total_expected_rent_current_month": 1000.00,
        "total_collected_current_month": 0.0,
        "total_pending_current_month": 1000.00,
        "total_tenants": 1
    }
    assert response.json() == expected_summary

def test_get_dashboard_summary_one_tenant_partial_payment():
    today = date.today()
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": (today - timedelta(days=30)).strftime('%Y-%m-%d')}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    payment_data = {
        "tenant_id": tenant_id,
        "amount": 500.00,
        "payment_date": today.strftime('%Y-%m-%d'),
        "notes": "Partial current month rent"
    }
    client.post("/payments", json=payment_data)

    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    expected_summary = {
        "total_expected_rent_current_month": 1000.00,
        "total_collected_current_month": 500.00,
        "total_pending_current_month": 500.00,
        "total_tenants": 1
    }
    assert response.json() == expected_summary

def test_get_dashboard_summary_one_tenant_full_payment():
    today = date.today()
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": (today - timedelta(days=30)).strftime('%Y-%m-%d')}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    payment_data = {
        "tenant_id": tenant_id,
        "amount": 1000.00,
        "payment_date": today.strftime('%Y-%m-%d'),
        "notes": "Full current month rent"
    }
    client.post("/payments", json=payment_data)

    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    expected_summary = {
        "total_expected_rent_current_month": 1000.00,
        "total_collected_current_month": 1000.00,
        "total_pending_current_month": 0.0,
        "total_tenants": 1
    }
    assert response.json() == expected_summary

def test_get_dashboard_summary_multiple_tenants_mixed_payments():
    today = date.today()
    move_in = (today - timedelta(days=60)).strftime('%Y-%m-%d')

    tenant_data1 = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": move_in}
    tenant1_resp = client.post("/tenants", json=tenant_data1)
    tenant1_id = tenant1_resp.json()["id"]

    tenant_data2 = {"name": "Bob", "monthly_rent": 1500.00, "move_in_date": move_in}
    tenant2_resp = client.post("/tenants", json=tenant_data2)
    tenant2_id = tenant2_resp.json()["id"]

    tenant_data3 = {"name": "Charlie", "monthly_rent": 800.00, "move_in_date": move_in}
    client.post("/tenants", json=tenant_data3)

    # Alice pays half
    client.post("/payments", json={
        "tenant_id": tenant1_id, "amount": 500.00, "payment_date": today.strftime('%Y-%m-%d')
    })
    # Bob pays full
    client.post("/payments", json={
        "tenant_id": tenant2_id, "amount": 1500.00, "payment_date": today.strftime('%Y-%m-%d')
    })

    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    summary = response.json()
    
    assert summary["total_tenants"] == 3
    assert summary["total_expected_rent_current_month"] == (1000.00 + 1500.00 + 800.00)
    assert summary["total_collected_current_month"] == (500.00 + 1500.00)
    assert summary["total_pending_current_month"] == (500.00 + 0.0 + 800.00)

def test_get_dashboard_summary_tenant_future_move_in():
    today = date.today()
    future_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    past_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')

    tenant_data1 = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": past_date}
    client.post("/tenants", json=tenant_data1)

    tenant_data2 = {"name": "Bob", "monthly_rent": 1500.00, "move_in_date": future_date} # This tenant's rent should not be counted for current month
    client.post("/tenants", json=tenant_data2)

    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    summary = response.json()
    
    assert summary["total_tenants"] == 2 # Both tenants exist in DB
    assert summary["total_expected_rent_current_month"] == 1000.00 # Only Alice's rent
    assert summary["total_collected_current_month"] == 0.0
    assert summary["total_pending_current_month"] == 1000.00

# --- Tenant History Endpoint ---

def test_get_tenant_history_not_found():
    response = client.get(f"/tenant/{str(uuid.uuid4())}/history")
    assert response.status_code == 404
    assert response.json() == {"detail": "Tenant not found"}

def test_get_tenant_history_no_payments():
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": "2023-01-01"}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    response = client.get(f"/tenant/{tenant_id}/history")
    assert response.status_code == 200
    history = response.json()
    assert history["tenant"]["id"] == tenant_id
    assert history["payments"] == []
    assert len(history["monthly_due_status"]) > 0
    # Check the first month (Jan 2023)
    assert history["monthly_due_status"][0]["month"] == "2023-01"
    assert history["monthly_due_status"][0]["expected_rent"] == 1000.00
    assert history["monthly_due_status"][0]["paid_amount"] == 0.0
    assert history["monthly_due_status"][0]["pending_amount"] == 1000.00
    assert history["monthly_due_status"][0]["is_paid_in_full"] == False

def test_get_tenant_history_with_payments():
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": "2023-01-01"}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    # Payments: Jan partial, Feb full, Mar overpayment, Apr no payment
    client.post("/payments", json={
        "tenant_id": tenant_id, "amount": 500.00, "payment_date": "2023-01-10", "notes": "Jan part 1"
    })
    client.post("/payments", json={
        "tenant_id": tenant_id, "amount": 500.00, "payment_date": "2023-01-20", "notes": "Jan part 2"
    })
    client.post("/payments", json={
        "tenant_id": tenant_id, "amount": 1000.00, "payment_date": "2023-02-05", "notes": "Feb rent"
    })
    client.post("/payments", json={
        "tenant_id": tenant_id, "amount": 1200.00, "payment_date": "2023-03-01", "notes": "Mar rent + extra"
    })

    response = client.get(f"/tenant/{tenant_id}/history", params={"month": "2023-04"}) # Get history up to April
    assert response.status_code == 200
    history = response.json()

    assert len(history["payments"]) == 4
    # Payments should be sorted by date descending
    assert history["payments"][0]["payment_date"] == "2023-03-01"
    assert history["payments"][1]["payment_date"] == "2023-02-05"

    monthly_dues = {m["month"]: m for m in history["monthly_due_status"]}

    # January
    jan_dues = monthly_dues["2023-01"]
    assert jan_dues["expected_rent"] == 1000.00
    assert jan_dues["paid_amount"] == 1000.00
    assert jan_dues["pending_amount"] == 0.0
    assert jan_dues["is_paid_in_full"] == True

    # February
    feb_dues = monthly_dues["2023-02"]
    assert feb_dues["expected_rent"] == 1000.00
    assert feb_dues["paid_amount"] == 1000.00
    assert feb_dues["pending_amount"] == 0.0
    assert feb_dues["is_paid_in_full"] == True

    # March
    mar_dues = monthly_dues["2023-03"]
    assert mar_dues["expected_rent"] == 1000.00
    assert mar_dues["paid_amount"] == 1200.00 # Overpayment
    assert mar_dues["pending_amount"] == 0.0 # Pending should not be negative
    assert mar_dues["is_paid_in_full"] == True

    # April (no payment)
    apr_dues = monthly_dues["2023-04"]
    assert apr_dues["expected_rent"] == 1000.00
    assert apr_dues["paid_amount"] == 0.0
    assert apr_dues["pending_amount"] == 1000.00
    assert apr_dues["is_paid_in_full"] == False

def test_get_tenant_history_month_parameter():
    tenant_data = {"name": "Bob", "monthly_rent": 1000.00, "move_in_date": "2023-05-01"}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    client.post("/payments", json={
        "tenant_id": tenant_id, "amount": 1000.00, "payment_date": "2023-05-15", "notes": "May rent"
    })

    # Request history up to May
    response = client.get(f"/tenant/{tenant_id}/history", params={"month": "2023-05"})
    assert response.status_code == 200
    history = response.json()
    assert len(history["monthly_due_status"]) == 1 # Only May should be present
    assert history["monthly_due_status"][0]["month"] == "2023-05"
    assert history["monthly_due_status"][0]["is_paid_in_full"] == True

    # Request history up to June (should show May as paid, June as pending)
    response = client.get(f"/tenant/{tenant_id}/history", params={"month": "2023-06"})
    assert response.status_code == 200
    history = response.json()
    assert len(history["monthly_due_status"]) == 2
    assert history["monthly_due_status"][0]["month"] == "2023-05"
    assert history["monthly_due_status"][0]["is_paid_in_full"] == True
    assert history["monthly_due_status"][1]["month"] == "2023-06"
    assert history["monthly_due_status"][1]["is_paid_in_full"] == False

def test_get_tenant_history_invalid_month_format():
    tenant_data = {"name": "Alice", "monthly_rent": 1000.00, "move_in_date": "2023-01-01"}
    create_tenant_response = client.post("/tenants", json=tenant_data)
    tenant_id = create_tenant_response.json()["id"]

    response = client.get(f"/tenant/{tenant_id}/history", params={"month": "2023/01"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid month format. Use YYYY-MM."}

    response = client.get(f"/tenant/{tenant_id}/history", params={"month": "invalid"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid month format. Use YYYY-MM."}

def test_calculate_monthly_dues_for_tenant_helper_function():
    # This tests the helper function directly, though it's covered by API tests
    tenant_id = str(uuid.uuid4())
    today = date.today()
    tenant_move_in = date(today.year - 1, today.month, 1)
    
    # Create a dummy tenant object for the helper function
    tenant_obj = Tenant(
        id=tenant_id,
        name="Test Tenant",
        monthly_rent=1000.00,
        contact_email="test@example.com",
        move_in_date=tenant_move_in,
        created_at=datetime.now()
    )

    # Clear payments_db for isolated test, though fixture usually handles it
    payments_db.clear()

    # Scenario 1: No payments, check current month
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_str = today.strftime('%Y-%m')
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.expected_rent == 1000.00
    assert current_month_due.paid_amount == 0.0
    assert current_month_due.pending_amount == 1000.00
    assert current_month_due.is_paid_in_full == False

    # Scenario 2: Partial payment in the current month
    payment_id1 = str(uuid.uuid4())
    payments_db.append({
        "id": payment_id1,
        "tenant_id": tenant_id,
        "amount": 300.00,
        "payment_date": today,
        "notes": "partial",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.expected_rent == 1000.00
    assert current_month_due.paid_amount == 300.00
    assert current_month_due.pending_amount == 700.00
    assert current_month_due.is_paid_in_full == False
    
    # Scenario 3: Full payment with multiple payments
    payment_id2 = str(uuid.uuid4())
    payments_db.append({
        "id": payment_id2,
        "tenant_id": tenant_id,
        "amount": 700.00,
        "payment_date": today,
        "notes": "remainder",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.expected_rent == 1000.00
    assert current_month_due.paid_amount == 1000.00
    assert current_month_due.pending_amount == 0.0
    assert current_month_due.is_paid_in_full == True

    # Scenario 4: Overpayment
    payment_id3 = str(uuid.uuid4())
    payments_db.append({
        "id": payment_id3,
        "tenant_id": tenant_id,
        "amount": 200.00,
        "payment_date": today,
        "notes": "overpayment",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.expected_rent == 1000.00
    assert current_month_due.paid_amount == 1200.00
    assert current_month_due.pending_amount == 0.0 # Pending should be 0, not negative
    assert current_month_due.is_paid_in_full == True

    # Scenario 5: Tenant moved in mid-month (rent should still be full monthly_rent)
    mid_month_move_in = date(today.year - 1, today.month, 15)
    tenant_obj_mid_month = Tenant(
        id=str(uuid.uuid4()),
        name="Mid-Month Tenant",
        monthly_rent=1500.00,
        contact_email=None,
        move_in_date=mid_month_move_in,
        created_at=datetime.now()
    )
    payments_db.clear()
    monthly_dues_mid_month = calculate_monthly_dues_for_tenant(tenant_obj_mid_month, end_date=today)
    move_in_month_str = mid_month_move_in.strftime('%Y-%m')
    mid_month_due = next(m for m in monthly_dues_mid_month if m.month == move_in_month_str)
    assert mid_month_due.expected_rent == 1500.00 # Still full rent
    assert mid_month_due.paid_amount == 0.0

    # Scenario 6: Test `is_paid_in_full` with floating point precision
    payments_db.clear()
    # One payment just shy
    payments_db.append({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "amount": 999.99,
        "payment_date": today,
        "notes": "",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.paid_amount == 999.99
    assert current_month_due.pending_amount == pytest.approx(0.01)
    assert current_month_due.is_paid_in_full == False # 0.01 pending, so not full

    payments_db.clear()
    # One payment exactly matching
    payments_db.append({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "amount": 1000.00,
        "payment_date": today,
        "notes": "",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.paid_amount == 1000.00
    assert current_month_due.pending_amount == 0.0
    assert current_month_due.is_paid_in_full == True

    payments_db.clear()
    # One payment slightly over (e.g., due to bank charges, small error)
    payments_db.append({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "amount": 1000.001,
        "payment_date": today,
        "notes": "",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.paid_amount == 1000.001
    assert current_month_due.pending_amount == 0.0 # Should still be 0 pending because it's over/paid in full
    assert current_month_due.is_paid_in_full == True

    # Scenario 7: Payments for previous months or future months should not affect current month
    # Clear payments, add payment for a past month
    payments_db.clear()
    past_month = date(today.year -1, today.month, 1)
    payments_db.append({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "amount": 1000.00,
        "payment_date": past_month,
        "notes": "",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.paid_amount == 0.0 # Past payment doesn't count for current month
    assert current_month_due.pending_amount == 1000.00

    # Add payment for a future month
    future_month = date(today.year + 1, today.month, 1)
    payments_db.append({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "amount": 1000.00,
        "payment_date": future_month,
        "notes": "",
        "recorded_at": datetime.now()
    })
    monthly_dues = calculate_monthly_dues_for_tenant(tenant_obj, end_date=today)
    current_month_due = next(m for m in monthly_dues if m.month == current_month_str)
    assert current_month_due.paid_amount == 0.0 # Future payment doesn't count for current month
    assert current_month_due.pending_amount == 1000.00

