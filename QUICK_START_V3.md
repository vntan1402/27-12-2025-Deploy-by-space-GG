# 🚀 Quick Start - Google Apps Script v3.0 Secure

## 📝 Checklist Deploy (5 phút)

- [ ] 1. Mở https://script.google.com
- [ ] 2. Copy code từ `/app/GOOGLE_APPS_SCRIPT_V3_SECURE.js`
- [ ] 3. Paste vào Apps Script Editor (thay thế toàn bộ code cũ)
- [ ] 4. Save script (Ctrl+S)
- [ ] 5. Deploy → New deployment → Web app
- [ ] 6. Execute as: **Me** | Who has access: **Anyone**
- [ ] 7. Copy NEW Web App URL
- [ ] 8. Test: `./test_apps_script_v3_secure.sh`
- [ ] 9. Configure trong app: System Settings → Google Drive
- [ ] 10. Done! 🎉

---

## 🧪 Quick Test

```bash
cd /app
./test_apps_script_v3_secure.sh
# Nhập Web App URL khi được hỏi
```

**Hoặc test thủ công:**

```bash
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{"action":"test_connection","folder_id":"1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"}'
```

**Kết quả mong đợi**: `"success": true`

---

## 🔑 Key Changes từ v2.0 → v3.0

| Feature | v2.0 | v3.0 |
|---------|------|------|
| Folder ID | Hardcoded | Dynamic (qua request) |
| Logging | Full data | Masked sensitive data |
| Security | ⚠️ Medium | ✅ High |
| API Key | Optional | Not needed |

---

## 📱 Config Trong App

1. Login → System Settings → Google Drive
2. Apps Script method
3. Điền:
   - **Web App URL**: [URL từ deploy]
   - **Folder ID**: `1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB`
   - **API Key**: Để trống
4. Test Connection → Save

---

## 🆘 Quick Troubleshooting

| Vấn đề | Giải pháp |
|--------|-----------|
| POST trả về HTML | Deploy mới (không edit deployment cũ) |
| "folder_id required" | Đúng! Đây là security feature |
| "Invalid folder_id" | Kiểm tra quyền truy cập folder |
| Logs không thấy gì | Check Executions tab trong Apps Script |

---

## 📚 Docs Đầy Đủ

- `/app/HUONG_DAN_DEPLOY_V3_SECURE.md` - Hướng dẫn chi tiết
- `/app/BAO_MAT_V3_TOM_TAT.md` - Giải thích bảo mật
- `/app/GOOGLE_APPS_SCRIPT_V3_SECURE.js` - Source code

---

**Ready? Go! 🚀**
