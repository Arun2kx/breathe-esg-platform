import { Toaster } from "react-hot-toast";
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/ui/Layout";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import ReviewPage from "./pages/ReviewPage";
import AuditPage from "./pages/AuditPage";

export default function App() {
  return (
    <>
    <Toaster position="top-right" />
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="review" element={<ReviewPage />} />
          <Route path="audit" element={<AuditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </>
  );
}
