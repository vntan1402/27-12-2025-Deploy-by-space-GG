/**
 * Bandwidth Test Component
 * Tests upload/download speeds to Google Apps Script with various payload sizes
 */
import React, { useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import api from '../../../services/api';
import { toast } from 'react-toastify';

const BandwidthTest = ({ onClose }) => {
  const { language } = useAuth();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [progress, setProgress] = useState(0);

  const runBandwidthTest = async () => {
    setLoading(true);
    setResults(null);
    setProgress(0);
    
    // Simulate progress for UX
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 15;
      });
    }, 2000);
    
    try {
      const response = await api.post('/api/health/bandwidth-test', {}, {
        timeout: 180000 // 3 minutes for full test
      });
      setResults(response.data);
      setProgress(100);
      
      const rating = response.data.summary?.bandwidth_rating;
      if (rating === 'excellent' || rating === 'good') {
        toast.success(language === 'vi' ? `Băng thông tốt: ${rating}` : `Good bandwidth: ${rating}`);
      } else if (rating === 'acceptable') {
        toast.info(language === 'vi' ? 'Băng thông chấp nhận được' : 'Acceptable bandwidth');
      } else {
        toast.warning(language === 'vi' ? `Băng thông chậm: ${rating}` : `Slow bandwidth: ${rating}`);
      }
    } catch (error) {
      console.error('Bandwidth test error:', error);
      toast.error(language === 'vi' ? 'Không thể chạy kiểm tra băng thông' : 'Failed to run bandwidth test');
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  const getRatingColor = (rating) => {
    switch (rating) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-green-500';
      case 'acceptable': return 'text-yellow-600';
      case 'slow': return 'text-orange-500';
      case 'very_slow': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getRatingBgColor = (rating) => {
    switch (rating) {
      case 'excellent': return 'bg-green-50 border-green-200';
      case 'good': return 'bg-green-50 border-green-200';
      case 'acceptable': return 'bg-yellow-50 border-yellow-200';
      case 'slow': return 'bg-orange-50 border-orange-200';
      case 'very_slow': return 'bg-red-50 border-red-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getRatingIcon = (rating) => {
    switch (rating) {
      case 'excellent': return '🚀';
      case 'good': return '✅';
      case 'acceptable': return '👍';
      case 'slow': return '🐢';
      case 'very_slow': return '🐌';
      default: return '❓';
    }
  };

  const getRatingText = (rating) => {
    const texts = {
      vi: {
        excellent: 'Xuất sắc',
        good: 'Tốt',
        acceptable: 'Chấp nhận được',
        slow: 'Chậm',
        very_slow: 'Rất chậm'
      },
      en: {
        excellent: 'Excellent',
        good: 'Good',
        acceptable: 'Acceptable',
        slow: 'Slow',
        very_slow: 'Very Slow'
      }
    };
    return texts[language === 'vi' ? 'vi' : 'en'][rating] || rating;
  };

  const formatSpeed = (mbps) => {
    if (!mbps) return 'N/A';
    return `${mbps.toFixed(2)} Mbps`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📊</span>
              <div>
                <h2 className="text-xl font-bold">
                  {language === 'vi' ? 'Kiểm tra Băng thông' : 'Bandwidth Test'}
                </h2>
                <p className="text-purple-100 text-sm">
                  {language === 'vi' 
                    ? 'Đo tốc độ upload đến Google Apps Script' 
                    : 'Measure upload speed to Google Apps Script'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Run Button */}
          <div className="mb-6">
            <button
              onClick={runBandwidthTest}
              disabled={loading}
              className={`
                w-full py-4 rounded-xl font-bold text-lg
                flex items-center justify-center gap-3
                transition-all duration-200
                ${loading 
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
                  : 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg hover:shadow-xl'}
              `}
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{language === 'vi' ? 'Đang kiểm tra...' : 'Testing...'}</span>
                </>
              ) : (
                <>
                  <span className="text-2xl">🚀</span>
                  <span>{language === 'vi' ? 'Chạy kiểm tra băng thông' : 'Run Bandwidth Test'}</span>
                </>
              )}
            </button>
          </div>

          {/* Progress Bar */}
          {loading && (
            <div className="mb-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>{language === 'vi' ? 'Đang test các payload...' : 'Testing payloads...'}</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-purple-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-2 text-center">
                {language === 'vi' 
                  ? 'Kiểm tra với 5 payload sizes: 100KB, 500KB, 1MB, 2MB, 3MB' 
                  : 'Testing with 5 payload sizes: 100KB, 500KB, 1MB, 2MB, 3MB'}
              </p>
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-4">
              {/* Overall Rating */}
              <div className={`p-4 rounded-xl border-2 ${getRatingBgColor(results.summary?.bandwidth_rating)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h5 className="font-bold text-lg">
                      {language === 'vi' ? 'Đánh giá Băng thông' : 'Bandwidth Rating'}
                    </h5>
                    <p className={`text-2xl font-bold ${getRatingColor(results.summary?.bandwidth_rating)}`}>
                      {getRatingText(results.summary?.bandwidth_rating)}
                    </p>
                  </div>
                  <div className="text-5xl">
                    {getRatingIcon(results.summary?.bandwidth_rating)}
                  </div>
                </div>
              </div>

              {/* Speed Summary */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-xl font-bold text-blue-600">
                    {formatSpeed(results.summary?.avg_upload_speed_mbps)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {language === 'vi' ? 'Trung bình' : 'Average'}
                  </div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className="text-xl font-bold text-green-600">
                    {formatSpeed(results.summary?.max_upload_speed_mbps)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {language === 'vi' ? 'Nhanh nhất' : 'Max'}
                  </div>
                </div>
                <div className="bg-orange-50 p-3 rounded-lg text-center">
                  <div className="text-xl font-bold text-orange-600">
                    {formatSpeed(results.summary?.min_upload_speed_mbps)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {language === 'vi' ? 'Chậm nhất' : 'Min'}
                  </div>
                </div>
              </div>

              {/* Detailed Results Table */}
              <div className="bg-white border rounded-xl overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b">
                  <h6 className="font-semibold text-gray-700">
                    {language === 'vi' ? 'Chi tiết từng Payload' : 'Payload Details'}
                  </h6>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">
                          {language === 'vi' ? 'Kích thước' : 'Size'}
                        </th>
                        <th className="px-4 py-2 text-center font-semibold text-gray-600">
                          {language === 'vi' ? 'Thời gian' : 'Time'}
                        </th>
                        <th className="px-4 py-2 text-center font-semibold text-gray-600">
                          {language === 'vi' ? 'Tốc độ' : 'Speed'}
                        </th>
                        <th className="px-4 py-2 text-center font-semibold text-gray-600">
                          vs Benchmark
                        </th>
                        <th className="px-4 py-2 text-center font-semibold text-gray-600">
                          {language === 'vi' ? 'Đánh giá' : 'Rating'}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.tests?.map((test, idx) => (
                        <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-4 py-3 font-medium">{test.payload_size}</td>
                          <td className="px-4 py-3 text-center">
                            {test.upload_time_seconds ? `${test.upload_time_seconds}s` : 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {formatSpeed(test.upload_speed_mbps)}
                          </td>
                          <td className="px-4 py-3 text-center font-mono">
                            {test.vs_benchmark || 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex items-center gap-1 ${getRatingColor(test.rating)}`}>
                              {getRatingIcon(test.rating)}
                              <span className="text-xs">{getRatingText(test.rating)}</span>
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Recommendations */}
              {results.summary?.bandwidth_rating === 'slow' || results.summary?.bandwidth_rating === 'very_slow' ? (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <div className="font-semibold text-yellow-800 mb-2">
                    ⚠️ {language === 'vi' ? 'Khuyến nghị' : 'Recommendation'}
                  </div>
                  <p className="text-sm text-yellow-700">
                    {language === 'vi' 
                      ? 'Băng thông chậm có thể gây timeout khi xử lý file PDF lớn. Thời gian xử lý có thể lâu hơn bình thường. Hãy liên hệ bộ phận IT để kiểm tra kết nối mạng của server.'
                      : 'Slow bandwidth may cause timeouts when processing large PDF files. Processing time may be longer than usual. Contact IT to check server network connection.'}
                  </p>
                </div>
              ) : null}

              {/* Timestamp */}
              <div className="text-center text-sm text-gray-400 mt-4">
                {language === 'vi' ? 'Kiểm tra lúc:' : 'Tested at:'} {new Date(results.timestamp).toLocaleString()}
              </div>
            </div>
          )}

          {/* Instructions when no results */}
          {!results && !loading && (
            <div className="text-center py-8 text-gray-500">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-lg mb-2">
                {language === 'vi' 
                  ? 'Công cụ kiểm tra băng thông' 
                  : 'Bandwidth Test Tool'}
              </p>
              <p className="text-sm max-w-md mx-auto">
                {language === 'vi'
                  ? 'Kiểm tra tốc độ upload từ server đến Google Apps Script với các kích thước file khác nhau (100KB - 3MB). Giúp xác định nguyên nhân chậm khi xử lý file lớn.'
                  : 'Test upload speed from server to Google Apps Script with different file sizes (100KB - 3MB). Helps identify causes of slow processing for large files.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BandwidthTest;
