import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import {
  Box,
  TextField,
  Typography,
  Button
} from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import MoreDataButton from "./MoreDataButton";
import { FormValues } from "../../types/formTypes";
import { fetchSearchData } from "./SearchBar";
import Buttons from "../purchase_req/Buttons";
import { convertBOC } from "../../utils/bocUtils";
import WarningIcon from "@mui/icons-material/Warning";
import PendingIcon from "@mui/icons-material/Pending";
import SuccessIcon from "@mui/icons-material/CheckCircle";
import { useUUIDStore } from "../../services/UUIDService";

interface ApprovalTableProps {
  onDelete: (ID: string) => void;
  resetTable: () => void;
  searchQuery: string;
}

const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;
const API_URL_APPROVE_DENY  = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`;

async function fetchApprovalData() {
  const res = await fetch(API_URL_APPROVAL_DATA, {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` }
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default function ApprovalTableDG({ onDelete, resetTable, searchQuery }: ApprovalTableProps) {
  const queryClient = useQueryClient();
  const { data: searchData} = useQuery({ queryKey: ["search", searchQuery], queryFn: () => fetchSearchData(searchQuery) });
  const { data: approvalData } = useQuery({ queryKey: ["approvalData"], queryFn: fetchApprovalData });
  const [draftIRQ1, setDraftIRQ1] = useState<Record<string,string>>({});

  // track which groups are expanded
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const toggleRowExpanded = (key: string) =>
    setExpandedRows(prev => ({ ...prev, [key]: !prev[key] }));

  /******************************************************************************************* */
  

  // handle approve/deny
  const approveDenyMutation = useMutation({
    mutationFn: async ({ ID, action }: { ID: string, action: "approve" | "deny" }) => {
      const res = await fetch(API_URL_APPROVE_DENY, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}` 
        },
        body: JSON.stringify({ ID, action })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvalData"] }),
    onError: (error) => {
      console.error("Approval action failed:", error);
      toast.error("Approval action failed. Please try again.");
    }
  });

  // Handle Approval/Deny/Download
  const handleApprove = (ID: string) => approveDenyMutation.mutate({ ID, action: "approve" });
  const handleDeny = (ID: string) => approveDenyMutation.mutate({ ID, action: "deny" });
  const handleDownload = (ID: string) => { /* TODO: download logic */ console.log("download", ID); };

  // basee rows
  const baseRows = (searchQuery ? searchData : approvalData) || [];

  // ensure each has a UUID
  const rowsWithIds = baseRows.map((r: FormValues, i: number) =>
    r.UUID ? r : { ...r, UUID: `row-${i}` }
  );

  // group by ID
  const grouped = rowsWithIds.reduce((acc: Record<string, FormValues[]>, row: FormValues) => {
    const key = String(row.ID);
    (acc[key] ||= []).push(row);
    return acc;
  }, {});

  // FlatRow type
  type FlatRow =
    | { id: string; isGroup: true; groupKey: string; rowCount: number }
    | (FormValues & { id: string; isGroup?: false });

  // build flatRows array
  const flatRows: FlatRow[] = (Object.entries(grouped) as [string,FormValues[]][])
    .flatMap(([key, items]) => {
      const header: FlatRow = {
        ...items[0],           // <-- copy all data fields from the 1st item
        id:        `group-${key}`,
        isGroup:   true,
        groupKey:  key,
        rowCount:  items.length
      };

      if (!expandedRows[key]) {
        return [header];
      }

      const detailRows: FlatRow[] = items.slice(1).map(item => ({
        ...item,
        id: item.UUID!,
        isGroup: false
      }));
      return [header, ...detailRows];
    });

  // the "toggle" column for group headers
  const toggleColumn: GridColDef = {
    field: "__groupToggle",
    headerName: "",
    width: 200,
    sortable: false,
    filterable: false,
    renderCell: params => {
      const row = params.row as FlatRow;
      if (!row.isGroup) return null;
      return (
        <Box
          sx={{ display: "flex", alignItems: "center", cursor: "pointer" }}
          onClick={() => toggleRowExpanded(row.groupKey)}
        >
          {expandedRows[row.groupKey]
            ? <KeyboardArrowUpIcon fontSize="small" />
            : <KeyboardArrowDownIcon fontSize="small" />}
          <Box component="span" sx={{ ml: 1, fontWeight: "bold" }}>
            {row.groupKey} ({row.rowCount})
          </Box>
        </Box>
      );
    }
  };

  // your existing data columns
  const dataColumns: GridColDef[] = [
    {
      field: "IRQ1_ID",
      headerName: "IRQ1 #",
      width: 220,
      renderCell: params => {
        const id = params.row.ID;
        const val = draftIRQ1[id] || "";
        const isAssigned = !!params.row.IRQ1_ID;
        return (
          <Box sx={{ display: "flex", gap: 1 }}>
            <Buttons
              className="btn btn-maroon"
              disabled={!!val}
              label={val ? "Assigned" : "Assign"}
              onClick={() => console.log("assign IRQ1:", params.row)}
            />
            <TextField
              value={val}
              disabled={isAssigned}
              size="small"
              onChange={e => setDraftIRQ1(prev => ({ ...prev, [id]: e.target.value }))}
              sx={{
                width: "100px",
                backgroundColor: val ? "rgba(0,128,0,0.2)" : "white",
                "& .MuiOutlinedInput-root fieldset": {
                  borderColor: val ? "green" : "red",
                  borderWidth: 2
                }
              }}
            />
          </Box>
        );
      }
    },
    { field: "ID",               headerName: "ID",                width: 130 },
    { field: "requester",        headerName: "Requester",         width: 130 },
    {
      field: "budgetObjCode",
      headerName: "Budget Object Code",
      width: 150,
      renderCell: params => convertBOC(params.value)
    },
    { field: "fund",             headerName: "Fund",              width: 130 },
    { field: "location",         headerName: "Location",          width: 130 },
    {
      field: "quantity",
      headerName: "Quantity",
      type: "number",
      align: "center",
      width: 100
    },
    {
      field: "priceEach",
      headerName: "Price Each",
      type: "number",
      align: "center",
      width: 120,
      renderCell: params =>
        typeof params.value === "number" ? params.value.toFixed(2) : "0.00"
    },
    {
      field: "totalPrice",
      headerName: "Line Total",
      type: "number",
      align: "center",
      width: 120,
      renderCell: params =>
        typeof params.value === "number" ? params.value.toFixed(2) : "0.00"
    },
    {
      field: "itemDescription",
      headerName: "Item Description",
      align: "center",
      width: 200
    },
    {
      field: "justification",
      headerName: "Justification",
      align: "center",
      width: 130,
      renderCell: params => (
        <MoreDataButton name="Justification" data={params.value} />
      )
    },
    {
      field: "status",
      headerName: "Status",
      align: "center",
      width: 200,
      renderCell: params => (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 1,
            color: "black",
            backgroundColor:
              params.value === "NEW REQUEST"
                ? "#ff9800"
                : params.value === "PENDING"
                ? "#2196f3"
                : params.value === "APPROVED"
                ? "#4caf50"
                : params.value === "DENIED"
                ? "#f44336"
                : "#9e9e9e",
            fontWeight: "bold",
            width: "100%",
            height: "100%"
          }}
        >
          {params.value === "NEW REQUEST" && <WarningIcon />}
          {params.value === "PENDING"     && <PendingIcon />}
          {params.value === "APPROVED"    && <SuccessIcon />}
          {params.value}
        </Box>
      )
    },
    {
      field: "actions",
      headerName: "Actions",
      width: 300,
      sortable: false,
      renderCell: params => (
        <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
          <Button
            variant="contained"
            color="success"
            onClick={() => handleApprove(params.row.ID)}
            disabled={params.row.status === "APPROVED"}
          >
            Approve
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => handleDeny(params.row.ID)}
            disabled={params.row.status === "DENIED"}
          >
            Deny
          </Button>
          <Button variant="contained" color="primary" onClick={() => handleDownload(params.row.ID)}>
            <DownloadOutlinedIcon />
          </Button>
          <Buttons
            className="btn btn-maroon"
            label="Delete"
            onClick={() => onDelete(params.row.ID)}
          />
        </Box>
      )
    }
  ];

  // combine toggle + data columns
  const allColumns = [toggleColumn, ...dataColumns];

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>Approval Table</Typography>
      <Box sx={{ height: "calc(100vh - 200px)", width: "100%" }}>
        <DataGrid
          rows={flatRows}
          columns={allColumns}
          getRowId={row => row.id}
          getRowClassName={({ row }) =>
            (row as FlatRow).isGroup ? "group-header-row" : ""
          }
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
          pageSizeOptions={[25, 50, 100]}
          disableRowSelectionOnClick
          rowHeight={60}
          sx={{
            background: "#2c2c2c",
            "& .MuiDataGrid-cell":        { color: "white", background: "#2c2c2c" },
            "& .MuiDataGrid-row":         { background: "#2c2c2c" },
            "& .MuiDataGrid-columnHeaders, .MuiDataGrid-columnHeader": {
              background: "linear-gradient(to top, #2c2c2c, #800000) !important",
              color: "white"
            },
            "& .MuiDataGrid-columnHeaderTitle": { fontWeight: "bold" },
            "& .MuiDataGrid-footer": { 
              background: "#2c2c2c", 
              color: "white !important",
              "& .MuiTablePagination-root": {
                color: "white !important",
                "& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows": {
                  color: "white !important"
                }
              }
            }
          }}
        />
      </Box>
      <style>{`
        .group-header-row .MuiDataGrid-cell {
          background-color: #3c3c3c !important;
          font-weight: bold;
        }
      `}</style>
    </Box>
  );
}
