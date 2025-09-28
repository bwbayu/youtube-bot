import { useParams } from "react-router-dom";
import { useState } from "react";
import { useFetchComments } from "../api/useFetchComments";
import { useUser } from "../context/UserContext";
import { Navbar } from "../components/Navbar";
import { CommentCard } from "../components/CommentCard";
import { CommentToolbar } from "../components/CommentToolbar";

export const VideoDetailPage = () => {
  const { videoId } = useParams();
  const [page, setPage] = useState(1);
  const user = useUser();
  const { videoDetail, comments, total, loadingComment, errorComment } = useFetchComments(videoId || "", page, 10);
  const [selected, setSelected] = useState<string[]>([]);

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
            <div className="mb-8 bg-gray-800 p-4 rounded shadow">
            <h2 className="text-xl font-semibold text-blue-300">{videoDetail.title}</h2>
            <p className="text-gray-300">{videoDetail.description}</p>
            <p className="text-sm text-gray-500">Dipublikasikan: {new Date(videoDetail.published_at).toLocaleString()}</p>
            </div>
        )}

        <CommentToolbar
            selectedCount={selected.length}
            onDeleteSelected={deleteSelected}
            onClearSelection={() => setSelected([])}
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

        <div className="flex gap-4 mt-6">
            <button
            onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
            className="px-3 py-1 bg-gray-700 rounded"
            disabled={page === 1}
            >
            Prev
            </button>
            <span>Halaman {page}/{Math.ceil(total/10)}</span>
            <button
            onClick={() => setPage((prev) => prev + 1)}
            className="px-3 py-1 bg-gray-700 rounded"
            >
            Next
            </button>
        </div>
      </div>
    </div>
  );
};