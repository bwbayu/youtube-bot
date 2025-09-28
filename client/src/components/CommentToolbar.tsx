export const CommentToolbar = ({
  selectedCount,
  onDeleteSelected,
  onClearSelection
}: {
  selectedCount: number,
  onDeleteSelected: () => void,
  onClearSelection: () => void
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="bg-white text-black flex items-center justify-between px-4 py-2 shadow mb-4 rounded">
      <div className="text-sm">
        {selectedCount} selected <button onClick={onClearSelection} className="underline ml-2 text-blue-600">Clear</button>
      </div>
      <div className="space-x-2">
        <button
          onClick={onDeleteSelected}
          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Delete
        </button>
      </div>
    </div>
  );
};
