from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import uuid

app = FastAPI(
    title="Asset/Rent Management System API",
    description="API for managing tenants and rent payments."
)

# CORS middleware to allow frontend to communicate with backend
origins = [
    "http://localhost:5173", # React app default port
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# In-memory database (for simplicity)
tenants_db: List[Dict] = []
payments_db: List[Dict] = []

# --- Pydantic Models ---

class TenantBase(BaseModel):
    name: str = Field(..., example="Alice Smith")
    monthly_rent: float = Field(..., gt=0, example=1200.00)
    contact_email: Optional[str] = Field(None, example="alice@example.com")
    move_in_date: date = Field(..., example="2023-01-15")

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.now)

class PaymentBase(BaseModel):
    tenant_id: str
    amount: float = Field(..., gt=0, example=1200.00)
    payment_date: date = Field(default_factory=date.today, example="2024-06-01")
    notes: Optional[str] = Field(None, example="June rent")

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: str
    recorded_at: datetime = Field(default_factory=datetime.now)

class DashboardSummary(BaseModel):
    total_expected_rent_current_month: float
    total_collected_current_month: float
    total_pending_current_month: float
    total_tenants: int

class TenantPaymentRecord(BaseModel):
    payment_id: str
    amount: float
    payment_date: date
    notes: Optional[str]

class MonthlyDueStatus(BaseModel):
    month: str # YYYY-MM
    expected_rent: float
    paid_amount: float
    pending_amount: float
    is_paid_in_full: bool

class TenantHistory(BaseModel):
    tenant: Tenant
    payments: List[TenantPaymentRecord]
    monthly_due_status: List[MonthlyDueStatus]

# --- Helper Functions ---

def get_tenant_by_id(tenant_id: str):
    for tenant_data in tenants_db:
        if tenant_data['id'] == tenant_id:
            return Tenant(**tenant_data)
    return None

def calculate_monthly_dues_for_tenant(tenant: Tenant, end_date: date = None) -> List[MonthlyDueStatus]:
    history = []
    if not end_date:
        end_date = date.today()

    current_date = tenant.move_in_date if tenant.move_in_date > date(tenant.move_in_date.year, tenant.move_in_date.month, 1) else date(tenant.move_in_date.year, tenant.move_in_date.month, 1)

    while current_date <= end_date:
        month_str = current_date.strftime('%Y-%m')
        expected_rent_for_month = tenant.monthly_rent

        # Filter payments for the current month
        # Payments are considered for a month if their payment_date falls within that month
        # or if they are made for the previous month's dues in the current month's beginning.
        # For simplicity, we consider payments made in the *calendar month*.
        month_payments = [
            p for p in payments_db
            if p['tenant_id'] == tenant.id and 
               p['payment_date'].year == current_date.year and 
               p['payment_date'].month == current_date.month
        ]
        paid_amount_for_month = sum(p['amount'] for p in month_payments)

        pending = expected_rent_for_month - paid_amount_for_month
        is_paid_in_full = pending <= 0.01 # Account for floating point inaccuracies

        history.append(MonthlyDueStatus(
            month=month_str,
            expected_rent=expected_rent_for_month,
            paid_amount=paid_amount_for_month,
            pending_amount=max(0.0, pending),
            is_paid_in_full=is_paid_in_full
        ))
        
        # Move to the next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
            
    return history


# --- API Endpoints ---

@app.post("/tenants", response_model=Tenant, status_code=201)
async def create_tenant(tenant: TenantCreate):
    tenant_id = str(uuid.uuid4())
    new_tenant = Tenant(id=tenant_id, **tenant.model_dump())
    tenants_db.append(new_tenant.model_dump())
    return new_tenant

@app.get("/tenants", response_model=List[Tenant])
async def get_all_tenants():
    return [Tenant(**t) for t in tenants_db]


@app.post("/payments", response_model=Payment, status_code=201)
async def record_payment(payment: PaymentCreate):
    tenant = get_tenant_by_id(payment.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    payment_id = str(uuid.uuid4())
    new_payment = Payment(id=payment_id, **payment.model_dump())
    payments_db.append(new_payment.model_dump())
    return new_payment

@app.get("/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    today = date.today()
    current_month_start = date(today.year, today.month, 1)

    total_expected_rent_current_month = 0.0
    total_collected_current_month = 0.0
    total_pending_current_month = 0.0

    for tenant_data in tenants_db:
        tenant = Tenant(**tenant_data)
        
        # Only count tenants who have moved in by or before the current month
        if tenant.move_in_date > today: # If move-in is in future, don't count for current month's rent
            continue

        total_expected_rent_current_month += tenant.monthly_rent
        
        # Payments made in the current calendar month for this tenant
        payments_this_month = [
            p for p in payments_db
            if p['tenant_id'] == tenant.id and 
               p['payment_date'].year == today.year and 
               p['payment_date'].month == today.month
        ]
        collected_from_tenant_this_month = sum(p['amount'] for p in payments_this_month)
        total_collected_current_month += collected_from_tenant_this_month
        
        # Calculate pending for current month for this specific tenant
        pending_from_tenant = tenant.monthly_rent - collected_from_tenant_this_month
        total_pending_current_month += max(0.0, pending_from_tenant)

    return DashboardSummary(
        total_expected_rent_current_month=total_expected_rent_current_month,
        total_collected_current_month=total_collected_current_month,
        total_pending_current_month=total_pending_current_month,
        total_tenants=len(tenants_db)
    )

@app.get("/tenant/{tenant_id}/history", response_model=TenantHistory)
async def get_tenant_history(tenant_id: str, month: Optional[str] = None):
    tenant = get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Filter payments for this tenant
    tenant_payments_raw = [
        p for p in payments_db
        if p['tenant_id'] == tenant_id
    ]
    
    # Sort payments by date descending
    tenant_payments_raw.sort(key=lambda p: p['payment_date'], reverse=True)

    payments = [
        TenantPaymentRecord(
            payment_id=p['id'],
            amount=p['amount'],
            payment_date=p['payment_date'],
            notes=p['notes']
        ) for p in tenant_payments_raw
    ]

    # Determine end date for history calculation
    end_date_for_history = date.today()
    if month:
        try:
            year, mon = map(int, month.split('-'))
            # Set end_date to the last day of the specified month
            last_day_of_month = (date(year, mon % 12 + 1, 1) - timedelta(days=1)) if mon < 12 else date(year, 12, 31)
            end_date_for_history = last_day_of_month
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.")

    monthly_due_status = calculate_monthly_dues_for_tenant(tenant, end_date=end_date_for_history)

    return TenantHistory(
        tenant=tenant,
        payments=payments,
        monthly_due_status=monthly_due_status
    )

@app.get("/")
async def root():
    return {"message": "Welcome to the Asset/Rent Management System API. Visit /docs for API documentation."}
