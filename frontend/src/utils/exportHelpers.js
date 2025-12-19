/**
 * Export Helpers - PDF and XLSX export utilities
 */
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';
import { formatDateDisplay } from './dateHelpers';

/**
 * Remove Vietnamese diacritics for PDF export (jsPDF doesn't support Vietnamese fonts by default)
 */
const removeVietnameseDiacritics = (str) => {
  if (!str) return str;
  const from = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ';
  const to = 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD';
  let result = str;
  for (let i = 0; i < from.length; i++) {
    result = result.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
  }
  return result;
};

/**
 * Export data to PDF
 * @param {Array} data - Array of objects to export
 * @param {Object} options - Export options
 */
export const exportToPDF = (data, options = {}) => {
  const {
    title = 'Export Data',
    subtitle = '',
    columns = [],
    filename = 'export.pdf',
    orientation = 'landscape',
    language = 'vi'
  } = options;

  const doc = new jsPDF({
    orientation,
    unit: 'mm',
    format: 'a4'
  });

  // Convert Vietnamese text to non-diacritics for PDF compatibility
  const safeTitle = removeVietnameseDiacritics(title);
  const safeSubtitle = removeVietnameseDiacritics(subtitle);

  // Add title
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text(safeTitle, 14, 15);

  // Add subtitle if provided
  if (safeSubtitle) {
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(safeSubtitle, 14, 22);
  }

  // Add timestamp
  doc.setFontSize(8);
  doc.setTextColor(100);
  const exportDate = new Date().toLocaleString(language === 'vi' ? 'vi-VN' : 'en-US');
  doc.text(`${language === 'vi' ? 'Ngay xuat' : 'Export date'}: ${exportDate}`, 14, safeSubtitle ? 28 : 22);

  // Prepare table data - remove Vietnamese diacritics
  const tableColumn = columns.map(col => removeVietnameseDiacritics(col.header));
  const tableRows = data.map(row => 
    columns.map(col => {
      const value = col.accessor(row);
      const strValue = value !== null && value !== undefined ? String(value) : '-';
      return removeVietnameseDiacritics(strValue);
    })
  );

  // Generate table
  doc.autoTable({
    head: [tableColumn],
    body: tableRows,
    startY: safeSubtitle ? 32 : 26,
    styles: {
      fontSize: 8,
      cellPadding: 2,
      overflow: 'linebreak',
      halign: 'left'
    },
    headStyles: {
      fillColor: [59, 130, 246],
      textColor: 255,
      fontStyle: 'bold',
      fontSize: 8
    },
    alternateRowStyles: {
      fillColor: [245, 247, 250]
    },
    columnStyles: columns.reduce((acc, col, index) => {
      if (col.width) {
        acc[index] = { cellWidth: col.width };
      }
      return acc;
    }, {}),
    margin: { top: 10, right: 10, bottom: 10, left: 10 },
    didDrawPage: (pageData) => {
      // Footer with page number
      const pageCount = doc.internal.getNumberOfPages();
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text(
        `${language === 'vi' ? 'Trang' : 'Page'} ${pageData.pageNumber} / ${pageCount}`,
        doc.internal.pageSize.getWidth() - 25,
        doc.internal.pageSize.getHeight() - 10
      );
    }
  });

  // Save the PDF
  doc.save(filename);
};

/**
 * Export data to XLSX
 * @param {Array} data - Array of objects to export
 * @param {Object} options - Export options
 */
export const exportToXLSX = (data, options = {}) => {
  const {
    title = 'Export Data',
    columns = [],
    filename = 'export.xlsx',
    sheetName = 'Sheet1'
  } = options;

  // Prepare data for Excel
  const headers = columns.map(col => col.header);
  const rows = data.map(row =>
    columns.map(col => {
      const value = col.accessor(row);
      return value !== null && value !== undefined ? value : '';
    })
  );

  // Create workbook and worksheet
  const wb = XLSX.utils.book_new();
  
  // Add title row
  const wsData = [
    [title],
    [], // Empty row
    headers,
    ...rows
  ];

  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // Set column widths
  const colWidths = columns.map(col => ({ wch: col.excelWidth || 15 }));
  ws['!cols'] = colWidths;

  // Merge title cell across all columns
  ws['!merges'] = [
    { s: { r: 0, c: 0 }, e: { r: 0, c: columns.length - 1 } }
  ];

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(wb, ws, sheetName);

  // Save the file
  XLSX.writeFile(wb, filename);
};

/**
 * Export Upcoming Surveys to PDF
 */
