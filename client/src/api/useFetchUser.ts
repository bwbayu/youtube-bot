import { useEffect, useState, useCallback } from "react"
import { useNavigate } from "react-router-dom";

export type User = {
  user_id: string;
  name: string;
  email: string;
  channel_id: string;
  custom_url: string;
  playlist_id: string;
}

export const useFetchUser = () => {
  const [user, setUser] = useState<User | null>(null)
  const [playlistId, setPlaylistId] = useState<string | null>(null)
  const [loadingUser, setLoading] = useState(true)
  const [errorUser, setError] = useState<string | null>(null)
  
  const navigate = useNavigate();

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
      setError((err as Error).message)
      navigate("/");
    } finally {
      setLoading(false)
    }
  }, [navigate]);


  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return { user, playlistId, loadingUser, errorUser }
}
