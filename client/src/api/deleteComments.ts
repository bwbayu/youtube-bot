type DeleteCommentsPayload = {
  comment_ids: string[];
  moderation_status?: "heldForReview" | "rejected" | "published";
  ban_author?: boolean;
};

type DeleteCommentsResponse = {
  success: boolean;
  updated: number;
};

export async function deleteComments(
  payload: DeleteCommentsPayload
): Promise<DeleteCommentsResponse> {
  const res = await fetch("http://localhost:8000/content/comments/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      comment_ids: payload.comment_ids,
      moderation_status: payload.moderation_status || "heldForReview",
      ban_author: payload.ban_author || false,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to delete comments");
  }

  return res.json();
}
