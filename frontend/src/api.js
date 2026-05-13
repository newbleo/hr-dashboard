import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? ''
const api = axios.create({ baseURL: `${BASE}/api` })

export const getJobs = (params) => api.get('/jobs', { params })
export const getStats = () => api.get('/stats')
export const triggerCollect = () => api.post('/collect')
