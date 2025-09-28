export const CommentToolbar = ({
  selectedCount,
  onDeleteSelected,
  onClearSelection,
  onRunMLDetection
}: {
  selectedCount: number,
  onDeleteSelected: () => void,
  onClearSelection: () => void,
  onRunMLDetection: () => void
}) => {
  return (
    <div className="bg-gray-800 text-white font-bold flex items-center justify-between px-4 py-2 shadow mb-4 rounded">
      <div className="text-sm">
        {selectedCount} selected{" "}
        {selectedCount > 0 && (
          <button
            onClick={onClearSelection}
            className="ml-2 text-blue-600"
          >
            Clear
          </button>
        )}
      </div>
      <div className="space-x-2">
        <button
          onClick={onRunMLDetection}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Run AI Detection
        </button>
        <button
          onClick={onDeleteSelected}
          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
          disabled={selectedCount === 0}
        >
          Delete Selected
        </button>
      </div>
    </div>
  );
};
