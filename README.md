# Asset and Rent Management System

This is a full-stack application for managing tenants and their rent payments, built with FastAPI for the backend and React (Vite) for the frontend.

## Features

- Tenant Management: Add new tenants with their details and monthly rent.
- Rent Payment Tracking: Record payments for tenants.
- Dashboard Summary: View total expected rent, total collected, and pending dues.
- Tenant Payment History: View detailed payment history for each tenant, including monthly due status.

## Project Structure

- `backend/`: Contains the FastAPI application.
- `frontend/`: Contains the React (Vite) application.

## Getting Started

Follow these steps to set up and run the application locally.

### 1. Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the FastAPI application:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend will be running at `http://127.0.0.1:8000`.
    You can access the API documentation at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    # or yarn install
    ```

3.  **Run the React development server:**
    ```bash
    npm run dev
    # or yarn dev
    ```
    The frontend will typically be running at `http://localhost:5173` (or another port as indicated by Vite).

### 3. Usage

- Open your browser to the frontend URL (e.g., `http://localhost:5173`).
- Use the dashboard to see summaries, add new tenants, record payments, and view tenant history.