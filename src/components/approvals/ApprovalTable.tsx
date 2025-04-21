import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  IconButton,
  Collapse,
  Typography,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ApprovalsTableRow from "./ApprovalsTableRow";
import MoreDataButton from "./MoreDataButton";
import { FormValues } from "../../types/formTypes";
import { fetchSearchData } from "./SearchBar";

interface ApprovalTableProps {
  onDelete: (ID: string) => void;
  resetTable: () => void;
  searchQuery: string;
}

const API_CALL1 = "/api/getApprovalData";
const API_URL1 = `${import.meta.env.VITE_API_URL}${API_CALL1}`;

async function fetchApprovalData() {
  const response = await fetch(API_URL1, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
    },
  });
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
}

export default function ApprovalTable({
  searchQuery,
  onDelete,
  resetTable,
}: ApprovalTableProps) {
  const { data: searchData } = useQuery({
    queryKey: ["search_data", searchQuery],
    queryFn: () => fetchSearchData(searchQuery),
  });

  const { data: approvalData } = useQuery({
    queryKey: ["approval_data"],
    queryFn: fetchApprovalData,
  });

  const rows: FormValues[] = searchQuery
    ? searchData || []
    : approvalData || [];

  const groupedRows = rows.reduce<Record<string, FormValues[]>>((acc, row) => {
    const id = String(row.ID);
    (acc[id] = acc[id] || []).push(row);
    return acc;
  }, {});

  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>(
    {}
  );
  const toggleRowExpanded = (id: string) =>
    setExpandedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));

  return (
    <Box sx={{ overflowX: "auto", height: "100vh", width: "100%" }}>
      <TableContainer
        component={Paper}
        sx={{
          background: "#2c2c2c",
          color: "white",
          borderRadius: 2,
          mt: 2,
          width: "100%",
        }}
      >
        <Table sx={{ minWidth: 800, width: "100%" }}>
          <TableHead
            sx={{ background: "linear-gradient(to bottom, #2c2c2c, #800000)" }}
          >
            <TableRow>
              <TableCell sx={{ width: 40 }} /> {/* expand/collapse */}
              {[
                "REQUISITION #",
                "ID",
                "REQUESTER",
                "BUDGET OBJECT CODE",
                "FUND",
                "LOCATION",
                "QUANTITY",
                "PRICE EACH",
                "LINE TOTAL",
                "ITEM DESCRIPTION",
                "JUSTIFICATION",
                "STATUS",
                "ACTIONS",
              ].map((label) => (
                <TableCell
                  key={label}
                  sx={{
                    color: "white",
                    fontWeight: "bold",
                    textAlign: "center",
                    p: "8px 16px",
                  }}
                >
                  {label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody sx={{ textAlign: "center" }}>
            {Object.entries(groupedRows).map(([id, items]) => (
              <React.Fragment key={id}>
                {/* use your row component for the main row */}
                <ApprovalsTableRow
                  approval_data={items[0]}
                  expandButton={
                    <IconButton
                      size="small"
                      onClick={() => toggleRowExpanded(id)}
                      sx={{ color: "white" }}
                    >
                      {expandedRows[id] ? (
                        <KeyboardArrowUpIcon />
                      ) : (
                        <KeyboardArrowDownIcon />
                      )}
                    </IconButton>
                  }
                />

                {/* collapsible extra rows */}
                {items.length > 1 && (
                  <TableRow>
                    <TableCell
                      colSpan={14}
                      sx={{ p: 0, background: "#3c3c3c" }}
                    >
                      <Collapse
                        in={expandedRows[id]}
                        timeout="auto"
                        unmountOnExit
                      >
                        <Box sx={{ m: 2 }}>
                          <Typography
                            variant="h6"
                            gutterBottom
                            component="div"
                            sx={{ color: "white" }}
                          >
                            Additional Items
                          </Typography>
                          <Table size="small" aria-label="additional items">
                            <TableHead>
                              <TableRow>
                                {[
                                  "ID",
                                  "BUDGET OBJECT CODE",
                                  "FUND",
                                  "LOCATION",
                                  "QUANTITY",
                                  "PRICE EACH",
                                  "LINE TOTAL",
                                  "ITEM DESCRIPTION",
                                  "JUSTIFICATION",
                                ].map((label) => (
                                  <TableCell
                                    key={label}
                                    sx={{
                                      color: "white",
                                      fontWeight: "bold",
                                    }}
                                  >
                                    {label}
                                  </TableCell>
                                ))}
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {items.slice(1).map((item, idx) => (
                                <TableRow key={idx}>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.ID}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.budgetObjCode}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.fund}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.location}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.quantity}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.priceEach}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.totalPrice}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    {item.itemDescription}
                                  </TableCell>
                                  <TableCell sx={{ color: "white" }}>
                                    <MoreDataButton
                                      name="Justification"
                                      data={item.justification}
                                    />
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
          </TableBody>

          <tfoot>
            <TableRow>
              <TableCell colSpan={9} />
              <TableCell
                colSpan={2}
                sx={{ color: "white", textAlign: "right" }}
              />
              <TableCell
                colSpan={4}
                sx={{ color: "white", fontWeight: "bold", textAlign: "right" }}
              >
                Total: $
                {rows
                  .reduce(
                    (acc, approval_data) =>
                      acc + (Number(approval_data.totalPrice) || 0),
                    0
                  )
                  .toFixed(2)}
              </TableCell>
            </TableRow>
          </tfoot>
        </Table>
      </TableContainer>
    </Box>
  );
}
