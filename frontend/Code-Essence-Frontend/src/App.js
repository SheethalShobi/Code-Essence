import React from "react";
import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SummaryPage from "./pages/SummaryPage";
import HealthPage from "./pages/HealthPage";
import SnippetPage from "./pages/SnippetPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import DependencyGraph from "./pages/DependencyGraph";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/summary" element={<SummaryPage />} />
      <Route path="/health" element={<HealthPage />} />
      <Route path="/snippet" element={<SnippetPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/dependency-graph" element={<DependencyGraph />} />
    </Routes>
  );
}

export default App;
