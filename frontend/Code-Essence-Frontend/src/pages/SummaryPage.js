import React, { useEffect, useState } from "react";
import { Box, Button, Typography, CircularProgress, Divider } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import api, { API_BASE } from "../api";
import FilePicker from "../shared/FilePicker";
import { jsPDF } from "jspdf";

export default function SummaryPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const repoUrl = location.state?.repoUrl || "";
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [level, setLevel] = useState("repo"); // repo | folder | file
  const [selectedFile, setSelectedFile] = useState("");
  const [showFilePicker, setShowFilePicker] = useState(false);

  useEffect(() => {
    document.body.style.backgroundColor = "#000";
  }, []);

  const fetchSummary = async (targetLevel = "repo", fileName = "") => {
    if (!repoUrl) return alert("No repo URL provided.");
    setLoading(true);
    setLevel(targetLevel);
    setSelectedFile(fileName);

    try {
      if (targetLevel === "file") {
        const resp = await api.post("/summarize_file", {
          repo_url: repoUrl,
          file_name: fileName,
        });
        setSummary(resp.data.summary || "No summary");
      } else {
        const resp = await api.post("/summarize_repo", {
          repo_url: repoUrl,
          level: targetLevel === "repo" ? "repo" : "folder",
        });
        // backend returns a dict of summaries for folder/repo; normalize it
        if (targetLevel === "repo") {
          const repoSummary = resp.data?.repo_summary ?? resp.data?.summary ?? resp.data;
          setSummary(typeof repoSummary === "string" ? repoSummary : JSON.stringify(repoSummary, null, 2));
        } else {
          setSummary(JSON.stringify(resp.data, null, 2));
        }
      }
    } catch (err) {
      console.error(err);
      setSummary("Error fetching summary: " + (err?.message || err));
    } finally {
      setLoading(false);
    }
  };

  const handlePush = async () => {
    if (!repoUrl) return alert("No repo URL.");
    try {
      await api.post("/push_summary", { repo_url: repoUrl, branch: "main" });
      alert("Push request sent (check backend logs).");
    } catch (err) {
      console.error(err);
      alert("Push failed: " + err.message);
    }
  };

  const savePDF = () => {
    const doc = new jsPDF();
    const lines = typeof summary === "string" ? summary.split("\n") : JSON.stringify(summary, null, 2).split("\n");
    let y = 10;
    const pageHeight = doc.internal.pageSize.height;
    lines.forEach((line) => {
      doc.text(String(line), 10, y);
      y += 7;
      if (y > pageHeight - 10) {
        doc.addPage();
        y = 10;
      }
    });
    doc.save("summary.pdf");
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", backgroundColor: "black", color: "white" }}>
      {/* Sidebar */}
      <Box sx={{ width: 240, backgroundColor: "#111", p: 2, display: "flex", flexDirection: "column", gap: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: "900", color: "limegreen" }}>
          Summaries
        </Typography>

        <Button variant="contained" onClick={() => fetchSummary("repo")} sx={{ backgroundColor: "limegreen", color: "black", fontWeight: "bold" }}>
          Project
        </Button>

        <Button variant="contained" onClick={() => fetchSummary("folder")} sx={{ backgroundColor: "green", color: "white" }}>
          Folder
        </Button>

        <Button variant="contained" onClick={() => setShowFilePicker(true)} sx={{ backgroundColor: "#2e7d32", color: "white" }}>
          Select File
        </Button>

        <Divider sx={{ bgcolor: "#333", my: 1 }} />

        <Button variant="contained" onClick={handlePush} sx={{ backgroundColor: "#0d47a1", color: "white" }}>
          Push Summary
        </Button>

        <Button variant="contained" onClick={savePDF} sx={{ backgroundColor: "#f9a825", color: "black" }}>
          Save PDF
        </Button>

        <Button variant="outlined" onClick={() => navigate("/")} sx={{ color: "white", borderColor: "#444" }}>
          Back Home
        </Button>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: "bold", mb: 2 }}>
          {selectedFile ? `File: ${selectedFile}` : "Project / Folder Summary"}
        </Typography>

        <Box sx={{ backgroundColor: "#222", p: 2, borderRadius: 1, minHeight: 300 }}>
          {loading ? <CircularProgress color="inherit" /> : <pre style={{ whiteSpace: "pre-wrap", color: "#e0f2f1" }}>{summary || "No summary yet. Click a button."}</pre>}
        </Box>
      </Box>

      {/* File Picker Modal */}
      {showFilePicker && (
        <FilePicker
          repoUrl={repoUrl}
          onClose={() => setShowFilePicker(false)}
          onPick={async (file) => {
            setShowFilePicker(false);
            await fetchSummary("file", file);
          }}
        />
      )}
    </Box>
  );
}
