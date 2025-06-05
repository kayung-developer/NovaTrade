# NovaTrade - Advanced Crypto & Forex Trading Platform (Frontend + Backend)

NovaTrade is a simulated cryptocurrency and forex trading platform built with a modern web stack. It features a React-based frontend that communicates with a FastAPI (Python) backend. User authentication is handled by Firebase.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
  - [I. Firebase Setup](#i-firebase-setup)
  - [II. Backend Setup (FastAPI)](#ii-backend-setup-fastapi)
  - [III. Frontend Setup (HTML/React)](#iii-frontend-setup-htmlreact)
- [Running the Application](#running-the-application)
- [Key Application Flow](#key-application-flow)
  - [Authentication](#authentication)
  - [Data Fetching](#data-fetching)
- [API Endpoints (Backend)](#api-endpoints-backend)
- [Client-Side Database (sql.js)](#client-side-database-sqljs)
- [Deployment Notes](#deployment-notes)
  - [Frontend (Firebase Hosting Example)](#frontend-firebase-hosting-example)
  - [Backend (Cloud Run Example)](#backend-cloud-run-example)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)

## Features

*   **User Authentication:** Secure registration and login using Firebase Authentication (Email/Password).
*   **Dashboard:** Overview of market data (crypto, forex, stocks - simulated) and portfolio summary.
*   **Real-time Market Data:** Simulated real-time price updates via WebSockets for listed assets.
*   **Trading:** Interface to place BUY/SELL market and (simulated) limit orders.
*   **Portfolio Management:** View current asset holdings, average buy prices, current values, and unrealized P&L.
*   **Transaction History:** List of all trades and deposits.
*   **Fund Deposits:** Simulated fund deposit system.
*   **Responsive UI:** Designed to work on various screen sizes.
*   **Client-Side Preferences:** Example of using `sql.js` for storing user preferences (like theme) in the browser.
*   **Interactive Charts:** Price history charts for assets using Chart.js.

## Tech Stack

**Frontend:**

*   HTML5
*   CSS3 (with CSS Variables for theming)
*   JavaScript (ES6+)
*   React 18 (using UMD builds via CDN for simplicity)
*   Babel (standalone for in-browser JSX transpilation)
*   Chart.js (for data visualization)
*   Firebase SDK (for client-side authentication)
*   `sql.js` (for client-side SQLite database)
*   `uuid` (for generating unique IDs client-side if needed)

**Backend:**

*   Python 3.9+
*   FastAPI (high-performance web framework)
*   Uvicorn (ASGI server)
*   Pydantic (for data validation)
*   Firebase Admin SDK (for backend authentication token verification and user management)
*   WebSockets (for real-time communication)
    *   *(Note: The current backend uses in-memory Python dictionaries for data storage. For a production application, this should be replaced with a persistent database like PostgreSQL or MySQL, ideally with an ORM like SQLAlchemy.)*

**Authentication:**

*   Firebase Authentication

## Project Structure

The application is currently contained within a single `index.html` file for ease of demonstration. This file includes:

1.  **HTML Structure:** Basic layout and the root div for React.
2.  **CSS Styles:** All styling for the application.
3.  **JavaScript (React Code within `<script type="text/babel">`):**
    *   Firebase client initialization.
    *   React components for UI (Layout, Pages, Helpers).
    *   Authentication context (`AuthProvider`).
    *   API service for backend communication.
    *   Client-side database (`sql.js`) helpers.
4.  **Commented Backend Code:** The FastAPI Python code is included in a large comment block at the end of the HTML file with instructions on how to run it separately.

## Prerequisites

*   **Node.js and npm/yarn:** (Optional, only if you decide to move to a bundled React setup). For the current setup, only a browser is needed for the frontend.
*   **Python 3.9+ and pip:** For running the FastAPI backend.
*   **A Firebase Project:** You'll need to create a project on the [Firebase Console](https://console.firebase.google.com/).
*   **Web Browser:** Chrome, Firefox, Edge, etc.

## Setup and Installation

### I. Firebase Setup

1.  **Create a Firebase Project:**
    *   Go to the [Firebase Console](https://console.firebase.google.com/).
    *   Click "Add project" and follow the setup steps.
2.  **Enable Email/Password Authentication:**
    *   In your Firebase project, go to "Authentication" (under Build).
    *   Select the "Sign-in method" tab.
    *   Enable "Email/Password" and save.
3.  **Get Web App Configuration:**
    *   In Project Overview, click the gear icon (Project settings).
    *   Under the "General" tab, scroll to "Your apps".
    *   If no web app (`</>`) exists, click "Add app", choose Web, give it a nickname (e.g., "NovaTrade Web"), and register.
    *   Copy the `firebaseConfig` object. You'll need this for the frontend.
4.  **Generate Firebase Admin SDK Service Account Key (for Backend):**
    *   In Project settings, go to the "Service accounts" tab.
    *   Click "Generate new private key" and confirm. A JSON file will be downloaded.
    *   **Store this JSON file securely.** You'll need its path for the backend. **Do not commit this file to public repositories.**

### II. Backend Setup (FastAPI)

1.  **Create Backend Directory:** Create a new folder for your backend (e.g., `novatrade-backend`).
2.  **Save `main.py`:**
    *   Copy the Python code block (marked `<!-- BEGIN PYTHON CODE ... END PYTHON CODE -->`) from the bottom of the `index.html` file.
    *   Save this code as `main.py` inside your backend directory.
3.  **Set up Virtual Environment (Recommended):**
    ```bash
    cd novatrade-backend
    python -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```
4.  **Install Dependencies:**
    ```bash
    pip install fastapi "uvicorn[standard]" pydantic firebase-admin websockets
    ```
    *(Add other database drivers like `psycopg2-binary` or `aiosqlite` if you integrate a persistent database.)*
5.  **Configure Firebase Admin SDK Path:**
    *   Open `main.py`.
    *   Locate the line: `cred = credentials.Certificate("path/to/your-service-account-key.json")`
    *   **Replace `"path/to/your-service-account-key.json"` with the actual path to the service account JSON file you downloaded in Firebase Setup (Step I.4).**

### III. Frontend Setup (HTML/React)

1.  **Save `index.html`:**
    *   Save the entire HTML content (including CSS and the React JavaScript) as `index.html` in a convenient location.
2.  **Configure Firebase Client SDK:**
    *   Open `index.html`.
    *   Find the `firebaseConfig` object within the `<script type="text/babel">` section:
        ```javascript
        const firebaseConfig = {
            apiKey: "YOUR_API_KEY",
            authDomain: "YOUR_AUTH_DOMAIN",
            // ... other keys ...
        };
        ```
    *   **Replace the placeholder values with the actual `firebaseConfig` values you copied from your Firebase project (Setup Step I.3).**
3.  **Configure Backend URL (if deploying):**
    *   If you plan to deploy the backend to a different URL than `http://localhost:8000`, update the `DEPLOYED_API_BASE_URL` constant in the JavaScript:
        ```javascript
        const DEPLOYED_API_BASE_URL = 'YOUR_DEPLOYED_FASTAPI_BACKEND_URL_HERE';
        ```

## Running the Application

1.  **Start the Backend Server:**
    *   Open a terminal in your `novatrade-backend` directory (with the virtual environment activated).
    *   Run:
        ```bash
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ```
    *   You should see output indicating the server is running, e.g., `Uvicorn running on http://0.0.0.0:8000`.
    *   Check for any errors, especially regarding Firebase Admin SDK initialization (service account key path).
2.  **Open the Frontend:**
    *   Open the `index.html` file directly in your web browser (e.g., by double-clicking it or using `File > Open`).
    *   The application should load. Open your browser's Developer Tools (usually F12) to check the Console for any errors and the Network tab to monitor API calls.

You should now be able to register an account, log in, and interact with the NovaTrade platform.

## Key Application Flow

### Authentication

1.  **User Registration/Login (Frontend):**
    *   The `AuthPage` component uses `firebase.auth().createUserWithEmailAndPassword()` or `firebase.auth().signInWithEmailAndPassword()`.
    *   Firebase handles the direct authentication.
2.  **State Change (Frontend):**
    *   `firebase.auth().onAuthStateChanged()` in `AuthProvider` detects the new Firebase user.
    *   It retrieves the Firebase ID Token using `user.getIdToken(true)`.
3.  **Backend Sync/Fetch (Frontend to Backend):**
    *   `AuthProvider` makes a `GET` request to the backend's `/users/me` endpoint, sending the Firebase ID Token in the `Authorization: Bearer <token>` header.
4.  **Token Verification (Backend):**
    *   The `get_current_user_firebase_data` dependency in FastAPI verifies the ID token using `firebase_admin.auth.verify_id_token()`.
5.  **User Profile Management (Backend):**
    *   The `get_current_active_user` dependency checks if a user with the Firebase UID exists in the backend's local database (currently `fake_users_db`).
    *   If the user doesn't exist, a new user profile is created in the local DB.
    *   The backend returns the user's profile data.
6.  **State Update (Frontend):**
    *   `AuthProvider` updates its `dbUser` state with the profile from the backend.
    *   `isAuthenticated` (which depends on `idToken` and `dbUser`) becomes `true`.
    *   `AppRouter` renders the main application pages.

### Data Fetching

*   Protected API endpoints on the backend require a valid Firebase ID Token.
*   Frontend components (e.g., `DashboardPage`, `PortfolioPage`) use `useAuth()` to get the `idToken`.
*   This token is passed to `apiService.call()` for requests to protected backend routes.
*   The backend verifies the token for each request to these routes.

## API Endpoints (Backend)

(Refer to `main.py` for detailed request/response models)

*   `GET /users/me`: Get current authenticated user's profile (creates if not exists).
*   `GET /market/prices`: Get simulated market prices for assets.
*   `GET /portfolio`: Get the current user's asset portfolio.
*   `POST /trade/execute`: Execute a BUY or SELL trade.
*   `GET /transactions`: Get the current user's transaction history.
*   `POST /payments/create-intent`: Create a (simulated) payment intent for deposit.
*   `POST /payments/confirm/{intent_id}`: Confirm a (simulated) payment.
*   `WEBSOCKET /ws/market-data`: WebSocket endpoint for broadcasting simulated market data updates.

## Client-Side Database (sql.js)

*   The application includes a simple example of using `sql.js` to create an in-browser SQLite database.
*   Currently, it's used to store a `theme` preference (though the theme switching UI is not implemented).
*   Functions `initSqlJs`, `getPreference`, `setPreference` in the JavaScript handle this.
*   Data stored this way is persistent in the user's browser for that specific domain until cleared.

## Deployment Notes

### Frontend (Firebase Hosting Example)

1.  **Install Firebase CLI:** `npm install -g firebase-tools` or `yarn global add firebase-tools`.
2.  **Login:** `firebase login`.
3.  **Initialize Hosting:** In the directory containing `index.html`, run `firebase init hosting`.
    *   Select your Firebase project.
    *   Public directory: `.` (if `index.html` is in the root).
    *   Configure as SPA: `No` (for this simple setup).
4.  **Update `DEPLOYED_API_BASE_URL`:** In `index.html`, set this constant to your deployed backend URL.
5.  **Deploy:** `firebase deploy --only hosting`.

### Backend (Cloud Run Example)

1.  **Create `Dockerfile` and `requirements.txt`** (see previous detailed response for examples).
2.  **Build and Push Docker Image** to Google Container Registry or Artifact Registry.
3.  **Deploy to Cloud Run:**
    *   Configure service name, region, authentication (Allow unauthenticated).
    *   Set container port (e.g., `8080`).
    *   **Crucially, manage the Firebase Admin service account key securely (e.g., via Secret Manager or by granting the Cloud Run service account IAM permissions for Firebase). Avoid baking the key into the image for production.**
    *   The Cloud Run service URL will be your `DEPLOYED_API_BASE_URL` for the frontend.

## Troubleshooting Common Issues

*   **`auth/api-key-not-valid` (Frontend):** Your `firebaseConfig` in `index.html` is incorrect. Copy it carefully from your Firebase project settings.
*   **Login Redirect Loop (Frontend):**
    *   Check browser console for errors from `AuthProvider` or API calls to `/users/me`.
    *   Verify the backend is running and accessible.
    *   Ensure the backend's `/users/me` can correctly verify the token and return/create a user profile. Check backend logs.
    *   Make sure the Firebase Admin SDK service account key path is correct in `main.py` and the file is readable.
*   **CORS Errors (Frontend Network Tab):**
    *   Ensure the `origins` list in `main.py` (FastAPI CORS middleware) includes the origin your frontend is being served from (e.g., `http://localhost:xxxx` if using a dev server, or your Firebase Hosting URL).
*   **401 Unauthorized from Backend API Calls:**
    *   Token expired: The frontend should handle token refresh via `getIdToken(true)`.
    *   Invalid token: Could be an issue with Firebase Admin SDK setup on the backend (service account key).
    *   Token not being sent: Ensure `apiService.call` correctly includes the token in headers.
*   **Backend Firebase Admin SDK Initialization Error:**
    *   "File not found": The path to your service account key JSON in `main.py` is wrong.
    *   Other errors: Could be permissions issues or an invalid key file.

## Future Enhancements

*   **Persistent Backend Database:** Replace in-memory Python dictionaries with a robust database (PostgreSQL, MySQL) using SQLAlchemy or another ORM.
*   **Real Market Data Integration:** Connect to actual crypto/forex/stock market data APIs (e.g., CoinGecko, Alpha Vantage, IEX Cloud, a broker's API).
*   **Advanced Order Types:** Implement real limit orders, stop-loss, take-profit, etc.
*   **Live Charting:** Integrate more sophisticated charting libraries (e.g., TradingView Lightweight Charts) with live data.
*   **User Profile Management:** Allow users to update their profile information.
*   **Two-Factor Authentication (2FA).**
*   **Admin Panel:** For managing users and platform settings.
*   **Improved UI/UX:** More polished design, better error handling, loading states.
*   **State Management:** For a larger React app, consider Redux, Zustand, or Recoil.
*   **Testing:** Implement unit and integration tests for both frontend and backend.
*   **Build System for Frontend:** Migrate from CDN/standalone Babel to a build system like Vite or Create React App for better optimization, module management, and development experience.
*   **Secure WebSocket Authentication.**
*   **Proper Error Handling and Logging:** Implement more comprehensive error reporting.

## Contributing

Contributions are welcome! If you'd like to contribute:

1.  Fork the repository (if this were on GitHub/GitLab).
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Test thoroughly.
5.  Submit a pull request with a clear description of your changes.
