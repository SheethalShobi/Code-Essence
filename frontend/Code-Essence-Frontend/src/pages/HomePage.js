import React, { useState, useEffect } from "react";
import { Box, Typography, TextField, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    document.body.style.backgroundColor = "#000";
    document.body.style.color = "#fff";
  }, []);

  const goSummary = () => {
    if (!repoUrl.trim()) return;
    navigate("/summary", { state: { repoUrl } });
  };

  const goHealth = () => {
    if (!repoUrl.trim()) return;
    navigate("/health", { state: { repoUrl } });
  };

  const goSnippet = () => {
    navigate("/snippet");
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        backgroundColor: "black",
        color: "white",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        p: 3,
      }}
    >
      <Typography variant="h3" sx={{ fontWeight: "900", mb: 2, textAlign: "center" }}>
        <span style={{ color: "white" }}>Code</span>{" "}
        <span style={{ color: "limegreen" }}>Essence</span>
      </Typography>

      <Typography variant="h5" sx={{ fontWeight: "bold", mb: 3, textAlign: "center" }}>
        Summarize any Github Repositories
      </Typography>

      <TextField
        placeholder="https://github.com/owner/repo"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        fullWidth
        sx={{
          maxWidth: 700,
          mb: 2,
          "& .MuiOutlinedInput-root": {
            backgroundColor: "#111",
            borderRadius: "10px",
          },
          "& input": { color: "white" },
        }}
      />

      <Box sx={{ display: "flex", gap: 2, mt: 1 }}>
        <Button
          onClick={goSummary}
          variant="contained"
          sx={{ backgroundColor: "limegreen", color: "black", fontWeight: "bold" }}
        >
          Summarize
        </Button>

        <Button
          onClick={goHealth}
          variant="contained"
          sx={{ backgroundColor: "#2e7d32", color: "white", fontWeight: "bold" }}
        >
          Health Check
        </Button>

        <Button
          onClick={goSnippet}
          variant="contained"
          sx={{ backgroundColor: "#4caf50", color: "black", fontWeight: "bold" }}
        >
          Snippet Summary
        </Button>
      </Box>

      <Box sx={{ position: "absolute", top: 16, right: 16 }}>
        <Button
          variant="contained"
          onClick={() => window.location.href = "http://localhost:5000/login"}
          sx={{ backgroundColor: "green", color: "white", fontWeight: "bold" }}
        >
          Login
        </Button>
      </Box>
    </Box>
  );
}
