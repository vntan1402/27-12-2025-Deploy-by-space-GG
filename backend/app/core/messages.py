"""
Common error messages for the application
"""

# Permission error messages (Vietnamese)
PERMISSION_DENIED = "Bạn không được cấp quyền để thực hiện việc này. Hãy liên hệ Admin."
ADMIN_ONLY = "Chỉ Admin mới có quyền thực hiện việc này. Hãy liên hệ Admin."
SYSTEM_ADMIN_ONLY = "Chỉ System Admin mới có quyền thực hiện việc này."
ACCESS_DENIED = "Truy cập bị từ chối. Bạn không có quyền xem nội dung này."

# ⭐ NEW: Specific permission messages
ACCESS_DENIED_SHIP = "Bạn không có quyền truy cập tàu này. Chỉ có thể xem tàu của công ty mình hoặc tàu đang sign on."
ACCESS_DENIED_COMPANY = "Bạn không có quyền truy cập dữ liệu của công ty này."
EDITOR_ONLY = "Chỉ Editor hoặc cao hơn mới có quyền thực hiện việc này."
MANAGER_ONLY = "Chỉ Manager hoặc cao hơn mới có quyền thực hiện việc này."
DEPARTMENT_PERMISSION_DENIED = "Department của bạn không có quyền quản lý loại tài liệu này. Hãy liên hệ Manager của department tương ứng."

# ⭐ NEW: Role-specific messages
DPA_MANAGER_ONLY = "Chỉ DPA Manager hoặc Admin mới có quyền thực hiện việc này."
CREWING_MANAGER_ONLY = "Chỉ Crewing Manager hoặc Admin mới có quyền thực hiện việc này."
TECHNICAL_MANAGER_ONLY = "Chỉ Technical Manager hoặc Admin mới có quyền thực hiện việc này."
SAFETY_MANAGER_ONLY = "Chỉ Safety Manager hoặc Admin mới có quyền thực hiện việc này."

# ⭐ NEW: Special cases
ADMIN_OWN_COMPANY_ONLY = "Admin chỉ có thể cập nhật thông tin công ty của mình."
SHIP_ACCESS_DENIED = "Bạn chỉ có thể xem tài liệu của tàu đang sign on."

# Authentication error messages
NOT_AUTHENTICATED = "Vui lòng đăng nhập để tiếp tục."
INVALID_CREDENTIALS = "Tên đăng nhập hoặc mật khẩu không chính xác."
TOKEN_EXPIRED = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."

# Common error messages
NOT_FOUND = "Không tìm thấy dữ liệu."
INTERNAL_ERROR = "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
BAD_REQUEST = "Yêu cầu không hợp lệ."
