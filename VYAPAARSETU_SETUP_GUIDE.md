# 🚀 VyapaarSetu AI - Complete Setup Guide

Complete setup guide for the VyapaarSetu AI system with Dashboard and Android App integration.

---

## 📋 System Overview

VyapaarSetu AI is a complete order confirmation system that includes:

1. **Extended Flask Backend** - Order management, risk assessment, blockchain consent
2. **React Dashboard** - Real-time merchant operations interface
3. **Android App** - Field agent mobile application (Kotlin code provided)
4. **Voice AI System** - Existing Twilio + Sarvam AI + Ollama integration

---

## 🔧 Backend Setup

### 1. Install New Dependencies

```bash
cd voice-bot
pip install -r requirements.txt
```

New dependencies added:
- `flask-cors` - Cross-origin requests for dashboard
- `flask-socketio` - Real-time updates
- `flask-sqlalchemy` - Database ORM
- `eventlet` - Socket.IO server
- `PyJWT` - Android app authentication
- `reportlab` - Invoice generation

### 2. Update Environment Variables

Your `.env` file now includes:

```env
# VyapaarSetu API Configuration
API_KEY=vyapaarsetu_api_key_2024
AGENT_USERNAME=agent
AGENT_PASSWORD=agent123
JWT_SECRET=vyapaarsetu_jwt_secret_key_2024
```

### 3. Start the Extended Backend

```bash
python app.py
```

The system will:
- Create SQLite database (`vyapaarsetu.db`)
- Register new API routes
- Start Socket.IO server for real-time updates
- Run on `http://localhost:5000`

### 4. Test the Backend

```bash
python test_extended_system.py
```

This will test:
- ✅ Database creation
- ✅ Order creation and management
- ✅ API endpoints
- ✅ Authentication
- ✅ Risk assessment
- ✅ Audit logging

---

## 🖥️ Dashboard Setup

### 1. Install Dashboard Dependencies

```bash
cd vyapaarsetu-dashboard
npm install
```

### 2. Start the Dashboard

```bash
npm run dev
```

Dashboard will run on `http://localhost:3000`

### 3. Login to Dashboard

Use these credentials:
- **Username**: `agent`
- **Password**: `agent123`

### 4. Dashboard Features

**Main Dashboard**:
- 📊 Real-time stats (6 cards)
- 📞 Active calls monitoring
- ⏳ Approval queue (highest priority)
- 🚨 Risk alerts panel
- 📋 Live activity feed

**Orders Page**:
- 📋 Complete order table
- 🔍 Status filtering
- 📞 Call initiation buttons
- 👁️ Order details

**Approvals Page**:
- ✅ Pending approvals
- 🔘 One-click approve/reject
- 📊 Risk assessment display

---

## 📱 Android App Integration

### 1. Android Project Structure

```
VyapaarSetuAITester/
├── app/
│   ├── src/main/java/com/vyapaarsetu/aitester/
│   │   ├── data/
│   │   │   ├── model/          # Order, Customer, CallSession
│   │   │   ├── remote/         # ApiService, SocketManager
│   │   │   └── repository/     # Data repositories
│   │   ├── ui/
│   │   │   ├── screens/        # Compose screens
│   │   │   ├── components/     # Reusable components
│   │   │   └── viewmodel/      # ViewModels
│   │   └── service/            # Background services
│   └── build.gradle.kts
└── gradle/
```

### 2. Key Android Features

**Authentication**:
```kotlin
// Login endpoint
POST /api/v1/auth/login
Body: { "username": "agent", "password": "agent123" }
Response: { "token": "jwt_token_here" }
```

**Order Management**:
```kotlin
// Get orders for mobile
GET /api/v1/mobile/orders
Header: Authorization: Bearer <token>

// Initiate call from mobile
POST /api/v1/mobile/orders/{orderId}/call
Header: Authorization: Bearer <token>
```

**Real-time Updates**:
```kotlin
// Socket.IO events
- order_update: Order status changed
- approval_needed: Order needs human approval
- risk_alert: High-risk order detected
- escalation_needed: Call escalated to human
```

### 3. Android App Screens

1. **LoginScreen** - JWT authentication
2. **HomeScreen** - Dashboard with stats
3. **OrderListScreen** - Mobile-optimized order list
4. **ActiveCallScreen** - Real-time call monitoring
5. **ApprovalScreen** - Quick approve/reject interface

---

## 🔄 Complete Order Flow

### 1. Order Creation

**Dashboard/Android** → **POST /api/v1/orders**:
```json
{
  "phone_number": "+919876543210",
  "customer_name": "Rajesh Kumar",
  "amount": 1500.0,
  "items": ["Samosa", "Chai", "Pakora"],
  "delivery_address": "123 MG Road, Mumbai",
  "language": "hi"
}
```

### 2. Call Initiation

**Dashboard/Android** → **POST /api/v1/call/initiate**:
```json
{
  "order_id": "ORD12345678",
  "phone_number": "+919876543210"
}
```

### 3. Voice Call Flow

```
Customer Picks Up → /voice/order-confirm
   ↓
Identity Check: "Kya aap Rajesh Kumar ji hain?"
   ↓
Order Details: "Aapka ₹1500 ka order hai..."
   ↓
Confirmation: "Kya aap confirm karte hain?"
   ↓
Risk Assessment → Blockchain Hash → Approval Queue
```

### 4. Human Approval

**Dashboard** → **POST /api/v1/orders/{id}/approve**:
```json
{
  "action": "APPROVE",  // or "REJECT"
  "agent_name": "Dashboard User"
}
```

