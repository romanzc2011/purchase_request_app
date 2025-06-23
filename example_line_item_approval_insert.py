#!/usr/bin/env python3
"""
Example script showing how to insert data into the LineItemFinalApproval table.

This script demonstrates:
1. How to insert a new approval record
2. How to query existing approvals
3. How to update approval status
4. How to determine deputy approval eligibility

Usage:
    python example_line_item_approval_insert.py
"""

import asyncio
import sys
import os

# Add the api directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from sqlalchemy.ext.asyncio import AsyncSession
from api.services.db_service import (
    get_async_session,
    insert_line_item_final_approval,
    get_line_item_final_approvals_by_line_item_uuid,
    get_line_item_final_approvals_by_approval_uuid,
    update_line_item_final_approval_status,
    can_deputy_approve
)
from api.schemas.purchase_schemas import ItemStatus


async def example_insert_approval():
    """Example of inserting a new approval record."""
    print("=== Example: Inserting New Approval ===")
    
    async for db in get_async_session():
        try:
            # Example data - you would get these from your actual approval process
            approvals_uuid = "example-approval-uuid-123"
            line_item_uuid = "example-line-item-uuid-456"
            task_id = 789
            approver = "john.doe"
            status = ItemStatus.APPROVED
            pending_approval_status = ItemStatus.PENDING_APPROVAL
            total_price = 150.0  # $150 - deputy can approve
            
            # Determine if deputy can approve
            deputy_can_approve_flag = can_deputy_approve(total_price)
            print(f"Total price: ${total_price}")
            print(f"Deputy can approve: {deputy_can_approve_flag}")
            
            # Insert the approval record
            final_approval = await insert_line_item_final_approval(
                db=db,
                approvals_uuid=approvals_uuid,
                line_item_uuid=line_item_uuid,
                task_id=task_id,
                approver=approver,
                status=status,
                pending_approval_status=pending_approval_status,
                deputy_can_approve=deputy_can_approve_flag
            )
            
            print(f"Successfully inserted approval:")
            print(f"  - Approvals UUID: {final_approval.approvals_uuid}")
            print(f"  - Line Item UUID: {final_approval.line_item_uuid}")
            print(f"  - Task ID: {final_approval.task_id}")
            print(f"  - Approver: {final_approval.approver}")
            print(f"  - Status: {final_approval.status}")
            print(f"  - Deputy Can Approve: {final_approval.deputy_can_approve}")
            print(f"  - Created At: {final_approval.created_at}")
            
        except Exception as e:
            print(f"Error inserting approval: {e}")
        finally:
            await db.close()


async def example_query_approvals():
    """Example of querying existing approvals."""
    print("\n=== Example: Querying Approvals ===")
    
    async for db in get_async_session():
        try:
            # Example line item UUID to query
            line_item_uuid = "example-line-item-uuid-456"
            
            # Get all approvals for this line item
            approvals = await get_line_item_final_approvals_by_line_item_uuid(
                db=db,
                line_item_uuid=line_item_uuid
            )
            
            print(f"Found {len(approvals)} approval(s) for line item {line_item_uuid}:")
            for approval in approvals:
                print(f"  - Approver: {approval.approver}")
                print(f"    Status: {approval.status}")
                print(f"    Deputy Can Approve: {approval.deputy_can_approve}")
                print(f"    Created: {approval.created_at}")
                print()
                
        except Exception as e:
            print(f"Error querying approvals: {e}")
        finally:
            await db.close()


async def example_update_approval():
    """Example of updating an approval status."""
    print("\n=== Example: Updating Approval Status ===")
    
    async for db in get_async_session():
        try:
            # Example data
            approvals_uuid = "example-approval-uuid-123"
            line_item_uuid = "example-line-item-uuid-456"
            task_id = 789
            new_status = ItemStatus.DENIED
            approver = "jane.smith"
            
            # Update the approval status
            updated_approval = await update_line_item_final_approval_status(
                db=db,
                approvals_uuid=approvals_uuid,
                line_item_uuid=line_item_uuid,
                task_id=task_id,
                new_status=new_status,
                approver=approver
            )
            
            print(f"Successfully updated approval status:")
            print(f"  - New Status: {updated_approval.status}")
            print(f"  - Updated By: {updated_approval.approver}")
            print(f"  - Updated At: {updated_approval.created_at}")
            
        except Exception as e:
            print(f"Error updating approval: {e}")
        finally:
            await db.close()


async def example_deputy_approval_logic():
    """Example of deputy approval logic."""
    print("\n=== Example: Deputy Approval Logic ===")
    
    # Test different price scenarios
    test_prices = [100.0, 250.0, 500.0, 1000.0]
    
    for price in test_prices:
        can_approve = can_deputy_approve(price)
        print(f"Price: ${price:,.2f} -> Deputy can approve: {can_approve}")


async def main():
    """Main function to run all examples."""
    print("LineItemFinalApproval Insert Examples")
    print("=" * 50)
    
    # Run examples
    await example_deputy_approval_logic()
    await example_insert_approval()
    await example_query_approvals()
    await example_update_approval()
    
    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main()) 