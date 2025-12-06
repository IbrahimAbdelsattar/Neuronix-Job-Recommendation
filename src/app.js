// Toast Notification
export function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  toast.style.display = "block";

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Backend API URL
export const API_URL = "http://localhost:5000";

// API Helper
export async function apiCall(endpoint, method = "GET", body = null) {
  const headers = {
    "Content-Type": "application/json",
  };

  const config = {
    method,
    headers,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_URL}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "API Request Failed");
    }

    return data;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

// Navbar Logic (Mobile Toggle if needed, currently simple)
document.addEventListener("DOMContentLoaded", () => {
  // Highlight active link
  const currentPath = window.location.pathname;
  const links = document.querySelectorAll(".nav-link");
  links.forEach((link) => {
    if (link.getAttribute("href") === currentPath.split("/").pop()) {
      link.style.color = "hsl(var(--primary))";
      link.style.fontWeight = "600";
    }
  });
});
