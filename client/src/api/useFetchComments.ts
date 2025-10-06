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
    confidence: number;
    moderation_status: string;
}

export const useFetchComments = (videoId: string, page = 1, page_size = 10) => {
  const [comments, setComments] = useState<CommentResponse[]>([])
  const [videoDetail, setVideoDetail] = useState<VideoResponse | null>(null)
  const [loadingComment, setLoading] = useState(true)
  const [errorComment, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 10,
    has_next: false,
  })

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)

      const res = await fetch(
        `http://localhost:8000/content/video/${videoId}?page=${page}&limit=${page_size}`,
        {
          method: 'GET',
          credentials: "include" 
        }
      )

      if (!res.ok) throw new Error(`HTTP error ${res.status}`)

      const data = await res.json()
      setVideoDetail(data.videoDetail)
      setComments(data.items)
      setPagination({
        total: data.total,
        page: data.page,
        page_size: data.page_size,
        has_next: data.has_next,
      })
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

  return { comments, videoDetail, loadingComment, errorComment, pagination, refetch: fetchData }
}
