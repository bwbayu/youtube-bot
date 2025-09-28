import type { CommentResponse } from "../api/useFetchComments";

export const CommentCard = ({
  comment,
  isSelected,
  onSelect,
  onDelete
}: {
  comment: CommentResponse,
  isSelected: boolean,
  onSelect: (checked: boolean) => void,
  onDelete: (id: string) => void
}) => (
  <div className="flex items-start space-x-4 p-4 bg-gray-800 rounded relative">
    <input
      type="checkbox"
      checked={isSelected}
      onChange={(e) => onSelect(e.target.checked)}
      className="mt-1"
    />
    <div>
      <p className="text-sm font-semibold text-white">{comment.author_display_name}</p>
      <p className="text-gray-300">{comment.text}</p>
      {comment.is_judi && (
        <span className="text-sm font-semibold text-red-500 mt-1 ml-6 inline-block">
          🎲 Mengandung Judi
        </span>
      )}
      <button
        onClick={() => onDelete(comment.comment_id)}
        className="absolute top-4 right-4 bg-red-600 hover:bg-red-700 px-3 py-1 text-sm rounded"
      >
        Delete
      </button>
    </div>
  </div>
);


