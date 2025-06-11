CREATE TABLE purchase_requests (
        id INTEGER NOT NULL,
        uuid VARCHAR,
        requester VARCHAR,
        phone_ext INTEGER,
        date_requested DATE,
        date_needed DATE,
        order_type VARCHAR,
        status VARCHAR(11),
        created_time DATETIME NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (uuid)
);
CREATE TABLE users (
        id INTEGER NOT NULL,
        username VARCHAR NOT NULL,
        email VARCHAR NOT NULL,
        department VARCHAR NOT NULL,
        PRIMARY KEY (id)
);
CREATE TABLE line_items (
        id INTEGER NOT NULL,
        purchase_request_uuid VARCHAR NOT NULL,
        item_description TEXT NOT NULL,
        justification TEXT NOT NULL,
        add_comments TEXT,
        train_not_aval BOOLEAN NOT NULL,
        needs_not_meet BOOLEAN NOT NULL,
        budget_obj_code VARCHAR NOT NULL,
        fund VARCHAR NOT NULL,
        quantity INTEGER NOT NULL,
        price_each FLOAT NOT NULL,
        total_price FLOAT NOT NULL,
        location VARCHAR NOT NULL,
        is_cyber_sec_related BOOLEAN NOT NULL,
        status VARCHAR(11) NOT NULL,
        created_time DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(purchase_request_uuid) REFERENCES purchase_requests (uuid)
);
CREATE INDEX ix_line_items_purchase_request_uuid ON line_items (purchase_request_uuid);
CREATE TABLE approvals (
        approval_uuid VARCHAR NOT NULL,
        approval_id VARCHAR NOT NULL,
        irq1_id VARCHAR,
        purchase_request_uuid VARCHAR NOT NULL,
        purchase_request_id VARCHAR NOT NULL,
        requester VARCHAR NOT NULL,
        co VARCHAR,
        phoneext INTEGER NOT NULL,
        datereq VARCHAR NOT NULL,
        dateneed VARCHAR,
        order_type VARCHAR,
        file_attachments BLOB,
        item_description TEXT NOT NULL,
        justification TEXT NOT NULL,
        train_not_aval BOOLEAN,
        needs_not_meet BOOLEAN,
        budget_obj_code VARCHAR NOT NULL,
        fund VARCHAR NOT NULL,
        price_each FLOAT NOT NULL,
        total_price FLOAT NOT NULL,
        location VARCHAR NOT NULL,
        quantity INTEGER NOT NULL,
        created_time DATETIME NOT NULL,
        is_cyber_sec_related BOOLEAN,
        status VARCHAR(11) NOT NULL,
        PRIMARY KEY (approval_uuid),
        UNIQUE (irq1_id),
        FOREIGN KEY(purchase_request_uuid) REFERENCES purchase_requests (uuid)
);
CREATE TABLE item_approvals (
        id INTEGER NOT NULL,
        approval_uuid VARCHAR NOT NULL,
        line_item_id INTEGER NOT NULL,
        approver VARCHAR NOT NULL,
        action VARCHAR(11) NOT NULL,
        comments TEXT,
        created_at DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(approval_uuid) REFERENCES approvals (approval_uuid),
        FOREIGN KEY(line_item_id) REFERENCES line_items (id)
);
CREATE TABLE line_item_statuses (
        item_approval_id INTEGER NOT NULL,
        approval_uuid VARCHAR NOT NULL,
        purchase_req_id VARCHAR NOT NULL,
        status VARCHAR(11) NOT NULL,
        created_at DATETIME NOT NULL,
        hold_until DATETIME,
        last_updated DATETIME NOT NULL,
        updated_by VARCHAR,
        updater_email VARCHAR,
        PRIMARY KEY (item_approval_id),
        FOREIGN KEY(approval_uuid) REFERENCES approvals (approval_uuid)
);
CREATE TABLE inbound_requests (
        id INTEGER NOT NULL,
        approval_uuid VARCHAR NOT NULL,
        purchase_req_uuid VARCHAR NOT NULL,
        purchase_req_id VARCHAR NOT NULL,
        raw_payload JSON NOT NULL,
        status VARCHAR(9) NOT NULL,
        error_message TEXT,
        created_at DATETIME NOT NULL,
        processed_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
        PRIMARY KEY (id),
        FOREIGN KEY(approval_uuid) REFERENCES approvals (approval_uuid),
        FOREIGN KEY(purchase_req_uuid) REFERENCES purchase_requests (uuid)
);
CREATE TABLE son_comments (
        id INTEGER NOT NULL,
        approval_uuid VARCHAR NOT NULL,
        purchase_req_id VARCHAR,
        comment_text TEXT,
        created_at DATETIME,
        son_requester VARCHAR NOT NULL,
        item_description VARCHAR,
        PRIMARY KEY (id),
        FOREIGN KEY(approval_uuid) REFERENCES approvals (approval_uuid)
);
CREATE TABLE approval_payload (
        id INTEGER NOT NULL,
        purchase_req_uuid VARCHAR NOT NULL,
        approval_uuid VARCHAR NOT NULL,
        purchase_req_id VARCHAR NOT NULL,
        item_funds VARCHAR NOT NULL,
        total_price FLOAT NOT NULL,
        target_status VARCHAR(11) NOT NULL,
        action VARCHAR(11) NOT NULL,
        co VARCHAR,
        created_at DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(purchase_req_uuid) REFERENCES purchase_requests (uuid),
        FOREIGN KEY(approval_uuid) REFERENCES approvals (approval_uuid)
);