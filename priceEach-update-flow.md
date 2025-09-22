# PriceEach Update Flow - Step-by-Step Map

## Overview
This document maps out how `priceEach` updates are persisted in the purchase request system.

## Step-by-Step Process

### 1. User Interaction
- User clicks on `priceEach` cell in DataGrid
- User types new price value
- User presses Enter or clicks outside cell

### 2. DataGrid Processing
- **File**: `ApprovalTable.tsx` (line 1055)
- **Trigger**: `processRowUpdate={handleEditPriceEach}`
- **Function**: `handleEditPriceEach` from `useApprovalHandlers`

### 3. Handler Function Execution
- **File**: `useApprovalHandlers.ts` (lines 211-239)
- **Function**: `handleEditPriceEach(newRow: DataRow, oldRow: DataRow)`
- **Validation**: Skip group headers, extract data

### 4. Data Preparation
```tsx
let newPriceEach = newRow.priceEach;        // New price from user
const quantity = newRow.quantity;           // Existing quantity
let newTotalPrice = newPriceEach * quantity; // Calculate new total
const item_uuid = newRow.UUID;              // Item identifier
const purchase_request_id = newRow.ID;      // Request identifier
```

### 5. Backend API Call
- **File**: `useApprovalHandlers.ts` (lines 127-156)
- **Function**: `updatePriceEachTotalPrice()`
- **API Endpoint**: `API_URL_UPDATE_PRICES` (POST request)
- **Payload**:
  ```json
  {
    "purchase_request_id": "string",
    "item_uuid": "string",
    "new_price_each": number,
    "new_total_price": number,
    "status": "ItemStatus"
  }
  ```

### 6. Backend Processing
- **Backend**: Receives POST request to `/api/updatePrices`
- **Database**: Updates `priceEach` and `totalPrice` in database
- **Validation**: Checks price allowance limits
- **Response**: Success or error

### 7. Success Path
- **Backend Response**: API returns success
- **Return Value**: `{ ...newRow, priceEach: newPriceEach, totalPrice: newTotalPrice }`
- **DataGrid Update**: Cell shows new value
- **Database**: Changes are permanently saved

### 8. Error Path
- **Backend Error**: API returns error (e.g., price allowance exceeded)
- **Catch Block**: Error is caught in try-catch
- **Revert**: Returns `{ ...oldRow, priceEach: oldRow.priceEach, totalPrice: oldRow.totalPrice }`
- **DataGrid Revert**: Cell reverts to original value
- **Database**: No changes made

### 9. Data Persistence
- **Database**: Changes are committed to database
- **React Query**: Cache is invalidated on next data fetch
- **UI**: DataGrid reflects the new values

## Key Points
- **Immediate UI Update**: DataGrid shows new value immediately
- **Backend Validation**: Server checks business rules (price limits)
- **Error Handling**: Reverts UI if backend validation fails
- **Persistence**: Changes are saved to database permanently
- **Cache Management**: React Query cache gets updated on next fetch

## Files Involved
- `ApprovalTable.tsx` - DataGrid configuration
- `useApprovalHandlers.ts` - Business logic
- Backend API endpoint - Database persistence
- React Query - Cache management

## The persistence happens at Step 6 when the backend successfully updates the database!
