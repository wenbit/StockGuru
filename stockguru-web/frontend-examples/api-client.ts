// lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
  async createScreening(params: { date: string }) {
    const response = await fetch(`${API_BASE_URL}/api/v1/screening`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return response.json();
  },
  
  async getScreeningResult(taskId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/screening/${taskId}`);
    return response.json();
  },
};
