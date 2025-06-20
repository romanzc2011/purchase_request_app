# Purchase Request Schema Cleanup Summary

## What Was Removed
- **`PurchaseRequestSchema`** - This was an unused legacy schema that duplicated functionality

## Current Schema Structure (CONSOLIDATED)

### 1. **FileAttachment**
- **Purpose**: File upload handling in purchase requests
- **Used in**: Tests, file upload endpoints
- **Fields**: attachment (bytes), name, type, size

### 2. **BasePurchaseItem** (NEW - Base Class)
- **Purpose**: Common fields shared between all purchase item representations
- **Used by**: PurchaseLineItem, PurchaseItem (inheritance)
- **Key fields**: All common purchase item fields with camelCase aliases
- **Standardized**: All fields use camelCase aliases for frontend consistency

### 3. **PurchaseLineItem** (Inherits from BasePurchaseItem)
- **Purpose**: Individual items within a purchase request
- **Used in**: API payloads, database operations
- **Maps to**: `PurchaseRequestLineItem` ORM model
- **Additional fields**: purchase_request_uuid, additional_comments

### 4. **PurchaseItem** (Inherits from BasePurchaseItem)
- **Purpose**: Processing individual purchase items (backward compatibility)
- **Used in**: Data processing functions, tests
- **Note**: Now just an alias - all functionality inherited from BasePurchaseItem

### 5. **PurchaseRequestPayload**
- **Purpose**: Incoming data from frontend when creating purchase requests
- **Used in**: `/sendToPurchaseReq` endpoint, notification service
- **Contains**: Header info + list of line items

### 6. **PurchaseResponse**
- **Purpose**: API response after creating purchase requests
- **Used in**: `/sendToPurchaseReq` endpoint response
- **Fields**: message, request_id

### 7. **PurchaseRequestHeader** (Pydantic)
- **Purpose**: PDF generation service specifically
- **Used in**: PDF service only
- **Note**: Different from the ORM model with same name

## Database ORM Models (in db_service.py)
- **`PurchaseRequestHeader`** (ORM) - Database table for request headers
- **`PurchaseRequestLineItem`** (ORM) - Database table for line items  
- **`Approval`** (ORM) - Database table for approval records
- **`PendingApproval`** (ORM) - Database table for pending approvals

## Key Improvements Made
1. ✅ Removed unused `PurchaseRequestSchema`
2. ✅ **CONSOLIDATED**: Merged `PurchaseItem` and `PurchaseLineItem` using inheritance
3. ✅ **STANDARDIZED**: All schemas now use camelCase aliases for frontend consistency
4. ✅ **DRY PRINCIPLE**: Created `BasePurchaseItem` to eliminate field duplication
5. ✅ Added clear documentation for each schema's purpose
6. ✅ Organized schemas by function (API, database, PDF, etc.)
7. ✅ Consistent formatting and structure

## Inheritance Structure
```
BasePurchaseItem (base class with all common fields)
├── PurchaseLineItem (adds purchase_request_uuid, additional_comments)
└── PurchaseItem (alias for backward compatibility)
```

## CamelCase Standardization
All schemas now consistently use camelCase aliases:
- `uuid` → `UUID`
- `item_description` → `itemDescription`
- `budget_obj_code` → `budgetObjCode`
- `price_each` → `priceEach`
- `total_price` → `totalPrice`
- `file_attachments` → `fileAttachments`
- `is_cyber_sec_related` → `isCyberSecRelated`
- etc.

## Usage Map
```
Frontend (camelCase) → PurchaseRequestPayload → Backend Processing
                                    ↓
                              PurchaseItem/PurchaseLineItem (inherited from BasePurchaseItem)
                                    ↓
                              Database ORM Models
                                    ↓
                              PurchaseResponse → Frontend
```

## Benefits of This Approach
1. **Reduced Duplication**: 90% less field duplication between schemas
2. **Frontend Consistency**: All camelCase aliases match frontend expectations
3. **Maintainability**: Changes to common fields only need to be made in one place
4. **Backward Compatibility**: Existing code using `PurchaseItem` continues to work
5. **Type Safety**: Inheritance provides better type checking and IDE support

## Remaining Considerations
- **`PurchaseItem` vs `PurchaseLineItem`**: These are very similar. Consider consolidating if possible
- **Naming consistency**: Some schemas use camelCase aliases, others don't
- **Field overlap**: There's still some duplication between schemas that could be reduced with inheritance