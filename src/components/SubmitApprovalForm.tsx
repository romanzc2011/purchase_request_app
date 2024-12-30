import React from "react";
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

interface Purchase {
  BOC: number;
  fund: string;
  location: string;
  description: string;
  quantity: number;
  price: number;
  estimatedCost: number;
  justification: string;
}

interface PurchaseProps {
  purchases: Purchase[];
  onDelete: (BOC: number) => void;
}

const PurchaseList = ({ purchases, onDelete }: PurchaseProps) => {
  if (purchases.length === 0) return null;
  return (
    <TableContainer
      component={Paper}
      sx={{
        background: " #2c2c2c",
        color: "white", // Ensure text contrast
        borderRadius: "10px",
        overflow: "hidden", // Ensure rounded corners
      }}
    >
      <Table>
        <TableHead
          sx={{ background: "linear-gradient(to bottom, #2c2c2c, #800000)" }}
        >
          <TableRow>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              BOC
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Fund
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Location
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Description
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Quantity
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Price
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Estimated Cost
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Justification
            </TableCell>
            <TableCell sx={{ color: "white", fontWeight: "bold" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {purchases.map((purchase) => (
            <TableRow key={purchase.BOC}>
              <TableCell sx={{ color: "white" }}>{purchase.BOC}</TableCell>
              <TableCell sx={{ color: "white" }}>{purchase.fund}</TableCell>
              <TableCell sx={{ color: "white" }}>{purchase.location}</TableCell>
              <TableCell sx={{ color: "white" }}>
                {purchase.description}
              </TableCell>
              <TableCell sx={{ color: "white" }}>{purchase.quantity}</TableCell>
              <TableCell sx={{ color: "white" }}>{purchase.price}</TableCell>
              <TableCell sx={{ color: "white" }}>
                {purchase.estimatedCost}
              </TableCell>
              <TableCell sx={{ color: "white" }}>
                {purchase.justification}
              </TableCell>
              <TableCell>
                <Button
                  variant="contained"
                  color="error"
                  onClick={() => onDelete(purchase.BOC)}
                >
                  Delete
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <tfoot>
          <TableRow>
            <TableCell>
              {/************************************************************************************ */}
              {/* BUTTONS: SUBMIT/PRINT */}
              {/************************************************************************************ */}
              {/* Submit data to proper destination, email to supervisor or notify sup that there's a request for them to approve */}
              <Buttons label="Submit Form" />

              {/* This button will print out Purchase Request */}
              <Buttons label="Print Form" />
            </TableCell>

            <TableCell colSpan={7} sx={{ color: "white", textAlign: "right" }}>
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
              {purchases
                .reduce((acc, purchase) => purchase.estimatedCost + acc, 0)
                .toFixed(2)}
            </TableCell>
          </TableRow>
        </tfoot>
      </Table>
    </TableContainer>
  );
};

export default PurchaseList;
