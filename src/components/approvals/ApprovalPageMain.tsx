import { useState } from "react";
import { FormValues } from "../../types/formTypes";
import ApprovalTableDG from "./ApprovalTableDG";
import SearchBar from "./SearchBar";
import { Box } from "@mui/material";

/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
}

function ApprovalPageMain({onDelete, resetTable }: ApprovalTableProps) {
    const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
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
                <ApprovalTableDG
                    onDelete={(ID: string) =>
                        setDataBuffer(
                            dataBuffer.filter(
                                (item) => item.ID !== ID
                            )
                        )
                    }
                    resetTable={resetTable}
                    searchQuery={searchQuery}
                />
            </Box>
        </Box>
    )
}

export default ApprovalPageMain;