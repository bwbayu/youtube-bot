import { useCallback, useEffect, useState } from "react"
import { type VideoResponse } from "../api/useFetchComments";

export const useFetchVideos = (playlist_id: string, page = 1, page_size = 10) => {
  /**
   * 
   */
  const [videos, setVideos] = useState<VideoResponse[]>([])
  const [loadingVideos, setLoading] = useState(true)
  const [errorvideos, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 10,
    has_next: false,
  })

  const fetchVideos = useCallback(async () => {
    /**
     * useCallback is used to memoize the function so it won't be re-created on every render.
     * In React, functions are recreated on each render, which can trigger useEffect repeatedly.
     * useCallback helps "freeze" the function reference, keeping it the same as long as dependencies don't change.
     */
    try {
      setLoading(true)
      const res = await fetch(`http://localhost:8000/content/user_videos?playlist_id=${playlist_id}&page=${page}&page_size=${page_size}`, {
        credentials: "include",
      })
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      const data = await res.json()
      setVideos(data.items || [])
      setPagination({
        total: data.total,
        page: data.page,
        page_size: data.page_size,
        has_next: data.has_next,
      })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [playlist_id, page, page_size])

  useEffect(() => {
    if (playlist_id) fetchVideos()
  }, [playlist_id, fetchVideos])

  return { videos, loadingVideos, errorvideos, refetch: fetchVideos, pagination }
}
