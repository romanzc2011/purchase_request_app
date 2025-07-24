import { useState, useCallback } from "react";
import React from "react";
import ApprovalTable from "../ui/ApprovalTable";
import SearchBar from "../ui/SearchBar";
import { Box } from "@mui/material";
import { DataRow } from "../../../types/approvalTypes";
/* INTERFACE */
interface ApprovalTableProps {
	onDelete: (ID: string) => void;
	resetTable: () => void;
}

const ApprovalPageMain = React.memo(({ resetTable }: ApprovalTableProps) => {
	const [dataBuffer, setDataBuffer] = useState<DataRow[]>([]);
	const [searchQuery, setSearchQuery] = useState("");

	// Optimize event handlers with useCallback
	const handleDelete = useCallback((ID: string) => {
		setDataBuffer(prevData =>
			prevData.filter(item => item.ID !== ID)
		);
	}, []);

	const handleClearSearch = useCallback(() => {
		setSearchQuery("");
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
					onDelete={handleDelete}
					resetTable={resetTable}
					searchQuery={searchQuery}
					onClearSearch={handleClearSearch}
				/>
			</Box>
		</Box>
	)
});

ApprovalPageMain.displayName = 'ApprovalPageMain';

export default ApprovalPageMain;