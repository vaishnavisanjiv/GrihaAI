'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAxiosError } from 'axios';
import { UploadCloud, FileImage, CheckCircle2, AlertCircle, Sparkles, Download, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';

type Project = { id: number; name: string };
type FloorPlanSummary = {
  id: number;
  original_filename: string;
  status: string;
  file_type?: string | null;
};

const SAMPLE_PLANS = [
  {
    name: '01_large_architectural_villa.png',
    title: 'Architectural Villa Plan',
    desc: 'Large multi-zone residential villa with multiple bedrooms, bathrooms, and living spaces.',
    url: '/samples/01_large_architectural_villa.png',
    size: '223 KB',
  },
  {
    name: '02_compact_residential_apartment.png',
    title: 'Compact 1-BHK Apartment',
    desc: 'Studio / 1-BHK compact layout with kitchen, living area, and attached bath.',
    url: '/samples/02_compact_residential_apartment.png',
    size: '30 KB',
  },
  {
    name: '03_modern_family_home.png',
    title: 'Modern Family Home',
    desc: 'Single-family house plan with kitchen, dining, multiple rooms and hallways.',
    url: '/samples/03_modern_family_home.png',
    size: '98 KB',
  },
  {
    name: '04_multi_room_duplex.png',
    title: 'Multi-Room Duplex Unit',
    desc: 'Detailed architectural drawing with partitions, structural walls, and entries.',
    url: '/samples/04_multi_room_duplex.png',
    size: '109 KB',
  },
  {
    name: '05_two_bedroom_flat.png',
    title: 'Two-Bedroom Urban Flat',
    desc: '2-BHK floor plan with distinct room boundaries, balconies, and corridors.',
    url: '/samples/05_two_bedroom_flat.png',
    size: '137 KB',
  },
];

export default function UploadPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | ''>('');
  const [file, setFile] = useState<File | null>(null);
  const [uploadedPlans, setUploadedPlans] = useState<FloorPlanSummary[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [analyzingPlanId, setAnalyzingPlanId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>('');
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const initialize = async () => {
      try {
        const response = await api.get<Project[]>('/api/projects/');
        if (!isMounted) return;
        setProjects(response.data);
        if (response.data.length) setSelectedProjectId(response.data[0].id);
      } catch {
        if (!isMounted) return;
        setProjects([]);
        setHasError(true);
        setStatus('Unable to load projects. Check that the backend is running and you are signed in.');
      }

      try {
        const response = await api.get<FloorPlanSummary[]>('/api/floor-plans/');
        if (isMounted) setUploadedPlans(response.data);
      } catch {
        if (isMounted) setUploadedPlans([]);
      }
    };

    void initialize();
    return () => {
      isMounted = false;
    };
  }, []);

  const [isLoadingSample, setIsLoadingSample] = useState(false);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const chosenFile = event.target.files?.[0] ?? null;
    setFile(chosenFile);
  };

  const loadSampleFile = async (sampleUrl: string, sampleFilename: string) => {
    setIsLoadingSample(true);
    setStatus('Loading sample floor plan...');
    setHasError(false);
    try {
      const res = await fetch(sampleUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const loadedFile = new File([blob], sampleFilename, { type: blob.type || 'image/png' });
      setFile(loadedFile);
      setStatus(`Loaded sample "${sampleFilename}". Click "Upload and analyze" above to run the trained model.`);
    } catch (err: unknown) {
      setHasError(true);
      setStatus(`Failed to load sample: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoadingSample(false);
    }
  };

  const startAnalysis = async (planId: number) => {
    setAnalyzingPlanId(planId);
    setStatus('');
    setHasError(false);
    try {
      const response = await api.post<{ id: number }>(`/api/analysis/${planId}/start`);
      router.push(`/analysis/${response.data.id}`);
    } catch (error: unknown) {
      const detail = isAxiosError<{ detail?: string }>(error)
        ? error.response?.data?.detail || error.message
        : error instanceof Error
          ? error.message
          : 'Unexpected error.';
      setHasError(true);
      setStatus(`Floor plan ${planId} is uploaded, but analysis failed: ${detail}`);
    } finally {
      setAnalyzingPlanId(null);
    }
  };

  const handleUpload = async () => {
    if (!file || !selectedProjectId) {
      setStatus('Please select a project and a floor plan file.');
      return;
    }

    setIsUploading(true);
    setStatus('');
    setHasError(false);

    const formData = new FormData();
    formData.append('project_id', String(selectedProjectId));
    formData.append('file', file);

    try {
      const response = await api.post<{ id: number; filename: string }>('/api/floor-plans/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const planId = response.data.id;
      setUploadedPlans((plans) => [
        {
          id: planId,
          original_filename: response.data.filename,
          status: 'UPLOADED',
          file_type: file.name.split('.').pop()?.toUpperCase(),
        },
        ...plans,
      ]);
      await startAnalysis(planId);
    } catch (error: unknown) {
      const detail = isAxiosError<{ detail?: string }>(error)
        ? error.response?.data?.detail || error.message
        : error instanceof Error
          ? error.message
          : 'Unexpected error.';
      setHasError(true);
      setStatus(`Floor plan upload failed: ${detail}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-600">Layout upload</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Upload floor plan for review</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <UploadCloud className="h-5 w-5 text-cyan-600" />
              Select files
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Project</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-cyan-100 text-cyan-700">
                <FileImage className="h-7 w-7" />
              </div>
              <p className="text-lg font-semibold text-slate-800">Drop a floor plan here</p>
              <p className="mt-1 text-sm text-slate-500">PNG, JPG, or PDF export</p>

              <label className="mt-6 inline-flex cursor-pointer rounded-full bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
                Choose file
                <input type="file" className="hidden" onChange={handleFileChange} />
              </label>

              {file && (
                <div className="mt-4 text-sm text-slate-700">
                  Selected: <span className="font-medium">{file.name}</span>
                </div>
              )}
            </div>

            <Button onClick={handleUpload} className="w-full" disabled={isUploading || !file}>
              {isUploading ? 'Uploading...' : 'Upload and analyze'}
            </Button>

            {status && (
              <div className={`flex items-start gap-2 rounded-xl border p-3 text-sm ${
                hasError
                  ? 'border-rose-200 bg-rose-50 text-rose-700'
                  : 'border-emerald-200 bg-emerald-50 text-emerald-700'
              }`}>
                {hasError
                  ? <AlertCircle className="mt-0.5 h-4 w-4" />
                  : <CheckCircle2 className="mt-0.5 h-4 w-4" />}
                <span>{status}</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <Sparkles className="h-5 w-5 text-cyan-600" />
              Processing queue
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {uploadedPlans.length ? (
              uploadedPlans.map((plan) => (
                <div key={plan.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-800">{plan.original_filename}</p>
                      <p className="text-xs text-slate-500">{plan.status}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-emerald-700">
                        {plan.file_type || 'file'}
                      </span>
                      <Button
                        type="button"
                        onClick={() => void startAnalysis(plan.id)}
                        disabled={isUploading || analyzingPlanId !== null}
                        className="px-3 py-1 text-xs"
                      >
                        {analyzingPlanId === plan.id ? 'Analyzing...' : 'Analyze / retry'}
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                No uploaded plans yet.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-200 bg-white">
        <CardHeader>
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <FileImage className="h-5 w-5 text-cyan-600" />
                Sample Test Floor Plans (Held-Out Test Set)
              </CardTitle>
              <p className="mt-1 text-sm text-slate-500">
                Download verified real architectural layouts or click &quot;Select for Test&quot; to load directly into the analysis pipeline.
              </p>
            </div>
            <span className="inline-flex items-center rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700 border border-cyan-200">
              CubiCasa5K Evaluation Samples
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {SAMPLE_PLANS.map((sample) => (
              <div
                key={sample.name}
                className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/70 p-4 transition-all hover:border-cyan-300 hover:bg-slate-50 hover:shadow-sm"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-slate-900 text-sm">{sample.title}</h3>
                    <span className="text-[11px] font-mono text-slate-400 shrink-0">{sample.size}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-600 leading-relaxed line-clamp-2">
                    {sample.desc}
                  </p>
                  <p className="mt-2 text-[11px] font-mono text-slate-400 truncate">
                    {sample.name}
                  </p>
                </div>

                <div className="mt-4 flex items-center gap-2 pt-2 border-t border-slate-200/80">
                  <Button
                    type="button"
                    size="sm"
                    disabled={isLoadingSample || isUploading}
                    onClick={() => void loadSampleFile(sample.url, sample.name)}
                    className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white text-xs h-8"
                  >
                    Select for Test
                    <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                  </Button>
                  <a
                    href={sample.url}
                    download={sample.name}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-2.5 h-8 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                    title="Download plan image file"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
