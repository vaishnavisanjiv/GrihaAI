'use client';

import { useEffect, useState } from 'react';
import {
  FolderGit2,
  AlertTriangle,
  CheckCheck,
  Clock3,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import api from '@/lib/api';

interface Project {
  id: number;
  name: string;
  status?: string;
  score?: number;
  building_type?: string;
  jurisdiction?: string;
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [planCount, setPlanCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const [projectResponse, floorPlanResponse] = await Promise.all([
          api.get('/api/projects/'),
          api.get('/api/floor-plans/'),
        ]);
        setProjects(projectResponse.data);
        setPlanCount(floorPlanResponse.data?.length || 0);
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : 'Could not load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    loadProjects();
  }, []);

  const totalProjects = projects.length;

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-600">Overview</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">Plan review dashboard</h2>
        </div>
        <p className="text-sm text-slate-500">Uploaded plans and preliminary model review activity.</p>
      </div>

      {loadError && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Could not load data from the backend: {loadError}. Check that the API is running at http://localhost:8000, then refresh.
        </div>
      )}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-blue-100 p-3 text-blue-600">
              <FolderGit2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total projects</p>
              <h3 className="text-2xl font-bold text-slate-900">{totalProjects}</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-emerald-100 p-3 text-emerald-600">
              <CheckCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Compliance checks</p>
              <h3 className="text-2xl font-bold text-slate-900">—</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-amber-100 p-3 text-amber-600">
              <Clock3 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">In review</p>
              <h3 className="text-2xl font-bold text-slate-900">—</h3>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-red-100 p-3 text-red-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Open issues</p>
              <h3 className="text-2xl font-bold text-slate-900">—</h3>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="text-slate-900">Analysis overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span className="rounded-full bg-cyan-100 px-2.5 py-1 font-medium text-cyan-700">
                {loading ? 'Loading floor plans…' : `${planCount} floor plans uploaded`}
              </span>
            </div>
            <div className="flex h-80 items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-6 text-center text-sm text-slate-500">
              Compliance charts will appear here after floor plans have been analyzed.
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="text-slate-900">Recent projects</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {projects.slice(0, 3).map((project) => (
              <div key={project.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-base font-semibold text-slate-900">{project.name}</p>
                    <p className="text-sm text-slate-500">{project.status || 'No analysis yet'}</p>
                  </div>
                  <div className="rounded-full bg-cyan-100 px-2.5 py-1 text-xs font-semibold text-cyan-700">
                    {project.score !== undefined ? `${project.score}%` : 'Not scored'}
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                  <span>{project.building_type || 'Residential'}</span>
                  <span>{project.jurisdiction || 'Bengaluru'}</span>
                </div>
              </div>
            ))}
            {!loading && !loadError && projects.length === 0 && (
              <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
                No projects yet. Create a project to get started.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
