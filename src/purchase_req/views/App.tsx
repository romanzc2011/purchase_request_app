import React, { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "../styles/App.css";
import { Routes, Route } from "react-router-dom";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import AddItemsForm from "../components/purchase_req_table/AddItemsForm";
import SubmitApprovalTable from "../components/purchase_req_table/SumbitToApproval";
import { Layout } from "../components/approval_table/app_layout";
import { Box, Toolbar } from "@mui/material";
import { FormValues } from "../types/formTypes";
import ApprovalPageMain from "../components/approval_table/containers/ApprovalPageMain";
import { IFile } from "../types/IFile";
import LoginDialog from "./LoginDialog";
import { usePurchaseForm } from "../hooks/usePurchaseForm";

interface AppProps {
	isLoggedIn: boolean;
	ACCESS_GROUP: boolean;
	CUE_GROUP: boolean;
	IT_GROUP: boolean;
}

function App({ isLoggedIn, ACCESS_GROUP, CUE_GROUP, IT_GROUP }: AppProps) {
	// Bring custom hook for purchase form
	const { createNewID } = usePurchaseForm();

	// Local state for reserved ID
	const [ID, setID] = useState<string>("");

	/* *********************************************************************************** */
	/* SHARED DATA BUFFER */
	const [dataBuffer, setDataBuffer] = useState<FormValues[]>([]);
	const [isSubmitted, setIsSubmitted] = useState(false); // Re-render once form is submitted
	const [fileInfo, setFileInfo] = useState<IFile[]>([]);
	const [loginOpen, setLoginOpen] = useState(!isLoggedIn);
	const [isFinalSubmitted, setIsFinalSubmitted] = useState(false);

	// Reserve the ID for the request
	useEffect(() => {
		(async () => {
			try {
				const json = await createNewID();
				console.log("New ID", json);
				setID(json.ID)
			} catch (e) {
				console.error("Error creating new ID", e);
				toast.error("Error creating new ID");
			}
		})();
	}, [createNewID]);

	/* *********************************************************************************** */
	// Reset the Submit Table after submission
	const resetTable = () => {
		setDataBuffer([]);
	};

	const onDelete = (ID: string) => {
		setDataBuffer((prevData) =>
			prevData.filter((item) => item.ID !== ID)
		);
	};

	const handleLoginSuccess = (ACCESS_GROUP: boolean, CUE_GROUP: boolean, IT_GROUP: boolean) => {
		// Handle login success
		setLoginOpen(false);
	};

	/* *********************************************************************************** */
	// Update the title and icon of app
	useEffect(() => {
		document.title =
			"Puchase Request - Bankruptcy Court Wester District of Louisiana";
	}, []);

	/* *********************************************************************************** */
	/* Determine if ApprovalTable requires a login or not */
	let element;
	if (isLoggedIn) {
		element = (
			<ApprovalPageMain
				onDelete={onDelete}
				resetTable={resetTable}
			/>
		);
	} else {
		element = (
			<LoginDialog
				open={loginOpen}
				onClose={() => setLoginOpen(false)}
				onLoginSuccess={handleLoginSuccess}
			/>
		);
	}

	return (
		<Box sx={{
			display: 'flex',
			flexDirection: 'column',
			height: '100vh',
			width: '100%'
		}}>
			<ToastContainer
				position="top-right"
				autoClose={1000}
				hideProgressBar={false}
				newestOnTop={false}
				closeOnClick
				rtl={false}
				pauseOnFocusLoss
				draggable
				pauseOnHover
				theme="dark"
			/>
			{/* Sidebar Navigation */}
			{/* Layout component has the sidebar/header/main content */}
			<Layout
				ACCESS_GROUP={ACCESS_GROUP}
				CUE_GROUP={CUE_GROUP}
				IT_GROUP={IT_GROUP}
			>
				<Routes>
					{/* Define Routes */}
					{/* Password protect the routes, only authorized users can visit Approvals table */}
					<Route path="/approvals" element={element} />;
					<Route
						path="/create-request"
						element={
							<>
								{/********************************************************************* */}
								{/* ADD ITEMS TO FORM - component */}
								{/********************************************************************* */}
								<AddItemsForm
									ID={ID}
									fileInfo={fileInfo}
									isFinalSubmitted={isFinalSubmitted}
									setDataBuffer={setDataBuffer}
									setIsSubmitted={setIsSubmitted}
									setID={setID}
									setFileInfo={setFileInfo}
									setIsFinalSubmitted={setIsFinalSubmitted}
								/>

								{/********************************************************************* */}
								{/* SUBMIT FORM TO APPROVAL TABLE - component */}
								{/********************************************************************* */}
								{/* isSubmitted and setIsSubmitted is what will determine to re-render the App or not, re-rendering is done
                    to get a new ID with each request */}
								<Box
									className="col-md-12"
									style={{ marginTop: "20px" }}
								>
									<SubmitApprovalTable
										ID={ID}
										setIsFinalSubmitted={setIsFinalSubmitted}
										dataBuffer={dataBuffer}
										onDelete={onDelete}
										fileInfo={fileInfo}
										isSubmitted={isSubmitted}
										setIsSubmitted={setIsSubmitted}
										setDataBuffer={setDataBuffer}
										setFileInfo={setFileInfo}
									/>
								</Box>
							</>
						}
					/>
				</Routes>
			</Layout>
		</Box>
	);
}

export default App;