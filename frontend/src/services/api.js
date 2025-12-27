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
  }
}

