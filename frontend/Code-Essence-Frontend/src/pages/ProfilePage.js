import React, { useEffect, useState } from "react";
import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function ProfilePage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState(localStorage.getItem("username") || "User");

  useEffect(() => {
    document.body.style.backgroundColor = "#000";
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/");
  };

  return (
    <Box sx={{ minHeight: "100vh", backgroundColor: "black", color: "white", p: 4 }}>
      <Typography variant="h4" sx={{ color: "limegreen", fontWeight: "bold", mb: 2 }}>Welcome, {username}</Typography>
      <Button variant="contained" onClick={() => navigate("/")} sx={{ mr: 2 }}>Home</Button>
      <Button variant="outlined" onClick={logout}>Logout</Button>
    </Box>
  );
}