### 5. Real-time Updates

All changes emit Socket.IO events:
- `order_update` → Dashboard table updates
- `approval_needed` → Approval queue updates
- `risk_alert` → Risk panel updates

---

## 🧪 Testing the Complete System

### 1. Backend Test

```bash
python test_extended_system.py
```

Expected output:
```
🚀 VyapaarSetu AI Extended System Test
==================================================
🧪 Testing GET /health
   Status: 200
   ✅ SUCCESS

🧪 Testing GET /api/v1/dashboard/stats
   Status: 200
   ✅ SUCCESS

📦 Creating test order...
🧪 Testing POST /api/v1/orders
   Status: 201
   ✅ SUCCESS
   Created order: ORD12345678

📞 Testing call initiation...
🧪 Testing POST /api/v1/call/initiate
   Status: 500  (Expected - Twilio trial limitation)

✅ Testing approval workflow...
🧪 Testing POST /api/v1/orders/ORD12345678/approve
   Status: 200
   ✅ SUCCESS

📱 Testing Android login...
🧪 Testing POST /api/v1/auth/login
   Status: 200
   ✅ SUCCESS
   Got JWT token: eyJ0eXAiOiJKV1QiLCJh...

🎉 Extended system test completed!
```

### 2. Dashboard Test

1. Open `http://localhost:3000`
2. Login with `agent` / `agent123`
3. Check dashboard stats
4. Create a test order
5. Try to initiate a call
6. Check real-time updates

### 3. Android Test

1. Build the Android project
2. Install on device/emulator
3. Login with same credentials
4. Check order synchronization
5. Test real-time notifications

---

## 📊 Database Schema

### Tables Created

```sql
-- Customer information
CREATE TABLE customer (
    id INTEGER PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    language_preference VARCHAR(10),
    cancellation_count INTEGER DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    created_at DATETIME
);

-- Order tracking
CREATE TABLE order (
    id INTEGER PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE,
    customer_id INTEGER REFERENCES customer(id),
    items TEXT,  -- JSON
    amount FLOAT,
    delivery_address TEXT,
    status VARCHAR(30),  -- PENDING, CALLING, AWAITING_APPROVAL, etc.
    risk_level VARCHAR(20),  -- SAFE, MEDIUM, SUSPICIOUS
    blockchain_hash VARCHAR(64),
    call_sid VARCHAR(50),
    created_at DATETIME,
    updated_at DATETIME
);

-- Call session tracking
CREATE TABLE call_session (
    id INTEGER PRIMARY KEY,
    call_sid VARCHAR(50) UNIQUE,
    order_id VARCHAR(50),
    customer_phone VARCHAR(20),
    detected_language VARCHAR(10),
    intent_result VARCHAR(20),  -- YES, NO, UNKNOWN
    full_transcript TEXT,  -- JSON
    started_at DATETIME,
    ended_at DATETIME
);

-- Audit trail
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    event_type VARCHAR(50),
    order_id VARCHAR(50),
    call_sid VARCHAR(50),
    actor VARCHAR(100),
    description TEXT,
    timestamp DATETIME
);
```

---

## 🔒 Security Features

### 1. API Authentication

**Dashboard**: API Key in headers
```
X-API-Key: vyapaarsetu_api_key_2024
```

**Android**: JWT tokens
```
Authorization: Bearer <jwt_token>
```

### 2. Twilio Webhook Validation

All Twilio webhooks validate request signatures.

### 3. Risk Assessment Engine

Multi-factor risk scoring:
- Cancellation history
- Order amount anomalies
- Address mismatches
- Rapid order frequency
- Previous flags

### 4. Blockchain Consent

SHA256 hash for order consent:
```
SHA256(order_id + customer_phone_hash + response + timestamp)
```

---

## 🚀 Production Deployment

### 1. Backend Deployment

```bash
# Use gunicorn for production
pip install gunicorn
gunicorn -w 4 -k eventlet -b 0.0.0.0:5000 app:app

# Or use Docker
docker build -t vyapaarsetu-backend .
docker run -p 5000:5000 vyapaarsetu-backend
```

### 2. Dashboard Deployment

```bash
# Build for production
npm run build

# Serve with nginx or deploy to Vercel/Netlify
```

### 3. Database Migration

For production, use PostgreSQL:
```python
# Update app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@host:5432/vyapaarsetu'
```

---

## 📈 Monitoring & Analytics

### 1. Key Metrics

- Total orders processed
- Call success rate
- Approval queue length
- Risk alert frequency
- Average call duration

### 2. Real-time Dashboard

All metrics update in real-time via Socket.IO.

### 3. Audit Trail

Complete audit log for compliance and debugging.

---

## 🎯 Next Steps

1. **Test the complete flow** with real phone calls
2. **Customize the UI** with your branding
3. **Add more languages** to the detection system
4. **Implement advanced analytics**
5. **Deploy to production** infrastructure
6. **Scale with load balancers** and Redis

---

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**:
- Check all dependencies installed
- Verify .env file configuration
- Check port 5000 is available

**Dashboard won't connect**:
- Verify backend is running on port 5000
- Check CORS configuration
- Verify API_KEY matches

**Socket.IO not working**:
- Check eventlet is installed
- Verify WebSocket support
- Check firewall settings

**Android app authentication fails**:
- Verify JWT_SECRET matches
- Check API endpoints are accessible
- Verify credentials are correct

---

**🎉 Your VyapaarSetu AI system is now ready for production use!**