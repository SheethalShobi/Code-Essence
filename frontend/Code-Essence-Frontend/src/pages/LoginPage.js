import React from "react";
import { Box, Button, Typography } from "@mui/material";

export default function LoginPage() {

  const handleLogin = () => {
    // Redirect to Flask backend login endpoint
    window.location.href = "http://localhost:5000/login"; // your Flask backend URL
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        backgroundColor: "black",
        color: "white",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Box sx={{ width: 420, p: 3, backgroundColor: "#111", borderRadius: 2, textAlign: "center" }}>
        <Typography variant="h5" sx={{ color: "limegreen", fontWeight: "bold", mb: 3 }}>
          Login
        </Typography>
        <Button
          onClick={handleLogin}
          variant="contained"
          sx={{ backgroundColor: "limegreen", color: "black", fontWeight: "bold", width: "100%" }}
        >
          Login with GitHub
        </Button>
      </Box>
    </Box>
  );
}
