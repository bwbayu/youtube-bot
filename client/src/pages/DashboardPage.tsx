import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom";

export const DashboardPage = () => {
  const [userId, setUserId] = useState<string | null>(null)
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const res = await fetch("http://localhost:8000/auth/logout", {
        method: "POST",
        credentials: "include",
      })

      const data = await res.json()

      if (res.ok && data.logout_status) {
        console.info(data.message)
      } else {
        console.warn(data.message || "Logout failed.")
      }

      // Redirect to home
      window.location.href = "/"
    } catch (err) {
      console.error("Logout failed:", err)
    }
  }

  const fetchUser = async () => {
  try {
    const res = await fetch("http://localhost:8000/content/user", {
      method: "GET",
      credentials: "include", // send cookie
    });

    if (res.ok) {
      const data = await res.json();

      if (!data.user_id) {
        redirectToHome();
        return;
      }

      setUserId(data.user_id);
    } else if (res.status === 401) {
      console.log("Unauthorized: user not logged in");
      redirectToHome();
    } else {
      console.warn("Unhandled error:", res.status);
      setUserId(null);
    }
  } catch (err) {
    console.error("Error fetching user info:", err);
    setUserId(null);
    redirectToHome();
  }
};

  const redirectToHome = () => {
    navigate("/");
  };

  useEffect(() => {
    fetchUser();
  });

  return (
    <>
      <div>
        <h1>dashboard</h1>
        <p><strong>User ID:</strong> {userId || "Not logged in"}</p>
        <button
        onClick={handleLogout}
        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded"
        >
        Logout
        </button>
      </div>
    </>
  )
}