import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export const uploadFile = (source, file, uploadedBy = "analyst") => {
  const form = new FormData();
  form.append("source", source);
  form.append("file", file);
  form.append("uploaded_by", uploadedBy);
  return api.post("/ingest/upload/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getStats = () => api.get("/ingest/stats/");

export const getBatches = () => api.get("/ingest/batches/");

export const getRecords = (params = {}) =>
  api.get("/review/records/", { params });

export const reviewRecord = (id, payload) =>
  api.patch(`/review/records/${id}/`, payload);

export const bulkReview = (ids, status, reviewedBy = "analyst", note = "") =>
  api.post("/review/bulk/", { ids, status, reviewed_by: reviewedBy, note });

export const getAuditLogs = (params = {}) =>
  api.get("/audit/logs/", { params });

export default api;
