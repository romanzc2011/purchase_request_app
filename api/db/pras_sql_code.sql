-- TRIGGERS

/* Trigger for auto updating pr_line_items, approvals, pending_approvals when 
a request is approved by IT/ACCESS and goes to final_approvals  ---> PENDING_APPROVAL */
CREATE TRIGGER IF NOT EXISTS sync_status_on_final_approval_insert
AFTER INSERT ON final_approvals
BEGIN
    UPDATE pr_line_items
    SET status = 'PENDING APPROVAL'
    WHERE UUID = NEW.line_item_uuid;

    UPDATE approvals
    SET status = 'PENDING APPROVAL'
    WHERE UUID = NEW.approvals_uuid;

    UPDATE pending_approvals
    SET status = 'PENDING APPROVAL'
    WHERE pending_approval_id = NEW.pending_approval_id;
END;
COMMIT;

/* UPDATE */
CREATE TRIGGER IF NOT EXISTS sync_status_on_final_approval_update
AFTER UPDATE ON final_approvals
WHEN NEW.status IN ('APPROVED', 'DENIED')
BEGIN
	UPDATE pr_line_items
	SET status = NEW.status
	WHERE UUID = NEW.line_item_uuid;
	
	UPDATE approvals
	SET status = NEW.status
	WHERE UUID = NEW.approvals_uuid;
	
	UPDATE pending_approvals
	SET status = NEW.status
	WHERE pending_approval_id = NEW.pending_approval_id;
END;
COMMIT;

-- DELETE FROM final_approvals;
-- DELETE FROM pending_approvals;
-- DELETE FROM approvals;
-- DELETE FROM pr_line_items;
-- DELETE FROM purchase_request_headers;



