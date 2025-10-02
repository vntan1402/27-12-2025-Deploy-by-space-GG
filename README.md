# Ship Management System

## Overview
AI-powered Ship Management System for maritime certificates and ship records management.

**Tech Stack:**
- Backend: FastAPI + Python + MongoDB
- Frontend: React + TailwindCSS
- AI: Google Gemini (via Emergent LLM Key)

---

## 🚨 CRITICAL DOCUMENTATION

### Date/Timezone Handling
**⚠️ MUST READ before working with ANY date fields:**

👉 **[TIMEZONE_HANDLING_GUIDE.md](./TIMEZONE_HANDLING_GUIDE.md)**

**Summary:** All dates MUST use UTC timezone. MongoDB stores naive datetime objects which cause 1-day shifts if not handled correctly. The guide contains mandatory principles for backend and frontend.

**Quick Rules:**
- Backend: Add `.replace(tzinfo=timezone.utc)` when reading from MongoDB
- Frontend Display: Use `getUTCDate()`, `getUTCMonth()`, `getUTCFullYear()`
- Frontend Submit: Use `convertDateInputToUTC()` helper

---

## Project Structure

```
/app
├── backend/
│   ├── server.py           # Main FastAPI application
│   ├── mongodb_database.py # MongoDB operations
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   └── App.js         # Main React application (monolithic)
│   └── package.json       # Node dependencies
└── TIMEZONE_HANDLING_GUIDE.md  # ⚠️ CRITICAL - Date handling principles
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 16+
- MongoDB
- Emergent LLM API Key (for AI features)

### Installation
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
yarn install
```

### Running
```bash
# Backend (via supervisor)
sudo supervisorctl restart backend

# Frontend (via supervisor)
sudo supervisorctl restart frontend
```

---

## Key Features

1. **AI Certificate Analysis**
   - Upload PDF certificates
   - Extract ship data automatically (Google Gemini)
   - Auto-populate forms

2. **Ship Management**
   - Comprehensive ship records
   - Survey schedules and dates
   - Docking history tracking

3. **Certificate Management**
   - Multiple certificate types (CSSC, CSSE, IOPP, etc.)
   - Validity tracking
   - Status monitoring

4. **Calculations**
   - Next docking dates
   - Special survey cycles
   - Anniversary dates

---

## Important Notes

### Date Fields
⚠️ **ALL date fields must follow timezone handling guide**
- See [TIMEZONE_HANDLING_GUIDE.md](./TIMEZONE_HANDLING_GUIDE.md)
- Failure to follow will cause 1-day date shifts

### API Endpoints
- Backend runs on port 8001
- All API routes prefixed with `/api`
- Authentication required (JWT tokens)

### Environment Variables
- `MONGO_URL` - MongoDB connection string
- `REACT_APP_BACKEND_URL` - Frontend API URL
- Never modify these directly

---

## Development Guidelines

### Adding New Date Fields

**Checklist:**
- [ ] Read [TIMEZONE_HANDLING_GUIDE.md](./TIMEZONE_HANDLING_GUIDE.md)
- [ ] Backend: Add UTC timezone when reading from MongoDB
- [ ] Frontend: Use UTC methods for display
- [ ] Frontend: Use `convertDateInputToUTC()` for submit
- [ ] Test: Verify no 1-day shift occurs

### Code Style
- Backend: Follow PEP 8
- Frontend: ESLint configuration in project
- Use meaningful variable names
- Add comments for complex logic

---

## Troubleshooting

### Dates Showing Wrong (1-day shift)
→ See [TIMEZONE_HANDLING_GUIDE.md](./TIMEZONE_HANDLING_GUIDE.md)

### Backend Not Starting
```bash
tail -n 100 /var/log/supervisor/backend.err.log
```

### Frontend Not Updating
- Hard refresh: Ctrl + Shift + R
- Clear browser cache
- Check browser console (F12) for errors

---

## Testing

### Backend Testing
```bash
# Use backend testing agent
See test_result.md for testing protocols
```

### Frontend Testing
```bash
# Use frontend testing agent
See test_result.md for testing protocols
```

---

## Additional Documentation

- `TIMEZONE_HANDLING_GUIDE.md` - ⚠️ **MANDATORY** - Date handling principles
- `test_result.md` - Testing protocols and results
- Other `.md` files - Feature-specific documentation

---

## License
Proprietary - Ship Management System

---

## Support
For issues related to date/timezone handling, refer to [TIMEZONE_HANDLING_GUIDE.md](./TIMEZONE_HANDLING_GUIDE.md) first.
