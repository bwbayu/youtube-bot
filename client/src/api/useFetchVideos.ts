import { useCallback, useEffect, useState } from "react"
import { type VideoResponse } from "../api/useFetchComments";

export const useFetchVideos = (playlist_id: string, page = 1, page_size = 10) => {
  const [videos, setVideos] = useState<VideoResponse[]>([])
  const [loadingVideos, setLoading] = useState(true)
  const [errorvideos, setError] = useState<string | null>(null)

  const fetchVideos = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`http://localhost:8000/content/user_videos?playlist_id=${playlist_id}&page=${page}&page_size=${page_size}`, {
        credentials: "include",
      })
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      const data = await res.json()
      setVideos(data.items || [])
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [playlist_id, page, page_size])

  useEffect(() => {
    if (playlist_id) fetchVideos()
  }, [playlist_id, fetchVideos])

  return { videos, loadingVideos, errorvideos, refetch: fetchVideos }
}
