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
/* Trigger to auto update BOC, Fund, Location if altered
	in PurchaseRequestLineItems: update approvals, */
----------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS sync_bocloclfund
AFTER UPDATE OF budgetObjCode, location, fund, quantity, priceEach, totalPrice ON pr_line_items
FOR EACH ROW
BEGIN
	UPDATE approvals
	SET
		budgetObjCode 	= coalesce(NEW.budgetObjCode, budgetObjCode),
		location		= coalesce(NEW.location, location),
		fund			= coalesce(NEW.fund, fund),
		quantity		= coalesce(NEW.quantity, quantity),
		priceEach		= coalesce(NEW.priceEach, priceEach),
		totalPrice		= coalesce(NEW.totalPrice, totalPrice)
	WHERE purchase_request_id = NEW.purchase_request_id;
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
/* Trigger to auto update originalPriceEach and priceUpdated on pr_line_items */
----------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS sync_originalPriceEach_on_update_pr_line_items
AFTER UPDATE OF priceEach ON pr_line_items
BEGIN
	UPDATE pr_line_items
	SET originalPriceEach = CASE 
		WHEN NEW.priceUpdated = FALSE THEN NEW.priceEach
		ELSE originalPriceEach
	END,
	priceUpdated = CASE 
		WHEN NEW.priceUpdated = FALSE THEN 1
		ELSE priceUpdated
	END
	WHERE UUID = NEW.UUID;
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
/* Trigger to auto update RQ1 number in approvals
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
("Peter Baltz", "peter_baltz@lawb.uscourts.gov");

INSERT OR IGNORE INTO contracting_officers
(username, email)
VALUES
("Lauren Lee", "lauren_lee@lawb.uscourts.gov");

INSERT OR IGNORE INTO contracting_officers
(username, email)
VALUES
("Lela Robichaux", "lela_robichaux@lawb.uscourts.gov");

----------------------------------------------------------
-- Fill out fund

-- Court Clerks: Edmund, Ted
INSERT OR IGNORE INTO budget_fund
(fund_code)
VALUES
("51140X");

INSERT OR IGNORE INTO budget_fund
(fund_code)
VALUES
("51140E");

INSERT OR IGNORE INTO budget_fund
(fund_code)
VALUES
("092000");