###################################################################
# Name: REQUISTION AND SEARCH SERVICE
# Author: ROMAN CAMPBELL
# Date: 03/20/2025
# Description:
"""
Requistion ID and Search Service for the search bar on the Approvals Table.
Put these two services together as they will both be dealing with the reqID.
For clarity and easy of searching the reqID will contain first 4 char of 
Requester's name, the 4 char of the BOC, Fund, and 4 char of location with the
4 char middle section of the uuid which will remain as the primary key of the
database. 
User will be able to search for orders based on any number of the sections of
req ID, functionality will also be added to search for requests based on status.
"""
###################################################################

###################################################################
# MAIN
def main():
    print("hello")

if __name__ == '__main__':
    main()