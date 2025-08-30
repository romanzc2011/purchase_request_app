import { useState, useCallback } from "react";
import React from "react";
import ApprovalTable from "../ui/ApprovalTable";
import SearchBar from "../ui/SearchBar";
import { Box } from "@mui/material";
// import { DataRow } from "../../../types/approvalTypes";
/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
}

const ApprovalPageMain = React.memo(({ resetTable }: ApprovalTableProps) => {
    // const [dataBuffer, setDataBuffer] = useState<DataRow[]>([]);
    const [searchQuery, setSearchQuery] = useState("");


    const handleClearSearch = useCallback(() => {
        setSearchQuery("");
    }, []);

    const handleDelete = useCallback((ID: string) => {
        // TODO: Implement delete functionality
        console.log("Delete requested for ID:", ID);
    }, []);

    return (
        <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%'
        }}>
            <Box sx={{ mb: 2 }}>
                <SearchBar setSearchQuery={setSearchQuery} />
            </Box>
            <Box sx={{ flex: 1 }}>
                <ApprovalTable
                    resetTable={resetTable}
                    searchQuery={searchQuery}
                    onClearSearch={handleClearSearch}
                    onDelete={handleDelete}
                />
            </Box>
        </Box>
    )
});

ApprovalPageMain.displayName = 'ApprovalPageMain';

export default ApprovalPageMain;