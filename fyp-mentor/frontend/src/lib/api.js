const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status}: ${body}`)
  }
  return res.json()
}

export const api = {
  // Projects list + management
  listProjects: () => request('/projects'),
  deleteProject: (id) => request(`/projects/${id}`, { method: 'DELETE' }),
  approveProject: (id) => request(`/projects/${id}/approve`, { method: 'POST' }),

  // Project pipeline
  createProject: (data) => request('/projects', { method: 'POST', body: JSON.stringify(data) }),
  selectIdea: (project_id, idea_index) =>
    request('/projects/select-idea', { method: 'POST', body: JSON.stringify({ project_id, idea_index }) }),
  getProject: (id) => request(`/projects/${id}`),

  // Tasks
  getTasks: (id) => request(`/projects/${id}/tasks`),
  updateTask: (id, status) => request(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify({ task_id: id, status }) }),

  // Risk, mentor, roadmap
  getRisk: (id) => request(`/projects/${id}/risk`),
  getMentor: (id) => request(`/projects/${id}/mentor`),
  regenerateRoadmap: (id) => request(`/projects/${id}/roadmap/regenerate`, { method: 'POST' }),
  replan: (id) => request(`/projects/${id}/replan`, { method: 'POST' }),
}