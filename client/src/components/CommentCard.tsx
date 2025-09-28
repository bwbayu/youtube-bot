import type { CommentResponse } from "../api/useFetchComments";

export const CommentCard = ({
  comment,
  isSelected,
  onSelect,
  onDelete,
}: {
  comment: CommentResponse;
  isSelected: boolean;
  onSelect: (checked: boolean) => void;
  onDelete: (id: string) => void;
}) => {
  const handleCardClick = () => onSelect(!isSelected);

  return (
    <div
      onClick={handleCardClick}
      className={`cursor-pointer flex items-start space-x-4 p-4 rounded relative border ${
        isSelected ? "bg-gray-700 border-purple-500" : "bg-gray-800 border-transparent"
      }`}
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={(e) => onSelect(e.target.checked)}
        className="mt-1"
        onClick={(e) => e.stopPropagation()} // prevent bubbling to card
      />
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold text-white">
          {comment.author_display_name}
        </p>
        <p className="text-gray-300">{comment.text}</p>
        {comment.is_judi && (
          <span className="text-sm font-semibold text-red-500 mt-1">
            Mengandung Judi
          </span>
        )}
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation(); // prevent toggle on delete click
          onDelete(comment.comment_id);
        }}
        className="absolute top-4 right-4 bg-red-600 hover:bg-red-700 px-3 py-1 text-sm rounded"
      >
        Delete
      </button>
    </div>
  );
};
