# 🧪 Test Crew Audit Logs

## Testing Checklist

### ✅ **Phase 1: UI Testing**
- [ ] Navigate to System Settings → Admin Tools → Crew Audit Logs
- [ ] Verify page loads without errors
- [ ] Test filters:
  - [ ] Date range (Today, Last 7 days, Last 30 days, Custom)
  - [ ] Action type dropdown
  - [ ] User dropdown
  - [ ] Ship dropdown
  - [ ] Search by crew name
- [ ] Test pagination (if logs exist)
- [ ] Test "View Details" modal
- [ ] Test Export CSV
- [ ] Test Export Excel

### ✅ **Phase 2: Integration Testing**

#### Test 1: Create Crew
```
Steps:
1. Go to Crew List
2. Click "Add Crew"
3. Fill form with:
   - Full Name: Test Crew Alpha
   - Passport: TEST12345
   - Rank: AB
   - Status: Standby
4. Save

Expected:
- Crew created successfully
- Navigate to Audit Logs
- Should see CREATE log with:
  - Action: CREATE
  - Crew: Test Crew Alpha
  - Changes: full_name, passport, rank, status (null → values)
```

#### Test 2: Update Crew
```
Steps:
1. Edit Test Crew Alpha
2. Change:
   - Rank: AB → OS
   - Nationality: Vietnam → Philippines
3. Save

Expected:
- Navigate to Audit Logs
- Should see UPDATE log with:
  - Action: UPDATE
  - Changes: 
    - rank: "AB" → "OS"
    - nationality: "Vietnam" → "Philippines"
```

#### Test 3: Sign On
```
Steps:
1. Select Test Crew Alpha
2. Click "Sign On"
3. Fill:
   - Ship: Ship ABC
   - Date: Today
   - Place: Port A
4. Sign On

Expected:
- Navigate to Audit Logs
- Should see SIGN_ON log with:
  - Action: SIGN_ON
  - Crew: Test Crew Alpha
  - Ship: Ship ABC
  - Changes:
    - ship_sign_on: "-" → "Ship ABC"
    - status: "Standby" → "Sign on"
    - date_sign_on: null → "2024-XX-XX"
```

#### Test 4: Sign Off
```
Steps:
1. Select Test Crew Alpha (currently Sign on)
2. Click "Sign Off"
3. Fill:
   - Date: Today
   - Place: Port B
4. Sign Off

Expected:
- Navigate to Audit Logs
- Should see SIGN_OFF log with:
  - Action: SIGN_OFF
  - Crew: Test Crew Alpha
  - Ship: Ship ABC
  - Changes:
    - ship_sign_on: "Ship ABC" → "-"
    - status: "Sign on" → "Standby"
    - date_sign_off: null → "2024-XX-XX"
```

#### Test 5: Delete Crew
```
Steps:
1. Select Test Crew Alpha
2. Click Delete
3. Confirm deletion

Expected:
- Navigate to Audit Logs
- Should see DELETE log with:
  - Action: DELETE
  - Crew: Test Crew Alpha
  - Changes: all fields removed
```

### ✅ **Phase 3: API Testing**

#### Test API Directly (using curl):

```bash
# Get audit logs
curl -X GET "http://localhost:8001/api/crew-audit-logs?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get unique users
curl -X GET "http://localhost:8001/api/crew-audit-logs/filters/users" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get unique ships
curl -X GET "http://localhost:8001/api/crew-audit-logs/filters/ships" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### ✅ **Phase 4: Database Verification**

```python
# Check logs in database
python3 -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_logs():
    client = AsyncIOMotorClient(os.getenv('MONGO_URL'))
    db = client.get_default_database()
    
    # Count logs
    count = await db.crew_audit_logs.count_documents({})
    print(f'Total logs: {count}')
    
    # Get recent logs
    logs = await db.crew_audit_logs.find({}, {'_id': 0}).sort('performed_at', -1).limit(5).to_list(5)
    
    print('\nRecent logs:')
    for log in logs:
        print(f'  - {log['action']}: {log['entity_name']} by {log['performed_by']} at {log['performed_at']}')
    
    # Check indexes
    indexes = await db.crew_audit_logs.list_indexes().to_list(None)
    print(f'\nIndexes: {len(indexes)}')
    for idx in indexes:
        print(f'  - {idx['name']}')
    
    client.close()

asyncio.run(check_logs())
"
```

---

## 🐛 Troubleshooting

### Issue: No logs appearing
**Check:**
1. Backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. Look for "Failed to create audit log" errors
3. Verify indexes exist: Run database verification script above

### Issue: Frontend not loading logs
**Check:**
1. Browser console for errors (F12)
2. Network tab: check API calls
3. Backend logs for API errors

### Issue: Export not working
**Check:**
1. Browser console for errors
2. Verify xlsx library installed: `cd /app/frontend && yarn list xlsx`

---

## ✅ Success Criteria

**Phase 2 (Backend + Integration) is complete when:**
- ✅ All CRUD operations create audit logs
- ✅ Sign on/off creates audit logs
- ✅ Logs contain correct before/after values
- ✅ API endpoints return data correctly
- ✅ Filters work
- ✅ Export works
- ✅ TTL index working (logs auto-delete after 1 year)

---

## 📊 Expected Results

After running all tests, you should have approximately:
- 5 logs (1 CREATE, 1 UPDATE, 1 SIGN_ON, 1 SIGN_OFF, 1 DELETE)
- All logs should be visible in Audit Logs page
- All filters should work
- Export should contain all 5 logs

---

**Ready to test!** 🚀
