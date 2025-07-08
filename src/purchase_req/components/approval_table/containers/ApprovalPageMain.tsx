import { useState } from "react";
import ApprovalTable from "../ui/ApprovalTable";
import SearchBar from "../ui/SearchBar";
import { Box } from "@mui/material";
import { DataRow } from "../../../types/approvalTypes";
/* INTERFACE */
interface ApprovalTableProps {
	onDelete: (ID: string) => void;
	resetTable: () => void;
}

export default function ApprovalPageMain({ resetTable }: ApprovalTableProps) {
	const [dataBuffer, setDataBuffer] = useState<DataRow[]>([]);
	const [searchQuery, setSearchQuery] = useState("");

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
					onDelete={(ID: string) =>
						setDataBuffer(
							dataBuffer.filter(
								(item) => item.ID !== ID
							)
						)
					}
					resetTable={resetTable}
					searchQuery={searchQuery}
					onClearSearch={() => setSearchQuery("")}
				/>
			</Box>
		</Box>
	)
}