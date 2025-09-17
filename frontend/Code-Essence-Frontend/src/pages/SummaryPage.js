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
  const [expandedFolders, setExpandedFolders] = useState({});

  useEffect(() => {
    document.body.style.backgroundColor = "#000";
  }, []);

  const toggleFolder = (folder) => {
    setExpandedFolders((prev) => ({ ...prev, [folder]: !prev[folder] }));
  };


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
  const pageHeight = doc.internal.pageSize.height;
  const pageWidth = doc.internal.pageSize.width;

  // normalize summary into string
  const text = typeof summary === "string" 
    ? summary 
    : JSON.stringify(summary, null, 2);

  // split text into wrapped lines that fit the page width
  const lines = doc.splitTextToSize(text, pageWidth - 20);

  let y = 10;
  lines.forEach((line) => {
    doc.text(line, 10, y);
    y += 7;
    if (y > pageHeight - 10) {
      doc.addPage();
      y = 10;
    }
  });

  doc.save("summary.pdf");
};

const renderSummary = (data, level = 0) => {
  if (!data) return null;

  // If it's a plain string, just show it nicely
  if (typeof data === "string") {
    const cleaned = data
      .replace(/\n+/g, " ")   // remove line breaks
      .replace(/\t+/g, " ")   // remove tabs
      .replace(/\s\s+/g, " "); // collapse extra spaces

    return (
      <Typography sx={{ ml: level * 2, mb: 1, color: "#e0f2f1", lineHeight: 1.6 }}>
        {cleaned}
      </Typography>
    );
  }

  // If it's an object, iterate through keys
  return Object.entries(data).map(([key, value], idx) => {
    const cleaned =
      typeof value === "string"
        ? value.replace(/\n+/g, " ").replace(/\t+/g, " ").replace(/\s\s+/g, " ")
        : null;

    return (
      <Box key={idx} sx={{ ml: level * 2, mb: 1 }}>
        <Typography sx={{ fontWeight: "bold", color: "limegreen" }}>
          {key}:
        </Typography>

        {cleaned ? (
          <Typography sx={{ ml: 2, color: "#e0f2f1", lineHeight: 1.6 }}>
            {cleaned}
          </Typography>
        ) : (
          <Box sx={{ backgroundColor: "#222", p: 2, borderRadius: 1, minHeight: 300 }}>
  {loading ? (
    <CircularProgress color="inherit" />
  ) : typeof summary === "string" ? (
    <Typography sx={{ whiteSpace: "pre-wrap", color: "#e0f2f1" }}>
      {summary}
    </Typography>
  ) : (
    renderSummary(summary)
  )}
</Box>

        )}
      </Box>
    );
  });
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

        
        <Button variant="contained" onClick={savePDF} sx={{ backgroundColor: "#2cb555ff", color: "black" }}>
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
       
      </Box>
      <Box sx={{ backgroundColor: "#222", p: 2, borderRadius: 1, minHeight: 300 }}>
        {loading ? (
          <CircularProgress color="inherit" />
        ) : summary && typeof summary === "object" && summary.summaries ? (
          <SummaryTree data={summary.summaries} />
        ) : (   
          <Typography sx={{ whiteSpace: "pre-wrap", color: "#e0f2f1" }}>
            {summary || "No summary yet. Click a button."}
          </Typography>   
        )}
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
