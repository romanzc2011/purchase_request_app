import { useState } from "react";
import { FormValues } from "../../types/formTypes";
//import ApprovalsTable from "./ApprovalTable";
import ApprovalTableDG from "./ApprovalTableDG";
import SearchBar from "./SearchBar";

/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: string) => void;
    resetTable: () => void;
}

function ApprovalPageMain({onDelete, resetTable }: ApprovalTableProps) {
    const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    
    return (
        <div>
            <SearchBar setSearchQuery={setSearchQuery} />
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
        </div>
    )
}

export default ApprovalPageMain;