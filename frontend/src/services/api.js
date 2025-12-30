import axios from 'axios'

const API_BASE_URL = 'http://localhost:8001'

export const api = {
  async processTranscript(chunk) {
    const response = await axios.post(`${API_BASE_URL}/api/transcript`, chunk)
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

  async getGraphState() {
    const response = await axios.get(`${API_BASE_URL}/api/graph/state`)
    return response.data
  }
}

