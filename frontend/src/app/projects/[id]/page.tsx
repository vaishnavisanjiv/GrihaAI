'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Building2, FileText, MapPinned, PlusCircle, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';

interface Project {
  id: number;
  name: string;
  description?: string | null;
  building_type?: string | null;
  jurisdiction?: string | null;
}

interface FloorPlan {
  id: number;
  project_id: number;
  original_filename: string;
  status: string;
}

interface ProjectSummary {
  plan_count: number;
  analysis_count: number;
  not_assessed_count: number;
}

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [plans, setPlans] = useState<FloorPlan[]>([]);
  const [summary, setSummary] = useState<ProjectSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingAnalysis, setStartingAnalysis] = useState<number | null>(null);
  const [loadError, setLoadError] = useState('');
  const [startError, setStartError] = useState('');

  useEffect(() => {
    const loadProjectData = async () => {
      const projectId = params.id;

      try {
        const [projectResponse, floorPlanResponse, summaryResponse] = await Promise.all([
          api.get<Project>(`/api/projects/${projectId}`),
          api.get<FloorPlan[]>('/api/floor-plans/'),
          api.get<ProjectSummary>(`/api/projects/${projectId}/summary`),
        ]);

        const projectData = projectResponse.data;
        const projectPlans = floorPlanResponse.data.filter(
          (plan) => String(plan.project_id) === projectId,
        );

        setProject(projectData);
        setPlans(projectPlans);
        setSummary(summaryResponse.data);
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : 'Could not load project details.');
      } finally {
        setLoading(false);
      }
    };

    loadProjectData();
  }, [params]);

  const startReview = async (floorPlanId: number) => {
    setStartingAnalysis(floorPlanId);
    setStartError('');
    try {
      const response = await api.post<{ id: number }>(`/api/analysis/${floorPlanId}/start`);
      router.push(`/analysis/${response.data.id}`);
    } catch (error) {
      setStartError(error instanceof Error ? error.message : 'Could not start plan review.');
    } finally {
      setStartingAnalysis(null);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-600">Loading project workspace...</div>;
  }

  if (!project) {
    return <div role="alert" className="p-8 text-red-700">{loadError || 'Project not found.'}</div>;
  }

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => router.push('/projects')}
            className="rounded-full border border-slate-200 bg-white p-2 text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-600">Project</p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">{project.name}</h1>
          </div>
        </div>
        <Button onClick={() => router.push('/upload')} className="inline-flex items-center gap-2">
          <PlusCircle className="h-4 w-4" />
          Upload plan
        </Button>
      </div>

      <div className="grid gap-5 md:grid-cols-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-cyan-100 p-3 text-cyan-700">
              <Building2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Building type</p>
              <h3 className="text-xl font-bold text-slate-900">{project.building_type || 'General'}</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-emerald-100 p-3 text-emerald-700">
              <MapPinned className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Jurisdiction</p>
              <h3 className="text-xl font-bold text-slate-900">{project.jurisdiction || 'Not set'}</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-amber-100 p-3 text-amber-700">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Floor plans</p>
              <h3 className="text-xl font-bold text-slate-900">{summary?.plan_count ?? plans.length}</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-violet-100 p-3 text-violet-700">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Assessment status</p>
              <h3 className="text-sm font-bold text-slate-900">Preliminary only</h3>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-200 bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-900">
            <Sparkles className="h-5 w-5 text-cyan-600" />
            Project overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-base leading-7 text-slate-600">{project.description || 'No project description available yet.'}</p>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        {startError && (
          <div role="alert" className="lg:col-span-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {startError}
          </div>
        )}
        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="text-slate-900">Uploaded plans</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {plans.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
                No floor plans uploaded yet for this project.
              </div>
            ) : (
              plans.map((plan) => (
                <div key={plan.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-base font-semibold text-slate-900">{plan.original_filename || `Plan ${plan.id}`}</p>
                    <p className="mt-1 text-sm text-slate-500">Status: {plan.status || 'READY'}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
                      {plan.status || 'READY'}
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => startReview(plan.id)}
                      disabled={startingAnalysis === plan.id}
                    >
                      {startingAnalysis === plan.id ? 'Starting...' : 'Start review'}
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="text-slate-900">Review summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Code assessment</p>
              <p className="mt-2 text-lg font-bold text-slate-900">Not assessed</p>
              <p className="mt-1 text-sm text-slate-600">No verified local rule catalog is configured.</p>
            </div>
            <div className="space-y-2 text-sm text-slate-600">
              <p>Code checks not assessed: {summary?.not_assessed_count ?? 0}</p>
              <p>Preliminary analyses: {summary?.analysis_count ?? 0}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