export const exportUpcomingSurveysToPDF = (surveys, options = {}) => {
  const { language = 'vi', companyName = '', totalCount = 0 } = options;
  
  const columns = [
    { 
      header: language === 'vi' ? 'Tên Tàu' : 'Ship Name', 
      accessor: (row) => row.ship_name,
      width: 35
    },
    { 
      header: language === 'vi' ? 'Tên Certificate' : 'Certificate Name', 
      accessor: (row) => row.cert_name_display || row.cert_name,
      width: 45
    },
    { 
      header: language === 'vi' ? 'Next Survey' : 'Next Survey', 
      accessor: (row) => formatDateDisplay(row.next_survey_date),
      width: 25
    },
    { 
      header: language === 'vi' ? 'Loại Survey' : 'Survey Type', 
      accessor: (row) => row.next_survey_type || '-',
      width: 25
    },
    { 
      header: language === 'vi' ? 'Last Endorse' : 'Last Endorse', 
      accessor: (row) => formatDateDisplay(row.last_endorse),
      width: 25
    },
    { 
      header: language === 'vi' ? 'Tình trạng' : 'Status', 
      accessor: (row) => {
        if (row.is_overdue) return language === 'vi' ? 'Quá hạn' : 'Overdue';
        if (row.is_critical) return language === 'vi' ? 'Khẩn cấp' : 'Critical';
        if (row.is_due_soon) return language === 'vi' ? 'Sắp đến hạn' : 'Due Soon';
        return language === 'vi' ? 'Trong Window' : 'In Window';
      },
      width: 25
    }
  ];

  const title = language === 'vi' 
    ? 'THÔNG BÁO SURVEY SẮP ĐẾN HẠN' 
    : 'UPCOMING SURVEY NOTIFICATION';
  
  const subtitle = language === 'vi'
    ? `Tổng cộng: ${totalCount} certificate | Công ty: ${companyName}`
    : `Total: ${totalCount} certificates | Company: ${companyName}`;

  const today = new Date().toISOString().split('T')[0];
  const filename = `upcoming_surveys_${today}.pdf`;

  exportToPDF(surveys, {
    title,
    subtitle,
    columns,
    filename,
    orientation: 'landscape',
    language
  });
};

/**
 * Export Upcoming Surveys to XLSX
 */
export const exportUpcomingSurveysToXLSX = (surveys, options = {}) => {
  const { language = 'vi', companyName = '', totalCount = 0 } = options;
  
  const columns = [
    { 
      header: language === 'vi' ? 'Tên Tàu' : 'Ship Name', 
      accessor: (row) => row.ship_name,
      excelWidth: 25
    },
    { 
      header: language === 'vi' ? 'Loại Certificate' : 'Certificate Type', 
      accessor: (row) => row.certificate_type === 'company' 
        ? (language === 'vi' ? 'Công ty' : 'Company') 
        : (language === 'vi' ? 'Tàu' : 'Ship'),
      excelWidth: 15
    },
    { 
      header: language === 'vi' ? 'Tên Certificate' : 'Certificate Name', 
      accessor: (row) => row.cert_name_display || row.cert_name,
      excelWidth: 40
    },
    { 
      header: language === 'vi' ? 'Next Survey' : 'Next Survey', 
      accessor: (row) => formatDateDisplay(row.next_survey_date),
      excelWidth: 15
    },
    { 
      header: language === 'vi' ? 'Loại Survey' : 'Survey Type', 
      accessor: (row) => row.next_survey_type || '-',
      excelWidth: 20
    },
    { 
      header: language === 'vi' ? 'Last Endorse' : 'Last Endorse', 
      accessor: (row) => formatDateDisplay(row.last_endorse),
      excelWidth: 15
    },
    { 
      header: language === 'vi' ? 'Còn lại (ngày)' : 'Days Remaining', 
      accessor: (row) => row.days_until_window_close,
      excelWidth: 15
    },
    { 
      header: language === 'vi' ? 'Window Type' : 'Window Type', 
      accessor: (row) => row.window_type || '-',
      excelWidth: 15
    },
    { 
      header: language === 'vi' ? 'Tình trạng' : 'Status', 
      accessor: (row) => {
        if (row.is_overdue) return language === 'vi' ? 'Quá hạn' : 'Overdue';
        if (row.is_critical) return language === 'vi' ? 'Khẩn cấp' : 'Critical';
        if (row.is_due_soon) return language === 'vi' ? 'Sắp đến hạn' : 'Due Soon';
        return language === 'vi' ? 'Trong Window' : 'In Window';
      },
      excelWidth: 15
    }
  ];

  const title = language === 'vi' 
    ? `THÔNG BÁO SURVEY SẮP ĐẾN HẠN - ${companyName} (Tổng: ${totalCount})`
    : `UPCOMING SURVEY NOTIFICATION - ${companyName} (Total: ${totalCount})`;

  const today = new Date().toISOString().split('T')[0];
  const filename = `upcoming_surveys_${today}.xlsx`;

  exportToXLSX(surveys, {
    title,
    columns,
    filename,
    sheetName: language === 'vi' ? 'Survey sắp đến hạn' : 'Upcoming Surveys'
  });
};
