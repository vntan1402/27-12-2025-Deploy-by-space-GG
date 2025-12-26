/**
 * Connectivity Health Check Component
 * Tests connection to external services (GDrive, Document AI, etc.)
 */
import React, { useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import api from '../../../services/api';
import { toast } from 'react-toastify';

const ConnectivityHealthCheck = ({ onClose }) => {
  const { language } = useAuth();
  const [loading, setLoading] = useState(false);
  const [diagnosticLoading, setDiagnosticLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [diagnosticResults, setDiagnosticResults] = useState(null);

  const runHealthCheck = async () => {
    setLoading(true);
    setResults(null);
    
    try {
      const response = await api.get('/api/health/connectivity');
      setResults(response.data);
      
      if (response.data.overall_status === 'healthy') {
        toast.success(language === 'vi' ? 'Tất cả dịch vụ hoạt động bình thường!' : 'All services are healthy!');
      } else if (response.data.overall_status === 'degraded') {
        toast.warning(language === 'vi' ? 'Một số dịch vụ đang gặp vấn đề' : 'Some services have issues');
      } else {
        toast.error(language === 'vi' ? 'Có lỗi kết nối!' : 'Connection errors detected!');
      }
    } catch (error) {
      console.error('Health check error:', error);
      toast.error(language === 'vi' ? 'Không thể kiểm tra kết nối' : 'Failed to check connectivity');
    } finally {
      setLoading(false);
    }
  };

  const runProductionDiagnostic = async () => {
    setDiagnosticLoading(true);
    setDiagnosticResults(null);
    
    try {
      const response = await api.get('/api/health/production-diagnostic');
      setDiagnosticResults(response.data);
      
      const rating = response.data.summary?.stability_rating;
      if (rating === 'excellent' || rating === 'good') {
        toast.success(language === 'vi' ? `Kết nối ổn định: ${rating}` : `Connection stable: ${rating}`);
      } else if (rating === 'slow') {
        toast.warning(language === 'vi' ? 'Kết nối chậm nhưng ổn định' : 'Connection slow but stable');
      } else {
        toast.error(language === 'vi' ? `Kết nối không ổn định: ${rating}` : `Unstable connection: ${rating}`);
      }
    } catch (error) {
      console.error('Diagnostic error:', error);
      toast.error(language === 'vi' ? 'Không thể chạy diagnostic' : 'Failed to run diagnostic');
    } finally {
      setDiagnosticLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return '✅';
      case 'degraded':
        return '⚠️';
      case 'unhealthy':
        return '❌';
      default:
        return '❓';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'unhealthy':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getLatencyColor = (latencyMs) => {
    if (!latencyMs) return 'text-gray-500';
    if (latencyMs < 1000) return 'text-green-600';
    if (latencyMs < 3000) return 'text-yellow-600';
    if (latencyMs < 5000) return 'text-orange-600';
    return 'text-red-600';
  };

  const formatLatency = (latencyMs) => {
    if (!latencyMs) return 'N/A';
    if (latencyMs < 1000) return `${latencyMs.toFixed(0)}ms`;
    return `${(latencyMs / 1000).toFixed(2)}s`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                🔌 {language === 'vi' ? 'Kiểm tra kết nối' : 'Connectivity Health Check'}
              </h2>
              <p className="text-blue-100 text-sm mt-1">
                {language === 'vi' 
                  ? 'Kiểm tra kết nối đến các dịch vụ bên ngoài' 
                  : 'Test connections to external services'}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Run Buttons */}
          <div className="mb-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={runHealthCheck}
              disabled={loading || diagnosticLoading}
              className={`
                py-4 rounded-xl font-bold text-base
                flex items-center justify-center gap-3
                transition-all duration-200
                ${loading || diagnosticLoading
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'}
              `}
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{language === 'vi' ? 'Đang kiểm tra...' : 'Checking...'}</span>
                </>
              ) : (
                <>
                  <span className="text-xl">🔍</span>
                  <span>{language === 'vi' ? 'Kiểm tra nhanh' : 'Quick Check'}</span>
                </>
              )}
            </button>
            
            <button
              onClick={runProductionDiagnostic}
              disabled={loading || diagnosticLoading}
              className={`
                py-4 rounded-xl font-bold text-base
                flex items-center justify-center gap-3
                transition-all duration-200
                ${loading || diagnosticLoading
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
                  : 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg hover:shadow-xl'}
              `}
            >
              {diagnosticLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{language === 'vi' ? 'Đang chẩn đoán...' : 'Diagnosing...'}</span>
                </>
              ) : (
                <>
                  <span className="text-xl">🔬</span>
                  <span>{language === 'vi' ? 'Chẩn đoán Production' : 'Production Diagnostic'}</span>
                </>
              )}
            </button>
          </div>

          {/* Results */}
          {results && (
            <div className="space-y-4">
              {/* Overall Status */}
              <div className={`p-4 rounded-xl border-2 ${getStatusColor(results.overall_status)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{getStatusIcon(results.overall_status)}</span>
                    <div>
                      <h3 className="font-bold text-lg">
                        {language === 'vi' ? 'Trạng thái tổng quan' : 'Overall Status'}
                      </h3>
                      <p className="text-sm opacity-80">
                        {results.overall_status === 'healthy' && (language === 'vi' ? 'Tất cả dịch vụ hoạt động tốt' : 'All services operational')}
                        {results.overall_status === 'degraded' && (language === 'vi' ? 'Một số dịch vụ gặp vấn đề' : 'Some services have issues')}
                        {results.overall_status === 'unhealthy' && (language === 'vi' ? 'Nhiều dịch vụ không hoạt động' : 'Multiple services down')}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{results.summary.healthy}/{results.summary.total_services}</div>
                    <div className="text-sm opacity-80">{language === 'vi' ? 'Dịch vụ OK' : 'Services OK'}</div>
                  </div>
                </div>
              </div>

              {/* Services List */}
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-700">
                  {language === 'vi' ? 'Chi tiết từng dịch vụ:' : 'Service Details:'}
                </h4>
                
                {Object.entries(results.services).map(([key, service]) => (
                  <div 
                    key={key}
                    className={`p-4 rounded-lg border-2 ${getStatusColor(service.status)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl mt-1">{getStatusIcon(service.status)}</span>
                        <div>
                          <h5 className="font-semibold">{service.service}</h5>
                          <p className="text-sm opacity-80 mt-1">{service.message}</p>
                          
                          {/* Details */}
                          {service.details && Object.keys(service.details).length > 0 && (
                            <div className="mt-2 text-xs space-y-1 opacity-70">
                              {Object.entries(service.details).map(([k, v]) => (
                                <div key={k}>
                                  <span className="font-medium">{k}:</span> {String(v)}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Latency */}
                      <div className="text-right">
                        <div className={`text-xl font-bold ${getLatencyColor(service.latency_ms)}`}>
                          {formatLatency(service.latency_ms)}
                        </div>
                        <div className="text-xs text-gray-500">latency</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-gray-700">{results.summary.total_services}</div>
                  <div className="text-sm text-gray-500">{language === 'vi' ? 'Tổng dịch vụ' : 'Total Services'}</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">{results.summary.healthy}</div>
                  <div className="text-sm text-gray-500">{language === 'vi' ? 'Hoạt động tốt' : 'Healthy'}</div>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className={`text-2xl font-bold ${getLatencyColor(results.summary.avg_latency_ms)}`}>
                    {formatLatency(results.summary.avg_latency_ms)}
                  </div>
                  <div className="text-sm text-gray-500">{language === 'vi' ? 'Latency TB' : 'Avg Latency'}</div>
                </div>
              </div>

              {/* Timestamp */}
              <div className="text-center text-sm text-gray-400 mt-4">
                {language === 'vi' ? 'Kiểm tra lúc:' : 'Checked at:'} {new Date(results.timestamp).toLocaleString()}
              </div>
            </div>
          )}

          {/* Production Diagnostic Results */}
          {diagnosticResults && (
            <div className="space-y-4 mt-6">
              <h4 className="font-semibold text-gray-700 flex items-center gap-2">
                🔬 {language === 'vi' ? 'Kết quả Chẩn đoán Production' : 'Production Diagnostic Results'}
              </h4>
              
              {/* Stability Rating */}
              <div className={`p-4 rounded-xl border-2 ${
                diagnosticResults.summary?.stability_rating === 'excellent' ? 'bg-green-50 border-green-200' :
                diagnosticResults.summary?.stability_rating === 'good' ? 'bg-green-50 border-green-200' :
                diagnosticResults.summary?.stability_rating === 'slow' ? 'bg-yellow-50 border-yellow-200' :
                'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h5 className="font-bold text-lg">
                      {language === 'vi' ? 'Độ ổn định kết nối' : 'Connection Stability'}
                    </h5>
                    <p className="text-sm opacity-80">
                      {diagnosticResults.summary?.stability_rating === 'excellent' && (language === 'vi' ? 'Xuất sắc - Kết nối rất nhanh và ổn định' : 'Excellent - Very fast and stable')}
                      {diagnosticResults.summary?.stability_rating === 'good' && (language === 'vi' ? 'Tốt - Kết nối ổn định' : 'Good - Stable connection')}
                      {diagnosticResults.summary?.stability_rating === 'slow' && (language === 'vi' ? 'Chậm - Kết nối ổn định nhưng chậm' : 'Slow - Stable but slow')}
                      {diagnosticResults.summary?.stability_rating === 'unstable' && (language === 'vi' ? 'Không ổn định - Có thể gây timeout' : 'Unstable - May cause timeouts')}
                      {diagnosticResults.summary?.stability_rating === 'poor' && (language === 'vi' ? 'Kém - Kết nối rất không ổn định' : 'Poor - Very unstable connection')}
                    </p>
                  </div>
                  <div className="text-4xl">
                    {diagnosticResults.summary?.stability_rating === 'excellent' && '🚀'}
                    {diagnosticResults.summary?.stability_rating === 'good' && '✅'}
                    {diagnosticResults.summary?.stability_rating === 'slow' && '🐢'}
                    {diagnosticResults.summary?.stability_rating === 'unstable' && '⚠️'}
                    {diagnosticResults.summary?.stability_rating === 'poor' && '❌'}
                  </div>
                </div>
              </div>
              
              {/* Ping Test Results */}
              <div className="grid grid-cols-3 gap-3">
                {diagnosticResults.ping_tests?.map((ping, idx) => (
                  <div key={idx} className={`p-3 rounded-lg text-center ${
                    ping.status === 'success' ? 'bg-green-50' : 
                    ping.status === 'timeout' ? 'bg-red-50' : 'bg-yellow-50'
                  }`}>
                    <div className="text-sm text-gray-500">Ping #{ping.ping_number}</div>
                    <div className={`text-lg font-bold ${getLatencyColor(ping.latency_ms)}`}>
                      {ping.latency_ms ? formatLatency(ping.latency_ms) : ping.status}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Latency Stats */}
              <div className="grid grid-cols-4 gap-3">
                <div className="bg-gray-50 p-3 rounded-lg text-center">
                  <div className={`text-xl font-bold ${getLatencyColor(diagnosticResults.summary?.avg_latency_ms)}`}>
                    {formatLatency(diagnosticResults.summary?.avg_latency_ms)}
                  </div>
                  <div className="text-xs text-gray-500">{language === 'vi' ? 'Trung bình' : 'Average'}</div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className={`text-xl font-bold ${getLatencyColor(diagnosticResults.summary?.min_latency_ms)}`}>
                    {formatLatency(diagnosticResults.summary?.min_latency_ms)}
                  </div>
                  <div className="text-xs text-gray-500">{language === 'vi' ? 'Nhanh nhất' : 'Min'}</div>
                </div>
                <div className="bg-red-50 p-3 rounded-lg text-center">
                  <div className={`text-xl font-bold ${getLatencyColor(diagnosticResults.summary?.max_latency_ms)}`}>
                    {formatLatency(diagnosticResults.summary?.max_latency_ms)}
                  </div>
                  <div className="text-xs text-gray-500">{language === 'vi' ? 'Chậm nhất' : 'Max'}</div>
                </div>
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-xl font-bold text-blue-600">
                    {diagnosticResults.summary?.successful_pings}/{diagnosticResults.summary?.total_pings}
                  </div>
                  <div className="text-xs text-gray-500">{language === 'vi' ? 'Thành công' : 'Success'}</div>
                </div>
              </div>
              
              {/* Recommendation based on results */}
              {diagnosticResults.summary?.avg_latency_ms > 5000 && (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <div className="font-semibold text-yellow-800 mb-2">
                    ⚠️ {language === 'vi' ? 'Khuyến nghị' : 'Recommendation'}
                  </div>
                  <p className="text-sm text-yellow-700">
                    {language === 'vi' 
                      ? 'Latency cao (>5s) có thể gây timeout khi xử lý file lớn. Hãy thử upload file nhỏ hơn hoặc liên hệ IT để kiểm tra kết nối mạng.'
                      : 'High latency (>5s) may cause timeouts with large files. Try uploading smaller files or contact IT to check network connection.'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Instructions when no results */}
          {!results && !diagnosticResults && !loading && !diagnosticLoading && (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                {language === 'vi' ? 'Sẵn sàng kiểm tra' : 'Ready to Test'}
              </h3>
              <p className="text-gray-500 max-w-md mx-auto">
                {language === 'vi' 
                  ? 'Nhấn nút "Chạy kiểm tra kết nối" để kiểm tra kết nối đến Google Apps Script, Document AI và các dịch vụ khác.'
                  : 'Click "Run Connectivity Test" to check connections to Google Apps Script, Document AI, and other services.'}
              </p>
              
              <div className="mt-6 text-left bg-blue-50 p-4 rounded-lg max-w-md mx-auto">
                <h4 className="font-semibold text-blue-800 mb-2">
                  {language === 'vi' ? 'Sẽ kiểm tra:' : 'Will check:'}
                </h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>✓ Google Apps Script (GDrive)</li>
                  <li>✓ AI Configuration</li>
                  <li>✓ Google Document AI</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              {language === 'vi' 
                ? 'So sánh latency giữa Preview và Production để phát hiện vấn đề'
                : 'Compare latency between Preview and Production to detect issues'}
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-gray-700 font-medium transition-colors"
            >
              {language === 'vi' ? 'Đóng' : 'Close'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectivityHealthCheck;
