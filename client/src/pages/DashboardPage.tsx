import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom";
import { useFetchVideos } from "../api/useFetchVideos";

type User = {
  user_id: string;
  name: string;
  email: string;
  channel_id: string;
  custom_url: string;
  playlist_id: string;
}

export const DashboardPage = () => {
  const [user, setUser] = useState<User | null>(null)
  const [playlistId, setPlaylistId] = useState<string | null>(null)
  const { videos, loading, error, refetch } = useFetchVideos(playlistId || "");
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

  const fetchUser = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/content/users", {
        method: "GET",
        credentials: "include", // send cookie
      });

      if (res.ok) {
        const data = await res.json();

        if (!data.user_id) {
          navigate("/");
          return;
        }

        setUser(data);
        setPlaylistId(data.playlist_id);
      } else if (res.status === 401) {
        console.log("Unauthorized: user not logged in");
        navigate("/");
      } else {
        console.warn("Unhandled error:", res.status);
        setUser(null);
      }
    } catch (err) {
      console.error("Error fetching user info:", err);
      setUser(null);
      navigate("/");
    }
  }, [navigate]);


  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return (
    <div className="min-h-screen bg-gray-900 text-white w-screen">
      <nav className="flex items-center justify-between px-8 py-4 bg-gray-800">
        <div className="text-2xl font-bold text-purple-400">StopJudol</div>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded"
        >
          Logout
        </button>
      </nav>

      <main className="px-8 py-16">
        <h1 className="text-4xl font-bold text-green-400 mb-4">Dashboard</h1>
        {user ? (
          <>
            <p><strong>User ID:</strong> {user.user_id}</p>
            <p><strong>Name:</strong> {user.name}</p>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Channel ID:</strong> {user.channel_id}</p>
            <p><strong>Custom URL:</strong> {user.custom_url}</p>
            <p><strong>Playlist ID:</strong> {user.playlist_id}</p>
          </>
        ) : (
          <p>Loading user...</p>
        )}
        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-blue-400 mb-2">Video & Komentar</h2>

          {loading && <p className="text-yellow-400">Mengambil data video dan komentar...</p>}
          {error && <p className="text-red-500">Error: {error}</p>}

          <ul className="space-y-2">
            {videos.map((v) => (
              <li key={v.video_id} className="border-b pb-2 border-gray-700">
                <p className="text-lg">
                  <strong>Video ID:</strong> {v.video_id}
                </p>
                {v.comment_count !== undefined ? (
                  <p className="text-green-400">
                    Komentar: {v.comment_count}
                  </p>
                ) : (
                  <p className="text-red-400">Error: {v.error}</p>
                )}
              </li>
            ))}
          </ul>

          <button
            onClick={refetch}
            className="mt-6 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
          >
            Fetch Ulang Komentar
          </button>
        </div>
      </main>
    </div>
  )
}