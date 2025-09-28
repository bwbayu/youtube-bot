import { useParams } from "react-router-dom";
import { useState } from "react";

import { useFetchComments } from "../api/useFetchComments";

import { useUser } from "../context/UserContext";

import { CommentToolbar } from "../components/CommentToolbar";
import { CommentCard } from "../components/CommentCard";
import { Navbar } from "../components/Navbar";

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext
} from "@/components/ui/pagination";

export const VideoDetailPage = () => {
  const { videoId } = useParams();
  const [page, setPage] = useState(1);
  const user = useUser();
  const { videoDetail, comments, loadingComment, errorComment, pagination, refetch } = useFetchComments(videoId || "", page, 10);
  const totalPages = Math.ceil(pagination.total / pagination.page_size);
  const [selected, setSelected] = useState<string[]>([]);
  // TODO: handle global context sebelum login jadi error ke dashboardnya
  // TODO_BACKEND: refactor code dan error handling di BE dan FE nya
  const model_predict = () => {
    console.log("ML process");
  };

  const toggleCheckbox = (id: string, checked: boolean) => {
    setSelected(prev => checked ? [...prev, id] : prev.filter(cid => cid !== id));
  };

  const handleDeleteComment = (id: string) => {
    console.log("Delete comment", id);
  };

  const deleteSelected = () => {
    console.log("Delete selected:", selected);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white w-screen">
      <Navbar user={user} />
      <div className="px-8 py-10">
        <h1 className="text-3xl font-bold text-green-400 mb-4">Detail Video</h1>
        {loadingComment && <p>Loading...</p>}
        {errorComment && <p className="text-red-500">Error: {errorComment}</p>}

        {videoDetail && (
          <div className="mb-8 bg-gray-800 p-4 rounded shadow flex flex-row justify-between items-center gap-4">
            <div className="flex flex-col flex-grow">
              <h2 className="text-xl font-semibold text-blue-300 hover:underline">
                <a href={`https://www.youtube.com/watch?v=${videoDetail.video_id}`}>
                  {videoDetail.title}
                </a>
              </h2>
              <p className="text-gray-300">{videoDetail.description}</p>
              <p className="text-gray-300">Total Komentar: {pagination.total}</p>
              <p className="text-sm text-gray-500">
                Dipublikasikan: {new Date(videoDetail.published_at).toLocaleString()}
              </p>
            </div>
            
            <div className="flex-shrink-0">
              <button
                onClick={refetch}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
              >
                Fetch Ulang Komentar
              </button>
            </div>
          </div>
        )}

        <CommentToolbar
            selectedCount={selected.length}
            onDeleteSelected={deleteSelected}
            onClearSelection={() => setSelected([])}
            onRunMLDetection={model_predict}
        />

        <div className="space-y-3">
            {comments.map((c) => (
            <CommentCard
                key={c.comment_id}
                comment={c}
                isSelected={selected.includes(c.comment_id)}
                onSelect={(checked) => toggleCheckbox(c.comment_id, checked)}
                onDelete={handleDeleteComment}
            />
            ))}
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
      </div>
    </div>
  );
};