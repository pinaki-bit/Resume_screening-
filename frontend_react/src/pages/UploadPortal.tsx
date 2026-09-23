import React, { useState, useRef } from 'react'
import { FileUp, File, X, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { api } from '../lib/api'

export function UploadPortal() {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [results, setResults] = useState<any>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(Array.from(e.dataTransfer.files))
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files))
    }
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    let processed = 0
    let failed = 0

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        
        try {
          await api.post('/resumes/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          processed++
        } catch (err) {
          console.error(`Failed to upload ${file.name}`, err)
          failed++
        }
      }

      setResults({
        status: failed > 0 ? 'warning' : 'success',
        message: `Successfully processed ${processed} resumes. ${failed > 0 ? `${failed} failed.` : ''}`,
        processed_count: processed,
      })
      if (processed === files.length) {
         setFiles([])
      }
    } catch (error) {
      console.error('Upload process failed:', error)
      setResults({ status: 'error', message: 'Upload process failed entirely.', processed_count: 0 })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="w-full h-full flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Resume Upload Portal</h1>
          <p className="text-gray-400">Securely ingest and analyze candidate documents.</p>
        </div>
      </div>
      
      <div className="flex-1 w-full flex flex-col lg:flex-row gap-6">
        <div className="lg:w-2/3 w-full flex flex-col gap-6">
          <div 
            className={`glass-card rounded-2xl flex flex-col items-center justify-center p-12 border-2 border-dashed transition-all duration-300 ${
              isDragging ? 'border-primary bg-primary/10' : 'border-white/20'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="w-16 h-16 rounded-full bg-surface border border-white/10 flex items-center justify-center mb-6 shadow-lg shadow-black/50">
              <FileUp className={`w-8 h-8 ${isDragging ? 'text-primary' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Drag and drop resumes here</h3>
            <p className="text-gray-400 text-sm mb-6">Supports PDF format up to 10MB.</p>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="px-6 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors shadow-lg shadow-primary/20"
            >
              Browse Files
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              multiple 
              accept="application/pdf"
              onChange={handleFileSelect}
            />
          </div>

          {files.length > 0 && (
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Selected Files ({files.length})</h3>
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-surface/50 border border-white/5 group">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <File className="w-5 h-5 text-primary shrink-0" />
                      <span className="text-sm text-gray-200 truncate">{file.name}</span>
                      <span className="text-xs text-gray-500 shrink-0">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                    <button 
                      onClick={() => removeFile(index)}
                      className="p-1 rounded-md text-gray-400 hover:text-red-400 hover:bg-red-400/10 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex justify-end">
                <button 
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="px-6 py-2 bg-primary hover:bg-primary/90 disabled:bg-surface disabled:text-gray-500 text-white rounded-lg font-medium transition-colors flex items-center gap-2 shadow-lg shadow-primary/20"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <FileUp className="w-4 h-4" />
                      Upload to Pipeline
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="lg:w-1/3 w-full flex flex-col gap-6">
          <div className="glass-card rounded-2xl p-6 h-full flex flex-col">
            <h3 className="text-lg font-semibold text-white mb-4">Processing Rules</h3>
            <ul className="space-y-4 text-sm text-gray-400 flex-1">
              <li className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
                <span>Files are securely encrypted in transit and at rest.</span>
              </li>
              <li className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
                <span>Text is extracted using pdfminer.six with optional OCR fallback.</span>
              </li>
              <li className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
                <span>NLP Pipeline identifies named entities and structures sections.</span>
              </li>
              <li className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />
                <span>Duplicate uploads (based on file hash) will be skipped.</span>
              </li>
            </ul>

            {results && (
              <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex gap-3 items-start">
                <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium mb-1">{results.message}</p>
                  <p className="text-green-400/80">Analyzed {results.processed_count} documents. They are now available in the Talent Explorer.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
