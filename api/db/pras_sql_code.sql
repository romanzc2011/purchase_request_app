----------------------------------------------------------
-- TRIGGERS ----------------------------------------------
----------------------------------------------------------

----------------------------------------------------------
/* Trigger for auto updating pr_line_items, approvals, pending_approvals when 
a request is approved by IT/ACCESS and goes to final_approvals  ---> PENDING_APPROVAL */
----------------------------------------------------------
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

----------------------------------------------------------
/* UPDATE all statuses to APPROVED, DENIED */
----------------------------------------------------------
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
	WHERE line_item_uuid = NEW.line_item_uuid;
END;

----------------------------------------------------------
/* Trigger to auto insert approvals uuid after 
the inital add comment is run */
----------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS sync_approvals_uuid_on_first_insert
AFTER INSERT ON son_comments
FOR EACH ROW
BEGIN
	UPDATE son_comments
	SET approvals_uuid = (
		SELECT approvals.UUID
		FROM pr_line_items
		JOIN approvals
			ON approvals.purchase_request_id = pr_line_items.purchase_request_id
		WHERE pr_line_items.UUID = son_comments.line_item_uuid
	)
	WHERE line_item_uuid = NEW.line_item_uuid;
END;

----------------------------------------------------------
/* Trigger to auto update status to denied AFTER pr_line_items
is set to DENIED */
----------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS sync_status_on_update_pr_line_items
AFTER UPDATE ON pending_approvals
WHEN NEW.status = 'DENIED'
BEGIN
    -- Update approvals table
    UPDATE approvals
    SET status = 'DENIED'
    WHERE UUID = NEW.approvals_uuid;

    -- Update pr_line_items table
    UPDATE pr_line_items
    SET status = 'DENIED'
    WHERE UUID = NEW.line_item_uuid;
END;

----------------------------------------------------------
/* Trigger to auto update CO in approvals
on contracting_officer_id update in pr header */
----------------------------------------------------------
CREATE TRIGGER sync_co_on_update_prhdr
AFTER UPDATE ON purchase_request_headers
WHEN NEW.contracting_officer_id IS NOT NULL
BEGIN
  UPDATE approvals
     SET CO = (
       SELECT username
         FROM contracting_officers
        WHERE id = NEW.contracting_officer_id
     )
   WHERE purchase_request_id = NEW.id;
END;

-- DELETE FROM final_approvals;	1
-- DELETE FROM pending_approvals;
-- DELETE FROM approvals;
-- DELETE FROM pr_line_items;
-- DELETE FROM purchase_request_headers;
-- DELETE FROM son_comments
-- DELETE FROM justification_templates;
-- DELETE FROM contracting_officers;

--RELEASE "UNDOPOINT";

