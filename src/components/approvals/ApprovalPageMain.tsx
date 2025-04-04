import { useState } from "react";
import { FormValues } from "../../types/formTypes";
import ApprovalsTable from "./ApprovalTable";
import SearchBar from "./SearchBar";

/* INTERFACE */
interface ApprovalTableProps {
    onDelete: (ID: number) => void;
    resetTable: () => void;
}

function ApprovalPageMain({onDelete, resetTable }: ApprovalTableProps) {
    const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    
    return (
        <div>
            <SearchBar setSearchQuery={setSearchQuery} />
            <ApprovalsTable
                onDelete={(ID: number) =>
                    setDataBuffer(
                        dataBuffer.filter(
                            (item) => item.ID !== ID.toString()
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
