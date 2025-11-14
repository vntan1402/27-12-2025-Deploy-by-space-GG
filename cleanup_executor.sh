#!/bin/bash

# ============================================
# Code Cleanup Executor
# Ship Management System
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
FILES_DELETED=0
FILES_ARCHIVED=0
SPACE_FREED=0

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Code Cleanup Executor${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# Function: Confirm Action
# ============================================
confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================
# Function: Create Backup
# ============================================
create_backup() {
    echo -e "${BLUE}Creating backup...${NC}"
    BACKUP_DIR="/tmp/ship_management_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup test files
    echo "  Backing up test files..."
    mkdir -p "$BACKUP_DIR/tests"
    cp /app/*test*.py "$BACKUP_DIR/tests/" 2>/dev/null || true
    cp /app/backend/*test*.py "$BACKUP_DIR/tests/" 2>/dev/null || true
    
    # Backup documentation
    echo "  Backing up documentation..."
    mkdir -p "$BACKUP_DIR/docs"
    cp /app/*.md "$BACKUP_DIR/docs/" 2>/dev/null || true
    
    # Backup utilities
    echo "  Backing up utility scripts..."
    mkdir -p "$BACKUP_DIR/scripts"
    cp /app/*_admin*.py "$BACKUP_DIR/scripts/" 2>/dev/null || true
    cp /app/debug_*.py "$BACKUP_DIR/scripts/" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
    echo ""
}

# ============================================
# PHASE 1: Delete Test Files
# ============================================
phase1_delete_tests() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}PHASE 1: Delete Test Files${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    
    if ! confirm "Delete test files? This will free ~277KB"; then
        echo -e "${YELLOW}⏭️  Skipped Phase 1${NC}"
        return
    fi
    
    TEST_FILES=(
        "/app/admin_api_test.py"
        "/app/backend_test.py"
        "/app/backend_test_audit_cert.py"
        "/app/backend_test_base_fee.py"
        "/app/backend_test_crew.py"
        "/app/backend_test_sidebar.py"
        "/app/test_nonexistent_ship.py"
        "/app/test_upcoming_surveys.py"
        "/app/test_english_autofill.js"
        "/app/backend/test_report_valid_date_calculator.py"
        "/app/backend/server_filedb_backup.py"
        "/app/backend/server_filedb_complete_backup.py"
        "/app/clear_all_crew_data.py"
        "/app/TEST_ADMIN_CREATION.py"
    )
    
    for file in "${TEST_FILES[@]}"; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" | cut -f1)
            rm "$file"
            echo -e "  ${GREEN}✅ Deleted:${NC} $(basename $file) ($size)"
            ((FILES_DELETED++))
        else
            echo -e "  ${YELLOW}⚠️  Not found:${NC} $(basename $file)"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Phase 1 Complete: $FILES_DELETED files deleted${NC}"
    echo ""
}

# ============================================
# PHASE 2: Archive Documentation
# ============================================
phase2_archive_docs() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}PHASE 2: Archive Documentation${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    
    if ! confirm "Archive old documentation? This will organize ~80+ files"; then
        echo -e "${YELLOW}⏭️  Skipped Phase 2${NC}"
        return
    fi
    
    # Create archive structure
    echo "Creating archive structure..."
    mkdir -p /docs/archive/{phases,fixes,migrations,analysis,planning,old-guides}
    mkdir -p /docs/current/{setup,operations,api,architecture}
    
    # Archive phase documents
    echo ""
    echo "Archiving phase documents..."
    for file in /app/PHASE_*.md; do
        if [ -f "$file" ]; then
            mv "$file" /docs/archive/phases/
            echo -e "  ${GREEN}✅ Archived:${NC} $(basename $file)"
            ((FILES_ARCHIVED++))
        fi
    done
    
    # Archive fix documents
    echo ""
    echo "Archiving fix documents..."
    for pattern in "*FIX*.md" "BUGFIX_*.md" "*_ERROR_*.md"; do
        for file in /app/$pattern; do
            if [ -f "$file" ]; then
                mv "$file" /docs/archive/fixes/
                echo -e "  ${GREEN}✅ Archived:${NC} $(basename $file)"
                ((FILES_ARCHIVED++))
            fi
        done
    done
    
    # Archive migration documents
    echo ""
    echo "Archiving migration documents..."
    for pattern in "*MIGRATION*.md" "*DEPLOYMENT*.md"; do
        for file in /app/$pattern; do
            if [ -f "$file" ]; then
                mv "$file" /docs/archive/migrations/
                echo -e "  ${GREEN}✅ Archived:${NC} $(basename $file)"
                ((FILES_ARCHIVED++))
            fi
        done
    done
    
    # Archive analysis documents
    echo ""
    echo "Archiving analysis documents..."
    for pattern in "*ANALYSIS*.md" "*STRUCTURE*.md" "*LOGIC*.md" "*COMPARISON*.md"; do
        for file in /app/$pattern; do
            if [ -f "$file" ]; then
                mv "$file" /docs/archive/analysis/
                echo -e "  ${GREEN}✅ Archived:${NC} $(basename $file)"
                ((FILES_ARCHIVED++))
            fi
        done
    done
    
    # Archive planning documents
    echo ""
    echo "Archiving planning documents..."
    for pattern in "*PLAN*.md" "*FLOW*.md" "VISUAL_STORYBOARD.md" "*REFACTORING*.md"; do
        for file in /app/$pattern; do
            if [ -f "$file" ] && [ "$file" != "/app/CODE_CLEANUP_PLAN.md" ]; then
                mv "$file" /docs/archive/planning/
                echo -e "  ${GREEN}✅ Archived:${NC} $(basename $file)"
                ((FILES_ARCHIVED++))
            fi
        done
    done
    
    # Move current operational docs
    echo ""
    echo "Organizing operational documents..."
    for pattern in "HUONG_DAN_*.md" "*_GUIDE.md" "ROLE_PERMISSIONS*.md" "CHECK_*.md"; do
        for file in /app/$pattern; do
            if [ -f "$file" ]; then
                mv "$file" /docs/current/operations/
                echo -e "  ${GREEN}✅ Moved:${NC} $(basename $file)"
            fi
        done
    done
    
    # Move architecture docs
    echo ""
    echo "Organizing architecture documents..."
    for file in /app/DATABASE_ARCHITECTURE_ANALYSIS.md \
                /app/ELECTRON_APP_DETAILED_GUIDE.md \
                /app/OFFLINE_*.md; do
        if [ -f "$file" ]; then
            mv "$file" /docs/current/architecture/
            echo -e "  ${GREEN}✅ Moved:${NC} $(basename $file)"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Phase 2 Complete: $FILES_ARCHIVED files archived${NC}"
    echo ""
}

# ============================================
# PHASE 3: Trim test_result.md
# ============================================
phase3_trim_test_results() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}PHASE 3: Trim test_result.md${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    
    if [ ! -f /app/test_result.md ]; then
        echo -e "${YELLOW}⚠️  test_result.md not found${NC}"
        return
    fi
    
    ORIGINAL_SIZE=$(du -h /app/test_result.md | cut -f1)
    echo "Current size: $ORIGINAL_SIZE"
    
    if ! confirm "Trim test_result.md? Will keep last 200 entries"; then
        echo -e "${YELLOW}⏭️  Skipped Phase 3${NC}"
        return
    fi
    
    echo "Trimming test_result.md..."
    
    # Create archive directory
    mkdir -p /docs/archive/test_results
    
    # Archive old content
    ARCHIVE_FILE="/docs/archive/test_results/test_result_$(date +%Y%m).md"
    
    # Keep only header and last 200 lines (approximately last 100 entries)
    head -n 100 /app/test_result.md > /tmp/test_result_header.md
    tail -n 2000 /app/test_result.md > /tmp/test_result_recent.md
    
    # Archive old content
    cp /app/test_result.md "$ARCHIVE_FILE"
    
    # Create new trimmed file
    cat /tmp/test_result_header.md > /app/test_result.md
    echo "" >> /app/test_result.md
    echo "# ===== TRIMMED ON $(date) =====" >> /app/test_result.md
    echo "# Older entries archived to: $ARCHIVE_FILE" >> /app/test_result.md
    echo "" >> /app/test_result.md
    cat /tmp/test_result_recent.md >> /app/test_result.md
    
    # Cleanup temp files
    rm /tmp/test_result_header.md /tmp/test_result_recent.md
    
    NEW_SIZE=$(du -h /app/test_result.md | cut -f1)
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_FILE" | cut -f1)
    
    echo -e "  ${GREEN}✅ Original:${NC} $ORIGINAL_SIZE"
    echo -e "  ${GREEN}✅ New size:${NC} $NEW_SIZE"
    echo -e "  ${GREEN}✅ Archived:${NC} $ARCHIVE_SIZE to $ARCHIVE_FILE"
    
    echo ""
    echo -e "${GREEN}✅ Phase 3 Complete${NC}"
    echo ""
}

# ============================================
# PHASE 4: Consolidate Scripts
# ============================================
phase4_consolidate_scripts() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}PHASE 4: Consolidate Utility Scripts${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    
    if ! confirm "Consolidate utility scripts to /scripts/?"; then
        echo -e "${YELLOW}⏭️  Skipped Phase 4${NC}"
        return
    fi
    
    # Create scripts structure
    echo "Creating scripts structure..."
    mkdir -p /scripts/{admin,database,utilities}
    
    # Move admin scripts
    echo ""
    echo "Moving admin scripts..."
    for file in /app/create_admin_user.py \
                /app/CREATE_PRODUCTION_ADMIN_DATA.py; do
        if [ -f "$file" ]; then
            mv "$file" /scripts/admin/
            echo -e "  ${GREEN}✅ Moved:${NC} $(basename $file)"
        fi
    done
    
    # Move database scripts
    echo ""
    echo "Moving database scripts..."
    for file in /app/database_management.py \
                /app/debug_mongodb.py; do
        if [ -f "$file" ]; then
            mv "$file" /scripts/database/
            echo -e "  ${GREEN}✅ Moved:${NC} $(basename $file)"
        fi
    done
    
    # Move other utilities
    echo ""
    echo "Moving utility scripts..."
    for file in /app/EXPORT_USERS_FOR_PRODUCTION.py \
                /app/debug_*.py; do
        if [ -f "$file" ]; then
            mv "$file" /scripts/utilities/
            echo -e "  ${GREEN}✅ Moved:${NC} $(basename $file)"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Phase 4 Complete${NC}"
    echo ""
}

# ============================================
# PHASE 5: Create Documentation Index
# ============================================
phase5_create_index() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}PHASE 5: Create Documentation Index${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    
    cat > /docs/README.md << 'EOF'
# Ship Management System - Documentation

## 📚 Documentation Structure

### Current Documentation
- **[Operations](./current/operations/)** - Operational guides and procedures
- **[Architecture](./current/architecture/)** - System architecture documentation
- **[Setup](./current/setup/)** - Setup and installation guides
- **[API](./current/api/)** - API documentation

### Archived Documentation
- **[Phases](./archive/phases/)** - Completed development phases
- **[Fixes](./archive/fixes/)** - Bug fix documentation
- **[Migrations](./archive/migrations/)** - Data migration documentation
- **[Analysis](./archive/analysis/)** - Code analysis reports
- **[Planning](./archive/planning/)** - Design and planning documents
- **[Test Results](./archive/test_results/)** - Historical test results

## 🔍 Quick Links

### For Developers
- System Architecture
- API Documentation
- Development Guides

### For Operations
- Deployment Guide
- Troubleshooting Guide
- User Management

### For Support
- Common Issues
- Debug Procedures
- Contact Information

## 📝 Documentation Guidelines

1. Keep documentation up-to-date
2. Archive completed projects
3. Max file size: 100KB
4. Use clear, descriptive names
5. Review and cleanup quarterly

---

**Last Updated:** $(date +%Y-%m-%d)
EOF
    
    echo -e "${GREEN}✅ Created /docs/README.md${NC}"
    echo ""
}

# ============================================
# Summary Report
# ============================================
generate_report() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}Cleanup Summary Report${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${GREEN}Files Deleted:${NC} $FILES_DELETED"
    echo -e "${GREEN}Files Archived:${NC} $FILES_ARCHIVED"
    echo ""
    echo -e "${GREEN}New Structure:${NC}"
    echo "  /docs/archive/    - Archived documentation"
    echo "  /docs/current/    - Current documentation"
    echo "  /scripts/         - Utility scripts"
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}✅ Cleanup Complete!${NC}"
    echo -e "${BLUE}============================================${NC}"
}

# ============================================
# Main Execution
# ============================================
main() {
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: This will delete and move files!${NC}"
    echo -e "${YELLOW}⚠️  Make sure you have a backup before proceeding.${NC}"
    echo ""
    
    if ! confirm "Continue with cleanup?"; then
        echo -e "${RED}Cleanup cancelled.${NC}"
        exit 0
    fi
    
    # Create backup
    create_backup
    
    # Execute phases
    phase1_delete_tests
    phase2_archive_docs
    phase3_trim_test_results
    phase4_consolidate_scripts
    phase5_create_index
    
    # Generate report
    generate_report
    
    echo ""
    echo -e "${BLUE}Backup Location:${NC} $BACKUP_DIR"
    echo -e "${YELLOW}Keep backup for at least 30 days!${NC}"
    echo ""
}

# Run main
main
