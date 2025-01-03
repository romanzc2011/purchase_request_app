import React, { useState } from "react";
import { useForm } from "react-hook-form";
import Buttons from "./Buttons";
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
import { FormValues } from "../types/formTypes";
import { convertBOC } from "../utils/bocUtils";

/* INTERFACE */
interface SubmitApprovalTableProps {
  dataBuffer: FormValues[];
  onDelete: (id: number) => void;
  //resetTable: () => void;
}

const SubmitApprovalTable: React.FC<SubmitApprovalTableProps> = ({
  dataBuffer,
  onDelete,
  //resetTable,
}) => {
  // Preprocess data to calculate price
  const processedData = dataBuffer.map((item) => ({
    ...item,
    calculatedPrice: (item.price || 0) * (item.quantity || 1), // Calculating based on quantity
  }));

  /************************************************************************************ */
  /* SUBMIT DATA --- send to backend to add to database */
  /************************************************************************************ */
  const handleSubmitData = (dataBuffer: FormValues[]) => {
    fetch("http://127.0.0.1:5000/getPurchaseData", {
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
        //resetTable();
      })
      .catch((err) => console.error("Error sending data:", err));
  };

  /************************************************************************************ */
  /* QUANTITY HOOK --- Update price base on quantity */
  const useQuantityPrice = (
    initialPrice: number,
    incrementQuantity: number
  ) => {
    const [price, setPrice] = useState(initialPrice);
    const quantity = () => setPrice(price * incrementQuantity);

    return [price, quantity] as const;
  };

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
              id
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
              Price
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {processedData.map((item) => (
            <TableRow key={item.id}>
              <TableCell sx={{ color: "white" }}>{item.id}</TableCell>
              <TableCell sx={{ color: "white" }}>
                {convertBOC(item.budgetObjCode)}
              </TableCell>
              <TableCell sx={{ color: "white" }}>{item.fund}</TableCell>
              <TableCell sx={{ color: "white" }}>{item.location}</TableCell>
              <TableCell sx={{ color: "white" }}>{item.quantity}</TableCell>
              <TableCell sx={{ color: "white" }}>
                {item.calculatedPrice.toFixed(2)}
              </TableCell>
              <TableCell>
                <Button
                  variant="contained"
                  color="error"
                  onClick={() => onDelete(item.id)}
                >
                  Delete
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

export default SubmitApprovalTable;
