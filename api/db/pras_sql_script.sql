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
	-- PR LINE ITEMS
    UPDATE pr_line_items
    SET status = 'PENDING APPROVAL'
    WHERE UUID = NEW.line_item_uuid;

	-- APPROVALS
    UPDATE approvals
    SET status = 'PENDING APPROVAL'
    WHERE UUID = NEW.approvals_uuid;

	-- PENDING APPROVALS
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
	-- PR LINE ITEMS
	UPDATE pr_line_items
	SET status = NEW.status
	WHERE UUID = NEW.line_item_uuid;
	
	-- APPROVALS
	UPDATE approvals
	SET status = NEW.status
	WHERE UUID = NEW.approvals_uuid;
	
	-- PENDING APPROVALS
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
	-- SON COMMENTS
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
    -- APPROVALS
    UPDATE approvals
    SET status = 'DENIED'
    WHERE UUID = NEW.approvals_uuid;

    -- PR LINE ITEMS
    UPDATE pr_line_items
    SET status = 'DENIED'
    WHERE UUID = NEW.line_item_uuid;
END;

----------------------------------------------------------
/* Trigger to auto update CO in approvals
on contracting_officer_id update in pr header */
----------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS sync_co_on_update_prhdr
AFTER UPDATE ON purchase_request_headers
WHEN NEW.contracting_officer_id IS NOT NULL
BEGIN
  -- PURCHASE REQUEST HEADERS
  UPDATE purchase_request_headers
     SET CO = (
       SELECT username
         FROM contracting_officers
        WHERE id = NEW.contracting_officer_id
     )
   WHERE ID = NEW.id;
   
   -- APPROVALS
   UPDATE approvals
   SET CO = (
		SELECT username
		FROM contracting_officers
		WHERE id = NEW.contracting_officer_id
   )
   WHERE purchase_request_id = NEW.id;
END;

----------------------------------------------------------
/* Trigger to auto update IRQ1 number in approvals
	after inserting into purchase_request_headers */
----------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS sync_irq1_on_update_irq1_prhdr
AFTER UPDATE ON purchase_request_headers
WHEN NEW.IRQ1_ID IS NOT NULL
BEGIN
	-- APPROVALS
	UPDATE approvals
	SET IRQ1_ID = NEW.IRQ1_ID
	WHERE purchase_request_id = NEW.ID;
END;
		

----------------------------------------------------------
/* INSERT CONTRACTING OFFICERS 
    - peter_baltz will be peterbaltz in prod
	PROD:
	- peterbaltz, 	 peter_baltz@lawb.uscourts.gov
	- laurenlee,  	 lauren_lee@lawb.uscourts.gov
	- lelarobichaux, lela_robichaux@lawb.uscourts.gov
 */
----------------------------------------------------------
INSERT OR IGNORE INTO contracting_officers
(username, email)
VALUES
("peter_baltz", "peter_baltz@lawb.uscourts.gov");

INSERT OR IGNORE INTO contracting_officers
(username, email)
VALUES
("romancampbell", "roman_campbell@lawb.uscourts.gov");

-- Court Clerks: Edmund, Ted


-- DELETE FROM final_approvals;
-- DELETE FROM pending_approvals;
-- DELETE FROM approvals;
-- DELETE FROM pr_line_items;
-- DELETE FROM purchase_request_headers;
-- DELETE FROM son_comments
-- DELETE FROM justification_templates;
-- DELETE FROM contracting_officers;

-- SELECT con.username 
-- FROM contracting_officers con
-- INNER JOIN purchase_request_headers prhdr ON con.id = prhdr.contracting_officer_id
-- WHERE 1=1
-- AND prhdr.purchase_request_seq_id = 1;

-- UPDATE final_approvals
-- SET status = 'NEW REQUEST'
-- WHERE UUID = '60735e02-9679-406f-89ba-241e33e769fa';
-- 
-- DELETE FROM final_approvals WHERE UUID = '60735e02-9679-406f-89ba-241e33e769fa';


-- CHANGE REQUEST BACK TO NEW REQUEST
-- UPDATE approvals
-- SET status = 'NEW REQUEST'
-- WHERE UUID = 'd4bc97bd-852e-44a1-988b-11b4a647165a';