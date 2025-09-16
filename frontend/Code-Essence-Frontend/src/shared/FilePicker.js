import React, { useEffect, useState } from "react";
import { Box, Button, Dialog, DialogTitle, DialogContent, List, ListItem, ListItemButton, ListItemText, CircularProgress } from "@mui/material";
import api from "../api";

export default function FilePicker({ repoUrl, onClose, onPick }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchFiles = async () => {
      setLoading(true);
      try {
        const resp = await api.post("/get_file_structure", { repo_url: repoUrl });
        // backend returns { files: [...] } or similar
        const dataFiles = resp.data?.files ?? resp.data?.structure ?? [];
        setFiles(dataFiles);
      } catch (err) {
        console.error(err);
        setFiles([]);
      } finally {
        setLoading(false);
      }
    };
    if (repoUrl) fetchFiles();
  }, [repoUrl]);

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Select a file to summarize</DialogTitle>
      <DialogContent>
        {loading ? (
          <CircularProgress />
        ) : (
          <List sx={{ maxHeight: "60vh", overflow: "auto" }}>
            {files.length === 0 ? (
              <ListItem>
                <ListItemText primary="No files found" />
              </ListItem>
            ) : (
              files.map((f) => (
                <ListItem key={f} disablePadding>
                  <ListItemButton onClick={() => onPick(f)}>
                    <ListItemText primary={f} />
                  </ListItemButton>
                </ListItem>
              ))
            )}
          </List>
        )}
        <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 2 }}>
          <Button onClick={onClose} sx={{ color: "white" }}>Close</Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
