import { useCallback, useEffect, useState } from "react";

export type VideoFetchResult = {
  video_id: string;
  title: string;
  published_at: Date;
  new_comment_count: number;
  error: string;
};

export function useFetchLatestVideos(playlistId: string, options?: { onSuccess?: () => void }) {
  const [latestVideos, setLatestVideos] = useState<VideoFetchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLatestVideos = useCallback(async () => {
    if (!playlistId) return;

    try {
      setLoading(true);
      const res = await fetch(
        `http://localhost:8000/content/fetch-latest-videos?playlist_id=${playlistId}`,
        {
          method: "GET",
          credentials: "include", // Kirim cookie session_id
        }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal ambil video");
      }

      const data = await res.json();
      setLatestVideos(data);
      setError(null);
      options?.onSuccess?.();
    } catch (err: unknown) {
        if (err instanceof Error){
            console.error("Fetch video gagal:", err);
            setError(err.message || "Unknown error");
        } else{
            console.error("Fetch video gagal:", err);
            setError("Unexpected error: " + err);
        }
    } finally {
      setLoading(false);
    }
  }, [playlistId]);

  useEffect(() => {
    fetchLatestVideos();
  }, [fetchLatestVideos]);

  return { latestVideos, loading, error, refetch: fetchLatestVideos };
}
