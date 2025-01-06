import React, { useState } from "react";
import { useForm } from "react-hook-form";
import Buttons from "../purchase_req/purchase_req_components/Buttons";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Typography,
} from "@mui/material";
import { FormValues } from "../../types/formTypes";
import { convertBOC } from "../../utils/bocUtils";

/* INTERFACE */
interface ApprovalTableProps {
  dataBuffer: FormValues[];
  onDelete: (req_id: number) => void;
  resetTable: () => void;
}

const ApprovalsTable: React.FC<ApprovalTableProps> = ({
  dataBuffer,
  onDelete,
  resetTable,
}) => {
  // Preprocess data to calculate price
  const processedData = dataBuffer.map((item) => ({
    ...item,
    calculatedPrice: (item.price || 0) * (item.quantity || 1), // Calculating based on quantity
  }));

  /************************************************************************************ */
  /* GET REQUEST DATA --- send to backend to add to database */
  /************************************************************************************ */
  const handleSubmitData = (dataBuffer: FormValues[]) => {
    fetch("http://127.0.0.1:5000/getRequests", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ dataBuffer }),
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        console.log("Response from POST request: ", data);
        resetTable();
      })
      .catch((err) => console.error("Error sending data:", err));
  };

  /************************************************************************************ */
  /* APPROVE OR DENY */
  /************************************************************************************ */
  const handleApprove = () => {};

  const handleDeny = () => {};

  return (
    <TableContainer
      component={Paper}
      sx={{
        background: " #2c2c2c",
        color: "white", // Ensure text contrast
        borderRadius: "10px",
        overflow: "hidden", // Ensure rounded corners
        width: "100%",
      }}
    >
      <Table sx={{ width: "100%", tableLayout: "auto" }}>
        <TableHead
          sx={{ background: "linear-gradient(to bottom, #2c2c2c, #800000)" }}
        >
          <TableRow>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Requisition ID
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Budget Object Code
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Fund
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Location
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Quantity
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Price Each
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Estimated Price
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {processedData.map((item) => (
            <TableRow key={item.req_id}>
              <TableCell sx={{ color: "white" }}>{item.req_id}</TableCell>
              <TableCell sx={{ color: "white" }}>
                {convertBOC(item.budgetObjCode)}
              </TableCell>
              <TableCell sx={{ color: "white" }}>{item.fund}</TableCell>
              <TableCell sx={{ color: "white" }}>{item.location}</TableCell>
              <TableCell sx={{ color: "white" }}>{item.quantity}</TableCell>
              <TableCell sx={{ color: "white" }}>
                {item.price.toFixed(2)}
              </TableCell>
              <TableCell sx={{ color: "white" }}>
                {item.calculatedPrice.toFixed(2)}
              </TableCell>
              <TableCell>
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleApprove}
                >
                  Approve
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  onClick={handleDeny}
                >
                  Deny
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <tfoot>
          <TableRow>
            <TableCell colSpan={4}>
              {/************************************************************************************ */}
              {/* BUTTONS: SUBMIT/PRINT */}
              {/************************************************************************************ */}
              {/* Submit data to proper destination, email to supervisor or notify sup that there's a request for them to approve */}
              <Buttons
                label="Submit Form"
                className=" me-3 btn btn-maroon"
                disabled={dataBuffer.length === 0}
                onClick={() => {
                  handleSubmitData(dataBuffer);
                }}
              />

              {/* This button will print out item Request */}
              <Buttons label="Print Form" className="btn btn-maroon" />
            </TableCell>

            <TableCell colSpan={2} sx={{ color: "white", textAlign: "right" }}>
              <Typography
                variant="h6"
                component="div"
                sx={{ fontWeight: "bold" }}
              >
                Total:
              </Typography>
            </TableCell>
            <TableCell colSpan={2} sx={{ color: "white", fontWeight: "bold" }}>
              $
              {processedData
                .reduce(
                  (acc, item) => acc + (Number(item.calculatedPrice) || 0),
                  0
                )
                .toFixed(2)}
            </TableCell>
          </TableRow>
        </tfoot>
      </Table>
    </TableContainer>
  );
};

export default ApprovalsTable;
