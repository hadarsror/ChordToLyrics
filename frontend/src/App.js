import React, { useState, useEffect } from 'react';
import { Upload, Music, CheckCircle, Loader2, AlertCircle, Copy } from 'lucide-react';

const API_BASE = "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState('IDLE');
  const [result, setResult] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let interval;
    if (status === 'PROCESSING' && taskId) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/status/${taskId}`);
          const data = await res.json();

          if (data.status === 'SUCCESS' || data.status === 'COMPLETED') {
            setResult(data.result);
            setStatus('SUCCESS');
            clearInterval(interval);
          } else if (data.status === 'FAILURE') {
            setError(data.result || 'AI Processing failed');
            setStatus('ERROR');
            clearInterval(interval);
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [status, taskId]);

  const handleUpload = async () => {
    if (!file) return;
    setStatus('UPLOADING');
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
      const data = await res.json();
      setTaskId(data.task_id);
      setStatus('PROCESSING');
    } catch (e) {
      setError('Could not connect to backend. Ensure FastAPI is running on port 8000.');
      setStatus('ERROR');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-12 font-sans">
      <div className="max-w-3xl mx-auto">
        <header className="flex items-center gap-4 mb-12 border-b border-slate-700 pb-6">
          <div className="p-3 bg-blue-600 rounded-lg"><Music size={32} /></div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Chord Aligner AI</h1>
            <p className="text-slate-400">Audio to Lead Sheet Alignment</p>
          </div>
        </header>

        <div className="bg-slate-800 border-2 border-dashed border-slate-600 rounded-xl p-10 text-center mb-8">
          <input type="file" accept="audio/*" className="hidden" id="audio-upload" onChange={(e) => setFile(e.target.files[0])} />
          <label htmlFor="audio-upload" className="cursor-pointer group">
            <Upload className="mx-auto mb-4 text-slate-500 group-hover:text-blue-400 transition-colors" size={48} />
            <span className="text-lg font-medium block mb-2">{file ? file.name : "Select Audio File"}</span>
          </label>
          <button onClick={handleUpload} disabled={!file || status === 'PROCESSING'} className="mt-8 px-8 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded-full font-bold transition-all flex items-center gap-2 mx-auto">
            {status === 'PROCESSING' && <Loader2 className="animate-spin" size={20} />}
            {status === 'PROCESSING' ? 'Processing...' : 'Generate Sheet'}
          </button>
        </div>

        {status === 'SUCCESS' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
             <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold flex items-center gap-2"><CheckCircle className="text-green-500" /> Result</h2>
                <button onClick={() => navigator.clipboard.writeText(result)} className="p-2 hover:bg-slate-700 rounded"><Copy size={18} /></button>
             </div>
             <pre className="bg-slate-950 p-6 rounded-lg border border-slate-700 text-blue-300 font-mono whitespace-pre-wrap">{result}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
export default App;