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
} from "@mui/material";
import { FormValues } from "../../types/formTypes";
import { convertBOC } from "../../utils/bocUtils";
import { IFile } from "../../types/File";
import { useState } from "react";
import { uploadFile } from "../../services/FileUploadHandler";
import FileUpload from "./FileUpload";

/* INTERFACE */
interface SubmitApprovalTableProps {
  dataBuffer: FormValues[];
  onDelete: (req_id: string) => void;
  fileInfo: IFile;
  reqID: string;
  setFileInfos: React.Dispatch<React.SetStateAction<IFile[]>>;
  //resetTable: () => void;
}

const SubmitApprovalTable: React.FC<SubmitApprovalTableProps> = ({
  dataBuffer,
  onDelete,
  fileInfo,
  reqID
  //resetTable,
}) => {
  const [fileInfos, setFileInfos] = useState<IFile[]>([]);

  // Check if any file is not uploaded, user may have already uploaded
  const filesPendingUpload = fileInfos.some(file => file.status !== "success");

  // Preprocess data to calculate price
  const processedData = dataBuffer.map((item) => ({
    ...item,
    calculatedPrice: (item.price || 0) * (item.quantity || 1), // Calculating based on quantity
  }));

  /************************************************************************************ */
  /* SUBMIT DATA --- send to backend to add to database */
  /************************************************************************************ */
  const handleSubmitData = (dataBuffer: FormValues[]) => {
    // Find all file not uploaded
    const filesToUpload = fileInfos.filter(file => file.status !== "success");
    
    if(filesToUpload.length > 0) {
      console.log("Uploading remaining files");
      setIsUploading(true);

      // Upload all pending files
      for(const file of filesToUpload) {
          uploadFile(file, reqID, setFileInfos);
      }

      setIsUploading(false); // Uploading done
      return;
    }

    // Retrieve access to from local storage
    const accessToken = localStorage.getItem("access_token");
    console.log("TOKEN: ",accessToken);
    fetch(`https://${window.location.hostname}:5002/api/sendToPurchaseReq`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`
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
                  color="error"
                  onClick={() => {
                    onDelete(item.req_id);
                  }}
                >
                  Delete
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>

        {/* FOOTER WITH FILE UPLOAD & SUBMIT BUTTON */}
        <tfoot>
          <TableRow>
            <TableCell colSpan={4}>
              {/* Show a warning if files are pending upload */}
              {filesPendingUpload && (
                <p style={{ color: "red", fontWeight: "bold" }}>
                    ⚠️ Some files are not uploaded yet. Upload them before submitting.              
                </p>
              )}

              {/* Upload Component */}
              <FileUpload reqID={reqID} setFileInfos={setFileInfos} />
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

            <TableCell
              colSpan={2}
              sx={{ color: "white", textAlign: "right" }}
            ></TableCell>
            <TableCell
              colSpan={2}
              sx={{ color: "white", fontWeight: "bold", textAlign: "right" }}
            >
              Total: $
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
