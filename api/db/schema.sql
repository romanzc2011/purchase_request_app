CREATE TABLE purchase_requests (
        id INTEGER NOT NULL,
        request_id VARCHAR NOT NULL,
        uuid VARCHAR,
        requester VARCHAR,
        phoneext INTEGER,
        datereq DATE,
        dateneed DATE,
        order_type VARCHAR,
        status VARCHAR(16) NOT NULL,
        created_time DATETIME NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (request_id),
        UNIQUE (uuid)
);
CREATE TABLE users (
        id INTEGER NOT NULL,
        username VARCHAR NOT NULL,
        email VARCHAR NOT NULL,
        department VARCHAR NOT NULL,
        PRIMARY KEY (id)
);
CREATE TABLE purchase_request_line_items (
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
        status VARCHAR(16),
        created_time DATETIME NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY(purchase_request_uuid) REFERENCES purchase_requests (uuid)
);
CREATE INDEX ix_purchase_request_line_items_purchase_request_uuid ON purchase_request_line_items (purchase_request_uuid);
CREATE TABLE approvals (
        id INTEGER NOT NULL,
        uuid VARCHAR NOT NULL,
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
        status VARCHAR(16) NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (irq1_id),
        FOREIGN KEY(purchase_request_uuid) REFERENCES purchase_requests (uuid)
);
CREATE TABLE pending_approvals (
        task_id INTEGER NOT NULL,
        purchase_request_uuid VARCHAR NOT NULL,
        purchase_request_line_item_id INTEGER,
        assigned_group VARCHAR NOT NULL,
        status VARCHAR(9) NOT NULL,
        item_status VARCHAR(11) NOT NULL,
        created_at DATETIME NOT NULL,
        processed_at DATETIME,
        error_message TEXT,
        PRIMARY KEY (task_id),
        FOREIGN KEY(purchase_request_uuid) REFERENCES purchase_requests (uuid),
        FOREIGN KEY(purchase_request_line_item_id) REFERENCES purchase_request_line_items (id)
);
CREATE INDEX ix_pending_approvals_purchase_request_line_item_id ON pending_approvals (purchase_request_line_item_id);
CREATE INDEX ix_pending_approvals_purchase_request_uuid ON pending_approvals (purchase_request_uuid);
CREATE TABLE line_item_approvals (
        id INTEGER NOT NULL,
        approvals_uuid VARCHAR,
        purchase_req_line_item_id INTEGER,
        approver VARCHAR,
        decision VARCHAR(11),
        comments TEXT,
        created_at DATETIME,
        PRIMARY KEY (id),
        FOREIGN KEY(approvals_uuid) REFERENCES approvals (uuid),
        FOREIGN KEY(purchase_req_line_item_id) REFERENCES purchase_request_line_items (id)
);
CREATE TABLE son_comments (
        id INTEGER NOT NULL,
        approvals_uuid VARCHAR NOT NULL,
        purchase_request_id VARCHAR,
        comment_text TEXT,
        created_at DATETIME,
        son_requester VARCHAR NOT NULL,
        item_description VARCHAR,
        PRIMARY KEY (id),
        FOREIGN KEY(approvals_uuid) REFERENCES approvals (uuid)
);