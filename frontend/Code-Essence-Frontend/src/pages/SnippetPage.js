import React, { useEffect, useState } from "react";
import { Box, Button, TextField, MenuItem, Typography, CircularProgress } from "@mui/material";
import api from "../api";

const LANGS = [
  { value: "py", label: "Python" },
  { value: "js", label: "JavaScript" },
  { value: "java", label: "Java" },
  { value: "sql", label: "SQL" },
  { value: "ts", label: "TypeScript" },
];

export default function SnippetPage() {
  const [code, setCode] = useState("");
  const [lang, setLang] = useState("py");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");

  useEffect(() => {
    document.body.style.backgroundColor = "#000";
  }, []);

  const sendSnippet = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setSummary("");
    try {
      const resp = await api.post("/summarize_snippet", { code, language: lang });
      setSummary(resp.data.summary || "No summary returned");
    } catch (err) {
      console.error(err);
      setSummary("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 4, backgroundColor: "black", minHeight: "100vh", color: "white" }}>
      <Typography variant="h4" sx={{ color: "limegreen", fontWeight: "bold", mb: 2 }}>Snippet Summary</Typography>

      <TextField
        select
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        sx={{ mb: 2, background: "#111", width: 160 }}
      >
        {LANGS.map((l) => <MenuItem key={l.value} value={l.value}>{l.label}</MenuItem>)}
      </TextField>

      <TextField
        multiline
        rows={12}
        placeholder="Paste code here..."
        value={code}
        onChange={(e) => setCode(e.target.value)}
        fullWidth
        sx={{ background: "#111", mb: 2 }}
        InputProps={{ style: { color: "white" } }}
      />

      <Box sx={{ display: "flex", gap: 2 }}>
        <Button variant="contained" onClick={sendSnippet} sx={{ backgroundColor: "limegreen", color: "black" }}>
          Summarize
        </Button>
        <Button variant="outlined" onClick={() => { setCode(""); setSummary(""); }}>Clear</Button>
      </Box>

      <Box sx={{ mt: 3 }}>
        {loading ? <CircularProgress /> : <pre style={{ color: "#e0f2f1", whiteSpace: "pre-wrap" }}>{summary}</pre>}
      </Box>
    </Box>
  );
}
