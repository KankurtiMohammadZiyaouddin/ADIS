const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) 
  ? import.meta.env.VITE_API_URL 
  : 'http://localhost:8000';

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    if (!response.ok) {
      return { online: false, data: null };
    }
    const data = await response.json();
    return { online: true, data };
  } catch (error) {
    return { online: false, data: null, error: error.message };
  }
}

export async function predictDeepfakeImage(file, detector = 'all') {
  if (!file) {
    throw new Error("No image file provided.");
  }

  const formData = new FormData();
  formData.append('image', file);
  formData.append('detector', detector);

  const response = await fetch(`${API_BASE_URL}/api/predict`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();

  if (!response.ok || data.success === false) {
    throw new Error(data.detail || data.error || data.message || "Image analysis failed.");
  }

  return data;
}

export function getHeatmapFullUrl(heatmapUrl) {
  if (!heatmapUrl) return null;
  if (heatmapUrl.startsWith('http://') || heatmapUrl.startsWith('https://')) {
    return heatmapUrl;
  }
  return `${API_BASE_URL}${heatmapUrl}`;
}
