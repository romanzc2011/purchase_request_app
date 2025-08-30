import { useState, useCallback, useRef } from "react";
import {addComments } from "../services/commentService";
import { GroupCommentPayload } from "../types/approvalTypes";
import { toast } from "react-toastify";

export function useCommentModal() {
  const [isOpen, setIsOpen]         = useState(false);
  const resolverRef                 = useRef<(value: string) => void>();

  // open with whatever payload you have (single or multi)
  const openCommentModal = useCallback((_payload: GroupCommentPayload) => {
    setIsOpen(true);
    return new Promise<string>(resolve => {
      resolverRef.current = resolve;
    });
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
  }, []);

  // called by your CommentModal’s “Submit” button
  const handleSubmit = useCallback(
    (userComment: string) => {
        console.log("🔥 handleSubmit fired with:", userComment);
        const trimmed = userComment.trim();
        if (trimmed && resolverRef.current) {
            resolverRef.current(trimmed);
        }
        close();
    },
    [close]
  );

  // #########################################################################################
  // Bulk comment - sends everything to backend, even if it's a single comment
  // #########################################################################################  
  async function onBulkComment(payload: GroupCommentPayload, comment: string) {
    const bulkPayload: GroupCommentPayload = {
        groupKey: payload.groupKey,
        comment: payload.item_uuids.map(uuid => ({ uuid, comment })),
        group_count: payload.group_count,
        item_uuids: payload.item_uuids,
        item_desc: payload.item_desc,
    };
    await addComments(bulkPayload);
    toast.success("Comments added successfully");
  }

  return {
    isOpen,
    openCommentModal,
    close,
    handleSubmit,
    onBulkComment,
  };
}
