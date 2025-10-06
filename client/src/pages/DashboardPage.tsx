import { useState } from "react";
import { useFetchLatestVideos } from "../api/useFetchLatestVideos";
import { useFetchUser } from "../api/useFetchUser";
import { useFetchVideos } from "../api/useFetchVideos";
import { VideoCard } from "../components/VideoCard";
import { Navbar } from "../components/Navbar";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext
} from "@/components/ui/pagination";

export const DashboardPage = () => {
  const { user, playlistId } = useFetchUser()
  const [shouldFetchHistory, setShouldFetchHistory] = useState(false);
  const { latestVideos, loading: loadingLatest, error: errorLatest, refetch } = useFetchLatestVideos(
    playlistId || "", 
    {
      onSuccess: () => setShouldFetchHistory(true),
    }
  );
  const [page, setPage] = useState(1);
  const { videos, loadingVideos, errorvideos, pagination } = useFetchVideos(
    shouldFetchHistory ? (playlistId || "") : "", page, 10,
  
  );
  const totalPages = Math.ceil(pagination.total / pagination.page_size);

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

  return (
    <div className="min-h-screen bg-gray-900 text-white w-screen">
      <Navbar user={user} onLogout={handleLogout} />

      <main className="px-8 py-16">
        {/* <h1 className="text-4xl font-bold text-green-400 mb-4">Dashboard</h1> */}
        {/* Latest Videos */}
        <div className="mt-0">
          <h2 className="text-2xl font-semibold text-blue-400 mb-4">Video Terbaru</h2>
          {loadingLatest && <p>Mengambil video terbaru...</p>}
          {errorLatest && <p className="text-red-500">Error: {errorLatest}</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {latestVideos.map((video) => (
              <VideoCard key={video.video_id} video={video} type="latest" />
            ))}
          </div>
          <button onClick={refetch} className="mt-4 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
            Fetch Ulang Komentar
          </button>
        </div>

        {/* History Videos */}
        <div className="mt-12">
          <h2 className="text-2xl font-semibold text-yellow-400 mb-4">Riwayat Video</h2>
          {loadingVideos && <p>Loading videos...</p>}
          {errorvideos && <p className="text-red-500">Error: {errorvideos}</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((video) => (
              <VideoCard key={video.video_id} video={video} />
            ))}
          </div>
        </div>

        <div className="pt-5">
        {totalPages > 1 && (
            <Pagination>
              <PaginationContent>
                {page > 1 && (
                  <PaginationItem>
                    <PaginationPrevious href="#" onClick={() => setPage(page - 1)} />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationLink href="#" isActive>
                    {page}
                  </PaginationLink>
                </PaginationItem>

                {pagination.has_next && (
                  <PaginationItem>
                    <PaginationNext href="#" onClick={() => setPage(page + 1)} />
                  </PaginationItem>
                )}
              </PaginationContent>
            </Pagination>
          )}
        </div>
      </main>
    </div>
  )
}