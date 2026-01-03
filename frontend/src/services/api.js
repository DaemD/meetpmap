import axios from 'axios'

// Use Railway URL in production, localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://meetpmap-production.up.railway.app'

export const api = {
  async processTranscript(chunk, userId = null) {
    // Add user_id to chunk if provided
    const chunkWithUser = userId ? { ...chunk, user_id: userId } : chunk
    const response = await axios.post(`${API_BASE_URL}/api/transcript`, chunkWithUser)
    return response.data
  },

  async batchProcess(chunks) {
    const response = await axios.post(`${API_BASE_URL}/api/batch-process`, chunks)
    return response.data
  },

  async getDownwardPath(nodeId) {
    const response = await axios.get(`${API_BASE_URL}/api/graph/path/down/${nodeId}`)
    return response.data
  },

  async getUpwardPath(nodeId) {
    const response = await axios.get(`${API_BASE_URL}/api/graph/path/up/${nodeId}`)
    return response.data
  },

  async getMaturity(nodeId) {
    const response = await axios.get(`${API_BASE_URL}/api/graph/maturity/${nodeId}`)
    return response.data
  },

  async getInfluence(nodeId) {
    const response = await axios.get(`${API_BASE_URL}/api/graph/influence/${nodeId}`)
    return response.data
  },

  async getGraphState(userId = null) {
    const params = userId ? { user_id: userId } : {}
    const response = await axios.get(`${API_BASE_URL}/api/graph/state`, { params })
    return response.data
  }
}

