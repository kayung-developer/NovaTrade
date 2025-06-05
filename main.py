import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer  # We can reuse for header parsing
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
import random
import time
from datetime import datetime, timezone
import uuid

# Database (using a simplified in-memory structure for this example, you'd use SQLAlchemy with a real DB)
# Re-integrate your SQLAlchemy setup here. For brevity, I'll use dicts.
# from .database import engine, SessionLocal, Base (your actual db setup)
# from . import models, schemas, crud (your actual db modules)

# --- Firebase Admin Initialization ---
# IMPORTANT: Download your service account key JSON from Firebase Project Settings
# Store it securely and provide the path. For deployment, use environment variables or secret managers.
try:
    # !!! REPLACE "path/to/your-service-account-key.json" WITH THE ACTUAL PATH TO YOUR KEY FILE !!!
    cred = credentials.Certificate("novatrade.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except FileNotFoundError:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!!! Firebase Admin SDK service account key file not found.                 !!!")
    print("!!! Please download it from your Firebase project settings and update the  !!!")
    print("!!! path in main.py. The application may not work correctly.             !!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # Allow app to start but auth will fail
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # Handle this critical error appropriately, app might not function correctly
    # For local dev, ensure the file path is correct. For prod, ensure env var is set.

app = FastAPI(title="NovaTrade API")

# --- CORS ---
# IMPORTANT: Configure origins for your deployed frontend
origins = [
    "http://localhost",  # Allow local React dev server (if different port)
    "http://localhost:3000",  # Common React dev port
    "http://127.0.0.1",  # Standard localhost
    "null",  # Often for local file:// access if you open HTML directly
    # "https://your-firebase-hosting-domain.web.app", # Add your Firebase Hosting domain
    # "https://your-custom-domain.com", # Add your custom domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# --- Pydantic Models (Adjust based on your SQLAlchemy models) ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):  # Password no longer here
    firebase_uid: str


class User(UserBase):
    id: int  # Your local DB user ID
    firebase_uid: str
    is_active: bool = True
    balance_usd: float = 0.0

    class Config:
        orm_mode = True  # if using SQLAlchemy models, allows mapping from ORM objects


# --- In-memory data stores (Replace with your actual database logic) ---
# This is a simplified placeholder. You should use your SQLAlchemy setup for a real application.
fake_users_db: Dict[str, User] = {}  # Keyed by firebase_uid
next_user_id_counter = 1  # Use a global counter for unique local IDs

fake_portfolio_db: Dict[str, List[Dict[str, Any]]] = {}  # user_firebase_uid -> list of assets
fake_transactions_db: Dict[str, List[Dict[str, Any]]] = {}  # user_firebase_uid -> list of transactions

MOCK_ASSETS_PRICES = {  # Asset ID -> current price, 24h change, type
    "BTCUSD": {"price": 60000.00, "change_24h": 1.5, "type": "crypto"},
    "ETHUSD": {"price": 3000.00, "change_24h": -0.5, "type": "crypto"},
    "EURUSD": {"price": 1.0850, "change_24h": 0.1, "type": "forex"},
    "GBPUSD": {"price": 1.2600, "change_24h": -0.2, "type": "forex"},
    "TSLA": {"price": 170.00, "change_24h": 2.1, "type": "stock"},
}
# --- End In-memory ---


# --- Authentication Dependency ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # tokenUrl is nominal, Firebase handles token issuance


async def get_current_user_firebase_data(token: str = Depends(oauth2_scheme)) -> dict:
    """Verifies Firebase ID token and returns decoded token data."""
    if not firebase_admin._apps:  # Check if Firebase Admin is initialized
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Admin SDK not initialized. Check server configuration.",
        )
    try:
        decoded_token = firebase_admin.auth.verify_id_token(token)
        return decoded_token  # Contains 'uid', 'email', 'name', etc.
    except firebase_admin.auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID token has expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_admin.auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID token. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:  # Catch any other Firebase auth errors
        print(f"Firebase token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(firebase_data: dict = Depends(get_current_user_firebase_data)) -> User:
    """
    Gets user from local DB based on Firebase UID.
    Creates user in local DB if not exists. This simulates user profile creation/sync.
    """
    global next_user_id_counter  # Use the global counter

    firebase_uid = firebase_data.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firebase UID not found in token")

    user = fake_users_db.get(firebase_uid)
    if not user:
        # Create user in local DB (simulated)
        email = firebase_data.get("email")
        # Firebase 'name' comes from user.updateProfile({ displayName: ... }) on client
        full_name = firebase_data.get("name") or firebase_data.get("displayName")

        new_user_data = {
            "id": next_user_id_counter,  # Assign a new local ID
            "firebase_uid": firebase_uid,
            "email": email,
            "full_name": full_name,
            "is_active": True,
            "balance_usd": 10000.00  # Initial demo balance for new users
        }
        user = User(**new_user_data)
        fake_users_db[firebase_uid] = user
        fake_portfolio_db.setdefault(firebase_uid, [])  # Initialize portfolio
        fake_transactions_db.setdefault(firebase_uid, [])  # Initialize transactions

        next_user_id_counter += 1  # Increment for the next user
        print(f"New user created in local DB: {user.email} (UID: {firebase_uid}, LocalID: {user.id})")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


# --- User Endpoints ---
# POST /users/register is GONE (Registration handled by Firebase Client SDK)
# POST /token is GONE (Token issuance handled by Firebase)

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Fetches the current user's profile from the local database.
    The get_current_active_user dependency handles creation if the user
    authenticated via Firebase is new to this backend.
    """
    return current_user


# --- Market Data Endpoints ---
@app.get("/market/prices", response_model=List[Dict[str, Any]])
async def get_market_prices(current_user: User = Depends(get_current_active_user)):  # Protected endpoint
    live_prices = []
    for symbol, data in MOCK_ASSETS_PRICES.items():
        price_factor = 1 + (random.random() - 0.5) * 0.02  # +/- 1% fluctuation for dynamic feel
        change_factor = 1 + (random.random() - 0.5) * 0.1  # Fluctuate change %
        live_prices.append({
            "symbol": symbol,
            "price": round(data["price"] * price_factor, 4 if data["type"] == "forex" else 2),
            "change_24h": round(data["change_24h"] * change_factor, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return live_prices


# --- WebSocket for Market Data ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


async def market_data_publisher():
    """Periodically sends market updates to connected WebSocket clients."""
    while True:
        await asyncio.sleep(5)  # Update interval
        prices_update = []
        for symbol, data in MOCK_ASSETS_PRICES.items():
            price_factor = 1 + (random.random() - 0.5) * 0.02
            change_factor = 1 + (random.random() - 0.5) * 0.1
            prices_update.append({
                "symbol": symbol,
                "price": round(data["price"] * price_factor, 4 if data["type"] == "forex" else 2),
                "change_24h": round(data["change_24h"] * change_factor, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        if manager.active_connections:  # Only broadcast if there are active connections
            await manager.broadcast({"type": "market_update", "data": prices_update})


@app.on_event("startup")
async def startup_event():
    # Start background tasks if any, e.g., market data publisher
    asyncio.create_task(market_data_publisher())
    print("Market data publisher started.")


@app.websocket("/ws/market-data")
async def websocket_endpoint(websocket: WebSocket):
    # Authentication for WebSockets is tricky. Common methods:
    # 1. Token in query param: ws://.../?token=FIREBASE_ID_TOKEN (backend verifies on connect)
    # 2. Token as first message: Client sends token, backend verifies, then proceeds.
    # This example does not implement WebSocket authentication for simplicity.
    # For a production app, secure your WebSocket endpoint.
    await manager.connect(websocket)
    print(f"Client {websocket.client} connected to market data WebSocket.")
    # Send initial snapshot of market data
    initial_prices = []
    for symbol, data in MOCK_ASSETS_PRICES.items():
        initial_prices.append({
            "symbol": symbol,
            "price": round(data["price"], 4 if data["type"] == "forex" else 2),
            "change_24h": data["change_24h"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    await websocket.send_json({"type": "market_snapshot", "data": initial_prices})
    try:
        while True:
            # Keep connection alive, or handle client messages if any
            # For example, client could send {"type": "subscribe", "symbols": ["BTCUSD"]}
            data = await websocket.receive_text()  # Or receive_json
            # print(f"Received from {websocket.client}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {websocket.client} disconnected from market data WebSocket.")


# --- Portfolio Endpoint ---
class PortfolioItem(BaseModel):
    asset_id: str
    quantity: float
    average_buy_price: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None


@app.get("/portfolio", response_model=List[PortfolioItem])
async def get_portfolio(current_user: User = Depends(get_current_active_user)):
    user_portfolio_data = fake_portfolio_db.get(current_user.firebase_uid, [])
    enriched_portfolio: List[PortfolioItem] = []

    # Get current market prices once for efficiency
    current_market_prices_list = []
    for symbol, data in MOCK_ASSETS_PRICES.items():  # Using MOCK_ASSETS for sim, replace with live feed
        current_market_prices_list.append(
            {"symbol": symbol, "price": data["price"]})  # Base price for calculation consistency
    current_prices_map = {p["symbol"]: p["price"] for p in current_market_prices_list}

    for item_data in user_portfolio_data:
        asset_id = item_data["asset_id"]
        quantity = item_data["quantity"]
        avg_buy_price = item_data["average_buy_price"]

        current_price = current_prices_map.get(asset_id, avg_buy_price)  # Fallback to avg_buy_price if not in market
        current_value = quantity * current_price
        unrealized_pnl = (current_price - avg_buy_price) * quantity

        cost_basis = avg_buy_price * quantity
        unrealized_pnl_percent = (unrealized_pnl / cost_basis) * 100 if cost_basis != 0 else 0.0

        enriched_portfolio.append(PortfolioItem(
            asset_id=asset_id,
            quantity=quantity,
            average_buy_price=avg_buy_price,
            current_price=current_price,
            current_value=current_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent
        ))
    return enriched_portfolio


# --- Trade Execution Endpoint ---
class TradeRequest(BaseModel):
    asset_id: str
    trade_type: str  # "BUY" or "SELL"
    quantity: float
    price_limit: Optional[float] = None


class TradeResponse(BaseModel):
    message: str
    transaction: Dict[str, Any]


@app.post("/trade/execute", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest, current_user: User = Depends(get_current_active_user)):
    asset_info = MOCK_ASSETS_PRICES.get(trade.asset_id)
    if not asset_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    current_market_price = asset_info["price"]  # Use the base mock price for execution

    # Determine execution price (simplified: market order or exact limit)
    execution_price = current_market_price
    if trade.price_limit is not None:
        if trade.trade_type == "BUY":
            if trade.price_limit < current_market_price:
                # For a real limit order, this would be queued or potentially partially filled.
                # For this simulation, we'll assume it means "buy at this price or better".
                # If the limit is too low, it might not execute in a real scenario.
                # Here, we just use the limit if it's advantageous or equal.
                pass  # execution_price = min(trade.price_limit, current_market_price) - but for simulation just use limit
            execution_price = trade.price_limit  # Assume limit is met for BUY
        elif trade.trade_type == "SELL":
            if trade.price_limit > current_market_price:
                # Similar logic for sell.
                pass
            execution_price = trade.price_limit  # Assume limit is met for SELL
        # A more realistic simulation for limit orders not being met:
        # if (trade.trade_type == "BUY" and trade.price_limit < current_market_price) or \
        #    (trade.trade_type == "SELL" and trade.price_limit > current_market_price):
        #     raise HTTPException(status_code=400, detail=f"Limit order price not met. Market: {current_market_price}, Limit: {trade.price_limit}")

    total_cost_or_proceeds = trade.quantity * execution_price
    user_portfolio = fake_portfolio_db.setdefault(current_user.firebase_uid, [])
    user_transactions = fake_transactions_db.setdefault(current_user.firebase_uid, [])

    if trade.trade_type.upper() == "BUY":
        if current_user.balance_usd < total_cost_or_proceeds:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
        current_user.balance_usd -= total_cost_or_proceeds

        existing_asset_item = next((item for item in user_portfolio if item["asset_id"] == trade.asset_id), None)
        if existing_asset_item:
            new_total_quantity = existing_asset_item["quantity"] + trade.quantity
            # Calculate new average buy price: (old_total_cost + new_trade_cost) / new_total_quantity
            new_avg_price = ((existing_asset_item["average_buy_price"] * existing_asset_item["quantity"]) +
                             (execution_price * trade.quantity)) / new_total_quantity
            existing_asset_item["quantity"] = new_total_quantity
            existing_asset_item["average_buy_price"] = new_avg_price
        else:
            user_portfolio.append({
                "asset_id": trade.asset_id,
                "quantity": trade.quantity,
                "average_buy_price": execution_price
            })
    elif trade.trade_type.upper() == "SELL":
        existing_asset_item = next((item for item in user_portfolio if item["asset_id"] == trade.asset_id), None)
        if not existing_asset_item or existing_asset_item["quantity"] < trade.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough assets to sell")

        existing_asset_item["quantity"] -= trade.quantity
        current_user.balance_usd += total_cost_or_proceeds
        if existing_asset_item["quantity"] == 0:  # Remove asset from portfolio if quantity is zero
            user_portfolio.remove(existing_asset_item)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trade type. Must be BUY or SELL.")

    # Record transaction
    transaction_record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": trade.trade_type.upper(),
        "asset_id": trade.asset_id,
        "quantity": trade.quantity,
        "price_per_unit": execution_price,
        "total_amount": total_cost_or_proceeds,
        "status": "COMPLETED"  # Simplified status
    }
    user_transactions.insert(0, transaction_record)  # Add to beginning of list
    fake_users_db[current_user.firebase_uid] = current_user  # Persist balance change (in memory)

    asset_type = asset_info.get('type', 'stock')  # Default to stock if type not defined
    price_format_decimals = 4 if asset_type == 'forex' else 2

    return TradeResponse(
        message=(
            f"Trade {trade.trade_type.upper()} {trade.quantity} {trade.asset_id} "
            f"@ ${execution_price:.{price_format_decimals}f} executed successfully."
        ),
        transaction=transaction_record
    )


# --- Transactions Endpoint ---
@app.get("/transactions", response_model=List[Dict[str, Any]])
async def get_transactions(limit: int = 50, current_user: User = Depends(get_current_active_user)):
    user_transactions = fake_transactions_db.get(current_user.firebase_uid, [])
    return user_transactions[:limit]  # Return most recent transactions up to limit


# --- Payment Endpoints (Simulated) ---
class PaymentIntentCreate(BaseModel):
    amount: float
    currency: str = "USD"  # Default currency


class PaymentIntentResponse(PaymentIntentCreate):
    id: str
    status: str  # e.g., "requires_confirmation", "succeeded", "failed"


# In-memory store for payment intents (replace with DB in production)
payment_intents_db: Dict[str, PaymentIntentResponse] = {}


@app.post("/payments/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(intent_data: PaymentIntentCreate,
                                current_user: User = Depends(get_current_active_user)):
    if intent_data.amount < 1.00:  # Minimum deposit amount
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum deposit amount is $1.00")

    intent_id = f"pi_{uuid.uuid4().hex[:24]}"  # Generate a unique payment intent ID

    payment_intent = PaymentIntentResponse(
        id=intent_id,
        amount=intent_data.amount,
        currency=intent_data.currency.upper(),  # Store currency in uppercase
        status="requires_confirmation"
    )
    payment_intents_db[intent_id] = payment_intent  # Store in our "DB"
    return payment_intent


@app.post("/payments/confirm/{intent_id}", response_model=TradeResponse)  # Reusing TradeResponse for message + tx
async def confirm_payment_intent(intent_id: str, current_user: User = Depends(get_current_active_user)):
    intent = payment_intents_db.get(intent_id)
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment intent not found")
    if intent.status != "requires_confirmation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment intent cannot be confirmed. Current status: {intent.status}"
        )

    # Simulate successful payment confirmation
    intent.status = "succeeded"
    current_user.balance_usd += intent.amount
    fake_users_db[current_user.firebase_uid] = current_user  # Persist balance change

    # Record deposit transaction
    user_transactions = fake_transactions_db.setdefault(current_user.firebase_uid, [])
    deposit_transaction = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "DEPOSIT",
        "asset_id": intent.currency,  # For deposits, asset is the currency
        "quantity": intent.amount,
        "price_per_unit": 1.0,  # Price per unit is 1 for fiat deposits
        "total_amount": intent.amount,
        "status": "COMPLETED"
    }
    user_transactions.insert(0, deposit_transaction)

    return TradeResponse(  # Reusing TradeResponse structure for consistency
        message=f"Payment of {intent.currency} {intent.amount:.2f} confirmed successfully.",
        transaction=deposit_transaction
    )


# --- Main execution (if running directly using `python main.py`) ---
if __name__ == "__main__":
    # This block is for direct execution. `uvicorn main:app --reload` is preferred for development.
    # Ensure you have your actual SQLAlchemy models and database setup for a real app:
    # For example:
    # from .database import engine, Base
    # Base.metadata.create_all(bind=engine)
    print("Starting NovaTrade API server with Firebase Auth integration...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
