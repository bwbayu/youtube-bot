import { useCallback, useEffect, useState } from "react"

export type VideoResponse = {
    video_id: string;
    channel_id: string;
    playlist_id: string;
    title: string;
    description: string;
    published_at: Date;
    last_fetch_comment: Date;
}

export type CommentResponse = {
    comment_id: string;
    video_id: string;
    author_display_name: string;
    text: string;
    published_at: Date;
    updated_at: Date;
    is_judi: boolean;
}

export const useFetchComments = (videoId: string, page = 1, page_size = 10) => {
  const [comments, setComments] = useState<CommentResponse[]>([])
  const [videoDetail, setVideoDetail] = useState<VideoResponse | null>(null)
  const [total, setTotal] = useState(0)
  const [loadingComment, setLoading] = useState(true)
  const [errorComment, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)

      const res = await fetch(
        `http://localhost:8000/content/video/${videoId}?page=${page}&limit=${page_size}`,
        { credentials: "include" }
      )

      if (!res.ok) throw new Error(`HTTP error ${res.status}`)

      const data = await res.json()
      setVideoDetail(data.videoDetail)
      setComments(data.items)
      setTotal(data.total)
      setError(null) // reset error on success
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [videoId, page, page_size])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { comments, videoDetail, total, loadingComment, errorComment }
}
