import React, { useEffect, useState, useRef } from "react";
import { useLocation } from "react-router-dom";
import { Box, Typography, CircularProgress, Drawer, List, ListItem, ListItemText } from "@mui/material";
import ForceGraph2D from "react-force-graph-2d";

export default function DependencyGraph() {
  const location = useLocation();
  const repoUrl = location.state?.repoUrl || "";
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [nodeColors, setNodeColors] = useState({}); // Store actual node colors
  const colorUpdateRef = useRef({}); // avoid frequent re-renders

  useEffect(() => {
    if (!repoUrl) return;

    const fetchGraph = async () => {
      try {
        const response = await fetch("http://localhost:5000/dependency_graph", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ repo_url: repoUrl }),
        });
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
        }
        const data = await response.json();
        setGraphData(data);
      } catch (err) {
        console.error("Error fetching dependency graph:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, [repoUrl]);

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 5 }}>
        <CircularProgress color="success" />
      </Box>
    );
  }

  if (!graphData || !graphData.nodes) {
    return <Typography sx={{ mt: 5, textAlign: "center" }}>No dependency data found.</Typography>;
  }

  // Group files by actual node colors
  const filesByColor = {};
  graphData.nodes.forEach((node) => {
    const color = nodeColors[node.id] || "grey";
    if (!filesByColor[color]) filesByColor[color] = [];
    filesByColor[color].push(node.id);
  });

  return (
    <Box sx={{ display: "flex", height: "100vh", backgroundColor: "black" }}>
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        anchor="left"
        sx={{
          width: 250,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: 250,
            boxSizing: "border-box",
            backgroundColor: "#1e1e1e",
            color: "white",
          },
        }}
      >
        <Typography variant="h6" sx={{ textAlign: "center", p: 2 }}>
          Files by Node Color
        </Typography>
        <List>
          {Object.entries(filesByColor).map(([color, files]) => (
            <Box key={color}>
              {files.map((file) => (
                <ListItem key={file} sx={{ pl: 2 }}>
                  <Box
                    sx={{
                      width: 16,
                      height: 16,
                      backgroundColor: color,
                      border: "1px solid #fff",
                      mr: 1,
                      display: "inline-block",
                    }}
                  />
                  <ListItemText primary={file} sx={{ color: "white", ml: 1 }} />
                </ListItem>
              ))}
            </Box>
          ))}
        </List>
      </Drawer>

      {/* Graph */}
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" sx={{ color: "white", textAlign: "center", pt: 2 }}>
          Dependency Graph for {repoUrl}
        </Typography>
        <ForceGraph2D
          graphData={graphData}
          nodeAutoColorBy="group"
          nodeLabel="id"
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          width={window.innerWidth - 250} // reserve space for sidebar
          height={window.innerHeight - 80}
          nodeCanvasObject={(node, ctx, globalScale) => {
            // Capture the actual node color
            const nodeColor = node.color; // automatically set by nodeAutoColorBy
            colorUpdateRef.current[node.id] = nodeColor;

            // Update state once per animation frame to avoid too many renders
            requestAnimationFrame(() => {
              setNodeColors({ ...colorUpdateRef.current });
            });

            // Default node rendering
            ctx.fillStyle = nodeColor;
            ctx.beginPath();
            ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
            ctx.fill();
          }}
        />
      </Box>
    </Box>
  );
}
