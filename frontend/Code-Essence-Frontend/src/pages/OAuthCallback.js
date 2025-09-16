import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function OAuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    // Call Flask backend callback to get token
    fetch("http://localhost:5000/callback")
      .then((res) => res.json())
      .then((data) => {
        localStorage.setItem("token", data.token); // save GitHub token
        localStorage.setItem("user", JSON.stringify(data.user));
        navigate("/profile"); // redirect to profile page
      })
      .catch((err) => console.error(err));
  }, [navigate]);

  return <div style={{ color: "white" }}>Logging in with GitHub...</div>;
}
