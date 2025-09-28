import { Link } from "react-router-dom";

export const VideoCard = ({ video, type = "history" }: { video: any, type?: "latest" | "history" }) => (
  <div className="p-4 bg-gray-800 rounded-lg shadow hover:shadow-lg transition">
    <h3 className="text-lg font-semibold text-white mb-1">{video.title}</h3>
    <p className="text-sm text-gray-400 mb-2">
      Published: {video.published_at}
    </p>

    {type === "latest" && (
      <>
        {video.new_comment_count !== undefined ? (
          <p className="text-green-400 mb-2">New Comments: {video.new_comment_count}</p>
        ) : (
          <p className="text-red-400 mb-2">Error: {video.error}</p>
        )}
      </>
    )}

    <Link to={`/video/${video.video_id}`} className="text-blue-400 hover:underline">
      View Details →
    </Link>
  </div>
);