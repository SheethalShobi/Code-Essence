import React, { useEffect, useState } from "react";
import { Box, Button, Typography, CircularProgress } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../api";

export default function HealthPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const repoUrl = location.state?.repoUrl || "";
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);

  useEffect(() => {
    document.body.style.backgroundColor = "#000";
  }, []);

  const getHealth = async () => {
    if (!repoUrl) return alert("Repo URL required");
    setLoading(true);
    try {
      const resp = await api.post("/health_check", { repo_url: repoUrl });
      setReport(resp.data);
    } catch (err) {
      console.error(err);
      setReport({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", backgroundColor: "black", color: "white", p: 4 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: "bold", color: "limegreen" }}>Repo Health</Typography>
        <Button variant="outlined" onClick={() => navigate("/")}>Back</Button>
      </Box>

      <Button variant="contained" onClick={getHealth} sx={{ mb: 2, backgroundColor: "green" }}>
        Run Health Check
      </Button>

      {loading ? (
        <CircularProgress />
      ) : report ? (
        <pre style={{ whiteSpace: "pre-wrap", color: "#e0f2f1" }}>{JSON.stringify(report, null, 2)}</pre>
      ) : (
        <Typography>No report yet</Typography>
      )}
    </Box>
  );
}
