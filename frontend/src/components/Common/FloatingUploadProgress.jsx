import React, { useState } from 'react';
import { X, Minimize2, Maximize2, CheckCircle, AlertCircle, Loader } from 'lucide-react';

/**
 * Floating Upload Progress Component
 * Shows upload progress in a minimizable floating box at bottom-right corner
 */
const FloatingUploadProgress = ({ 
  isVisible, 
  isMinimized, 
  onMinimize, 
  onMaximize, 
  onClose,
  uploadStatus 
}) => {
  if (!isVisible) return null;

  const { 
    totalFiles = 0, 
    completedFiles = 0, 
    currentFile = '', 
    status = 'uploading', // 'uploading', 'completed', 'error'
    errorMessage = ''
  } = uploadStatus;

  const progress = totalFiles > 0 ? Math.round((completedFiles / totalFiles) * 100) : 0;

  // Minimized view - small box at bottom-right
  if (isMinimized) {
    return (
      <div 
        className="fixed bottom-4 right-4 bg-white rounded-lg shadow-2xl border border-gray-200 p-3 cursor-pointer hover:shadow-xl transition-shadow z-50"
        onClick={onMaximize}
        style={{ width: '280px' }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {status === 'uploading' && <Loader className="w-4 h-4 text-blue-500 animate-spin" />}
            {status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
            {status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
            <span className="text-sm font-medium text-gray-700">
              {status === 'uploading' && `Uploading ${completedFiles}/${totalFiles}`}
              {status === 'completed' && 'Upload Complete'}
              {status === 'error' && 'Upload Failed'}
            </span>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        
        {/* Progress bar */}
        <div className="mt-2 bg-gray-200 rounded-full h-1.5">
          <div 
            className={`h-1.5 rounded-full transition-all duration-300 ${
              status === 'completed' ? 'bg-green-500' : 
              status === 'error' ? 'bg-red-500' : 
              'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  }

  // Expanded view - larger box with details
  return (
    <div 
      className="fixed bottom-4 right-4 bg-white rounded-lg shadow-2xl border border-gray-200 z-50"
      style={{ width: '400px' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800">
          {status === 'uploading' && '📤 Uploading Folder'}
          {status === 'completed' && '✅ Upload Complete'}
          {status === 'error' && '❌ Upload Failed'}
        </h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={onMinimize}
            className="text-gray-400 hover:text-gray-600 p-1"
            title="Minimize"
          >
            <Minimize2 className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Progress info */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span className="font-medium">{completedFiles} / {totalFiles} files</span>
          </div>
          
          {/* Progress bar */}
          <div className="bg-gray-200 rounded-full h-2.5">
            <div 
              className={`h-2.5 rounded-full transition-all duration-300 ${
                status === 'completed' ? 'bg-green-500' : 
                status === 'error' ? 'bg-red-500' : 
                'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          
          <div className="text-xs text-gray-500 mt-1 text-right">
            {progress}%
          </div>
        </div>

        {/* Current file */}
        {status === 'uploading' && currentFile && (
          <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
            <div className="flex items-center space-x-2">
              <Loader className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 mb-0.5">Currently uploading:</p>
                <p className="text-sm font-medium text-gray-700 truncate">{currentFile}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success message */}
        {status === 'completed' && (
          <div className="mb-3 p-3 bg-green-50 rounded-lg border border-green-100">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-800">
                  All files uploaded successfully!
                </p>
                <p className="text-xs text-green-600 mt-0.5">
                  {totalFiles} files uploaded to Google Drive
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {status === 'error' && errorMessage && (
          <div className="mb-3 p-3 bg-red-50 rounded-lg border border-red-100">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">Upload failed</p>
                <p className="text-xs text-red-600 mt-0.5">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action button */}
        {status === 'completed' && (
          <button
            onClick={onClose}
            className="w-full py-2 px-4 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm font-medium"
          >
            Done
          </button>
        )}
      </div>
    </div>
  );
};

export default FloatingUploadProgress;
