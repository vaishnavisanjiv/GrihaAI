'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { FolderPlus, Search, MapPinned, Building2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';

interface Project {
  id: number;
  name: string;
  description?: string;
  building_type?: string;
  jurisdiction?: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadError, setLoadError] = useState('');
  const [createError, setCreateError] = useState('');
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [query, setQuery] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [buildingType, setBuildingType] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await api.get('/api/projects/');
        setProjects(response.data);
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : 'Could not load projects.');
      } finally {
        setLoadingProjects(false);
      }
    };

    loadProjects();
  }, []);

  const filteredProjects = projects.filter((project) => {
    const search = query.toLowerCase();
    return (
      project.name.toLowerCase().includes(search) ||
      project.description?.toLowerCase().includes(search) ||
      project.jurisdiction?.toLowerCase().includes(search)
    );
  });

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setCreateError('');

    const payload = {
      name,
      description,
      building_type: buildingType,
      jurisdiction,
    };

    try {
      const response = await api.post('/api/projects/', payload);
      setProjects((current) => [response.data, ...current]);
      setName('');
      setDescription('');
      setBuildingType('');
      setJurisdiction('');
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : 'Could not create the project.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6 md:p-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-600">Projects</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">Your plan review workspace</h1>
        </div>
        <div className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600">
          {projects.length} active projects
        </div>
      </div>

      {loadError && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Could not load projects from the backend: {loadError}. Check that the API is running at http://localhost:8000, then refresh.
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <FolderPlus className="h-5 w-5 text-cyan-600" />
              Project library
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="Search by project, location or type"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="border-slate-200 pl-9"
              />
            </div>

            <div className="space-y-4">
              {loadingProjects && <p className="text-sm text-slate-500">Loading projects…</p>}
              {filteredProjects.map((project) => (
                <Link key={project.id} href={`/projects/${project.id}`} className="block">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 transition hover:border-slate-300 hover:bg-white">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900">{project.name}</h3>
                        <p className="mt-1 text-sm text-slate-600">{project.description || 'No description provided'}</p>
                      </div>
                      <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
                        {project.building_type || 'General'}
                      </span>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-500">
                      <span className="inline-flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        {project.building_type || 'Unknown category'}
                      </span>
                      <span className="inline-flex items-center gap-2">
                        <MapPinned className="h-4 w-4" />
                        {project.jurisdiction || 'Location not set'}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
              {!loadingProjects && !loadError && filteredProjects.length === 0 && (
                <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
                  {query ? 'No projects match your search.' : 'No projects yet. Create one to get started.'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader>
            <CardTitle className="text-slate-900">New project</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <Input
                label="Project name"
                placeholder="e.g. Riverside Apartments"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <Input
                label="Jurisdiction"
                placeholder="e.g. PMC, Pune or PCMC, Pimpri-Chinchwad"
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                required
              />
              <Input
                label="Building type"
                placeholder="e.g. Commercial office or retail"
                value={buildingType}
                onChange={(e) => setBuildingType(e.target.value)}
              />
              <label className="block text-sm font-medium text-slate-700">Description</label>
              <textarea
                className="min-h-28 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-cyan-500 focus:outline-none"
                placeholder="Brief project summary for the verification team"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              {createError && (
                <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                  Could not create project: {createError}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating project...' : 'Create project'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
