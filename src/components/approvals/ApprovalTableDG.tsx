import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

const API_URL_ASSIGN = `${import.meta.env.VITE_API_URL}/api/assignIRQ1_ID`;
const API_URL_APPROVE_DENY = `${import.meta.env.VITE_API_URL}/api/approveDenyRequest`;
const API_URL_APPROVAL_DATA = `${import.meta.env.VITE_API_URL}/api/getApprovalData`;

async function fetchApprovalData() {
  const response = await fetch(API_URL_APPROVAL_DATA, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
    },
  });
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

function ApprovalTableDG({
  searchQuery,
  onDelete,
  resetTable,
}: ApprovalTableProps) {
  const queryClient = useQueryClient();
  const { getUUID } = useUUIDStore();
  
  const { data: searchData } = useQuery({
    queryKey: ["search_data", searchQuery],
    queryFn: () => fetchSearchData(searchQuery),
  });

  const { data: approvalData } = useQuery({
    queryKey: ["approval_data"],
    queryFn: fetchApprovalData,
  });

  const rows = searchQuery ? searchData || [] : approvalData || [];

  // Ensure each row has a UUID
  const rowsWithIds = rows.map((row: FormValues, index: number) => {
    if (!row.UUID) {
      return { ...row, UUID: `row-${index}` };
    }
    return row;
  });

  const handleAssignIRQ1 = (row: any) => {
    // TODO: Implement IRQ1 assignment
    console.log("Assign IRQ1 for row:", row);
  };

  const handleIRQ1Change = (row: any, value: string) => {
    // TODO: Implement IRQ1 change
    console.log("IRQ1 changed for row:", row, "to:", value);
  };

  const handleApprove = (row: any) => {
    // TODO: Implement approve functionality
    console.log("Approve row:", row);
  };

  const handleDeny = (row: any) => {
    // TODO: Implement deny functionality
    console.log("Deny row:", row);
  };

  const handleDownload = (row: any) => {
    // TODO: Implement download functionality
    console.log("Download row:", row);
  };

  const columns: GridColDef[] = [
    {
      field: 'IRQ1_ID',
      headerName: 'IRQ1 #',
      width: 150,
      renderCell: (params) => (
        <Box sx={{ display: "flex", gap: "5px" }}>
          <Buttons
            className="btn btn-maroon"
            disabled={Boolean(params.row.IRQ1_ID)}
            label={params.row.IRQ1_ID ? "Assigned" : "Assign"}
            onClick={() => handleAssignIRQ1(params.row)}
          />
          <TextField
            id="IRQ1_ID"
            value={params.row.IRQ1_ID || ''}
            disabled={Boolean(params.row.IRQ1_ID)}
            className="form-control"
            fullWidth
            variant="outlined"
            size="small"
            onChange={(e) => handleIRQ1Change(params.row, e.target.value)}
            sx={{
              backgroundColor: params.row.IRQ1_ID ? 'rgba(0, 128, 0, 0.2)' : 'white',
              width: '100px',
              '& .MuiOutlinedInput-root': {
                '& fieldset': {
                  borderColor: params.row.IRQ1_ID ? 'green' : 'red',
                  borderWidth: '2px',
                },
                '&.Mui-disabled': {
                  backgroundColor: 'rgba(0, 128, 0, 0.2)',
                  '& .MuiOutlinedInput-input': {
                    color: '#00ff00',
                    WebkitTextFillColor: '#00ff00',
                  },
                },
              },
            }}
          />
        </Box>
      )
    },
    { field: 'ID', headerName: 'ID', width: 130 },
    { field: 'requester', headerName: 'Requester', width: 130 },
    { 
      field: 'budgetObjCode', 
      headerName: 'Budget Object Code', 
      width: 150,
      renderCell: (params) => convertBOC(params.value)
    },
    { field: 'fund', headerName: 'Fund', width: 130 },
    { field: 'location', headerName: 'Location', width: 130 },
    { 
      field: 'quantity', 
      headerName: 'Quantity', 
      width: 100,
      align: 'center',
      type: 'number'
    },
    { 
      field: 'priceEach', 
      headerName: 'Price Each', 
      width: 120,
      align: 'center',
      type: 'number',
      renderCell: (params) => (
        typeof params.value === "number" ? params.value.toFixed(2) : "0.00"
      )
    },
    { 
      field: 'totalPrice', 
      headerName: 'Line Total', 
      width: 120,
      align: 'center',
      type: 'number',
      renderCell: (params) => (
        typeof params.value === "number" ? params.value.toFixed(2) : "0.00"
      )
    },
    { 
      field: 'itemDescription', 
      headerName: 'Item Description', 
      width: 200,
      align: 'center'
    },
    { 
      field: 'justification', 
      headerName: 'Justification', 
      width: 130,
      align: 'center',
      renderCell: (params) => (
        <MoreDataButton
          name="Justification"
          data={params.value}
        />
      )
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 200,
      align: 'center',
      renderCell: (params) => (
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          gap: 1,
          color: "black",
          backgroundColor: 
            params.value === "NEW REQUEST" ? "#ff9800" :
            params.value === "PENDING" ? "#2196f3" :
            params.value === "APPROVED" ? "#4caf50" :
            params.value === "DENIED" ? "#f44336" :
            "#9e9e9e",
          fontWeight: "bold",
          width: '100%',
          height: '100%'
        }}>
          {params.value === "NEW REQUEST" && <WarningIcon />}
          {params.value === "PENDING" && <PendingIcon />}
          {params.value === "APPROVED" && <SuccessIcon />}
          {params.value}
        </Box>
      )
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 300,
      sortable: false,
      renderCell: (params) => (
        <Box sx={{ 
          display: 'flex', 
          gap: 1,
          height: '100%',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Button
            variant="contained"
            color="success"
            onClick={() => handleApprove(params.row)}
            disabled={params.row.status === "APPROVED"}
          >
            Approve
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => handleDeny(params.row)}
            disabled={params.row.status === "DENIED"}
          >
            Deny
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handleDownload(params.row)}
          >
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

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>Approval Table</Typography>
      <Box sx={{ height: "calc(100vh - 200px)", width: "100%", position: "relative", zIndex: 1 }}>
        <DataGrid
          rows={rowsWithIds}
          columns={columns}
          getRowId={(row) => row.UUID}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
          pageSizeOptions={[25, 50, 100]}
          disableRowSelectionOnClick
          rowHeight={60}
          sx={{
            background: "#2c2c2c",
            color: "white",
            '& .MuiDataGrid-cell': {
              color: "white",
              backgroundColor: "#2c2c2c",
            },
            '& .MuiDataGrid-row': {
              backgroundColor: "#2c2c2c",
            },
            '& .MuiDataGrid-columnHeaders': {
              background: "linear-gradient(to top, #2c2c2c, #800000) !important",
              color: "white",
            },
            '& .MuiDataGrid-columnHeader': {
              background: "linear-gradient(to top, #2c2c2c, #800000) !important",
              color: "white",
            },
            '& .MuiDataGrid-columnHeaderTitle': {
              color: "white",
              fontWeight: "bold",
            },
            '& .MuiDataGrid-footer': {
              backgroundColor: "#2c2c2c",
              color: "white",
            },
            '& .MuiDataGrid-virtualScroller': {
              overflow: 'auto',
              position: 'relative',
              zIndex: 1,
            },
            '& .MuiDataGrid-virtualScrollerContent': {
              minWidth: '100%',
            },
            '& .MuiDataGrid-virtualScrollerRenderZone': {
              position: 'relative',
              zIndex: 1,
            },
            '& .MuiDataGrid-virtualScrollerScrollbar': {
              zIndex: 10,
              position: 'relative',
            },
            '& .MuiDataGrid-virtualScrollerScrollbarVertical': {
              zIndex: 10,
            },
            '& .MuiDataGrid-virtualScrollerScrollbarHorizontal': {
              zIndex: 10,
            },
            '& .MuiDataGrid-virtualScrollerScrollbarVertical .MuiDataGrid-virtualScrollerScrollbarTrack': {
              backgroundColor: '#2c2c2c',
              zIndex: 10,
            },
            '& .MuiDataGrid-virtualScrollerScrollbarVertical .MuiDataGrid-virtualScrollerScrollbarThumb': {
              backgroundColor: '#800000',
              zIndex: 10,
            },
            '& .MuiDataGrid-virtualScrollerScrollbarVertical .MuiDataGrid-virtualScrollerScrollbarThumb:hover': {
              backgroundColor: '#a00000',
            },
          }}
        />
      </Box>
    </Box>
  );
}

export default ApprovalTableDG;
