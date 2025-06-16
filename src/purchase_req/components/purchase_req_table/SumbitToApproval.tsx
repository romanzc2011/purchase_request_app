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
	Box,
	IconButton,
	Collapse,
	Typography,
} from "@mui/material";
import { FormValues } from "../../types/formTypes";
import { convertBOC } from "../../utils/bocUtils";
import { IFile } from "../../types/IFile";
import React, { useEffect, useState } from "react";
import { v4 as uuidv4 } from 'uuid';
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { toast } from "react-toastify";
import { ItemStatus } from "../../types/approvalTypes";

const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/send_to_purchase_req";
const API_URL = `${baseURL}${API_CALL}`;

/************************************************************************************ */
/* INTERFACE PROPS */
/************************************************************************************ */
interface SubmitApprovalTableProps {
	dataBuffer: FormValues[];
	onDelete: (id: string) => void;
	id?: string;
	fileInfo: IFile[];
	isSubmitted: boolean;
	setIsSubmitted: React.Dispatch<React.SetStateAction<boolean>>;
	setID?: React.Dispatch<React.SetStateAction<string>>;
	setDataBuffer: React.Dispatch<React.SetStateAction<FormValues[]>>;
	setFileInfo: React.Dispatch<React.SetStateAction<IFile[]>>;
}

function SubmitApprovalTable({
	dataBuffer,
	onDelete,
	id,
	fileInfo,
	isSubmitted,
	setIsSubmitted,
	setDataBuffer,
	setFileInfo,
	setID
}: SubmitApprovalTableProps) {

	// State for expanded rows
	const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

	// Toggle row expansion
	const toggleRowExpanded = (id: string) =>
		setExpandedRows((prev) => ({
			...prev,
			[id]: !prev[id],
		}));

	/* Check if table has been submitted */
	useEffect(() => {
		if (isSubmitted) {
			setDataBuffer([]);

			console.log("In the if isSubmitted: dataBuffer==", dataBuffer);
			setIsSubmitted(false);
		}
	}, [isSubmitted, setDataBuffer, setIsSubmitted]);


	/************************************************************************************ */
	/* CALCULATE PRICE -- helper function to convert price/quantity to number and do
		 calculations */
	/************************************************************************************ */
	function calculatePrice(item: FormValues): number {
		const price = Number(item.price_each) || 0;
		const quantity = Number(item.quantity) || 1;
		return price * quantity;
	}

	// Preprocess data to calculate price
	const processedData = dataBuffer.map((item) => ({
		...item,
		price_each: Number(item.price_each),
		calculatedPrice: calculatePrice(item)
	}));

	/* Check if data buffer is multiple items */
	const item_count = dataBuffer.length;
	console.log("item_count==", item_count);

	// Group items by request_id
	const groupedItems = processedData.reduce<Record<string, FormValues[]>>((acc, item) => {
		const itemRequestId = item.request_id || 'default';
		(acc[itemRequestId] = acc[itemRequestId] || []).push(item);
		return acc;
	}, {});
	console.log("processedData==", processedData);
	/************************************************************************************ */
	/* SUBMIT DATA --- send to backend to add to database */
	/************************************************************************************ */
	const handleSubmitData = async (processedData: FormValues[]) => {
		try {
			// Get a proper ID from the backend
			const idRequest = await fetch(`${baseURL}/api/create_new_id`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${localStorage.getItem("access_token")}`,
				},
			});

			if (!idRequest.ok) {
				toast.error("Failed to get ID");
				throw new Error(`Failed to get ID: ${idRequest.status}`);
			}

			const idData = await idRequest.json();
			const requestId = idData.id;

			// Get the requester from the first item
			const requester = processedData[0]?.requester;
			if (!requester) {
				throw new Error("Requester is required");
			}

			// Process each item in the data buffer
			const processedItems = processedData.map(item => ({
				request_id: requestId,
				uuid: item.uuid || uuidv4(),
				irq1_id: item.irq1_id || null,
				requester: item.requester,
				phoneext: String(item.phoneext),
				datereq: item.datereq instanceof Date
					? item.datereq.toISOString().split('T')[0]
					: item.datereq || null,
				dateneed: item.dateneed instanceof Date
					? item.dateneed.toISOString().split('T')[0]
					: item.dateneed || null,
				order_type: item.order_type || "STANDARD",
				item_description: item.item_description,
				justification: item.justification,
				train_not_aval: Boolean(item.train_not_aval),
				needs_not_meet: Boolean(item.needs_not_meet),
				quantity: Number(item.quantity),
				price_each: Number(item.price_each),
				total_price: Number(item.total_price) || (Number(item.price_each) * Number(item.quantity)),
				fund: item.fund,
				location: item.location,
				budget_obj_code: String(item.budget_obj_code).padStart(4, '0'),
				status: ItemStatus.NEW_REQUEST,
				file_attachments: fileInfo.map(file => ({
					name: file.name,
					file: file.file,
					type: file.file?.type || '',
					size: file.file?.size || 0
				}))
			}));

			// Create a single object with the requester and items
			const requestData = {
				requester: requester,
				items: processedItems,
				item_count: item_count
			};

			const formData = new FormData();
			formData.append("payload_json", JSON.stringify(requestData));

			// Attach files from fileInfo
			fileInfo.forEach(file => {
				if (file.file && file.status === "ready") {
					formData.append("files", file.file);
					console.log("Attaching file to formData:", file.name);
				}
			});

			// Send the data to the backend
			const response = await fetch(API_URL, {
				method: "POST",
				headers: {
					Authorization: `Bearer ${localStorage.getItem("access_token")}`,
				},
				body: formData,
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			console.log("dataBuffer, isArray==", Array.isArray(dataBuffer), " length==", dataBuffer.length)

			const result = await response.json();
			console.log("Submission result:", result);

			// Reset the form and data buffer
			setIsSubmitted(true);
			setDataBuffer([]);

			// Update the ID if setID is provided
			if (setID) {
				setID(requestId);
			}

			toast.success("Data submitted successfully");
		} catch (error) {
			console.error("Error submitting data:", error);
			toast.error("Failed to submit data");
		}
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
					sx={{
						background:
							"linear-gradient(to bottom, #2c2c2c, #800000)",
					}}
				>
					<TableRow>
						<TableCell sx={{ width: 40 }} /> {/* expand/collapse */}
						<TableCell sx={{ color: "white", fontWeight: "bold" }}>
							ID
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
							Line Total
						</TableCell>
						<TableCell sx={{ color: "white", fontWeight: "bold" }}>
							Actions
						</TableCell>
					</TableRow>
				</TableHead>
				<TableBody>
					{Object.entries(groupedItems).map(([request_id, items]) => (
						<React.Fragment key={request_id}>
							{/* Main row with expand/collapse button */}
							<TableRow>
								<TableCell>
									{items.length > 1 && (
										<IconButton
											size="small"
											onClick={() => toggleRowExpanded(request_id)}
											sx={{ color: "white" }}
										>
											{expandedRows[request_id] ? (
												<KeyboardArrowUpIcon />
											) : (
												<KeyboardArrowDownIcon />
											)}
										</IconButton>
									)}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{items[0].request_id}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{convertBOC(items[0].budget_obj_code)}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{items[0].fund}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{items[0].location}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{items[0].quantity}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{typeof items[0].price_each === "number"
										? items[0].price_each.toFixed(2)
										: "0.00"}
								</TableCell>
								<TableCell sx={{ color: "white" }}>
									{calculatePrice(items[0]).toFixed(2)}
								</TableCell>
								<TableCell>
									<Button
										variant="contained"
										color="error"
										onClick={() => {
											onDelete(items[0].request_id || 'default');
										}}
									>
										Delete
									</Button>
								</TableCell>
							</TableRow>

							{/* Collapsible rows for additional items */}
							{items.length > 1 && (
								<TableRow>
									<TableCell
										colSpan={9}
										sx={{ p: 0, background: "#3c3c3c" }}
									>
										<Collapse
											in={expandedRows[request_id]}
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
																"Budget Object Code",
																"Fund",
																"Location",
																"Quantity",
																"Price Each",
																"Line Total",
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
																	{item.request_id}
																</TableCell>
																<TableCell sx={{ color: "white" }}>
																	{convertBOC(item.budget_obj_code)}
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
																	{typeof item.price_each === "number"
																		? item.price_each.toFixed(2)
																		: "0.00"}
																</TableCell>
																<TableCell sx={{ color: "white" }}>
																	{calculatePrice(item).toFixed(2)}
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

				{/* FOOTER WITH FILE UPLOAD & SUBMIT BUTTON */}
				<tfoot>
					<TableRow>
						<TableCell colSpan={9}>
							{/* Display current files */}
							{fileInfo.length > 0 && (
								<Box sx={{ mb: 2 }}>
									<Typography variant="subtitle2" sx={{ color: "white" }}>
										Attached Files:
									</Typography>
									<ul style={{ color: "white", listStyle: "none", padding: 0 }}>
										{fileInfo.map((file, index) => (
											<li key={index}>
												{file.name} - {file.status}
											</li>
										))}
									</ul>
								</Box>
							)}

							{/************************************************************************************ */}
							{/* BUTTONS: SUBMIT/PRINT */}
							{/************************************************************************************ */}
							{/* Submit data to proper destination, email to supervisor or notify sup that there's a request for them to approve */}
							<Buttons
								label="Submit Form"
								className=" me-3 btn btn-maroon"
								disabled={dataBuffer.length === 0}
								onClick={() => {
									handleSubmitData(processedData);
									setIsSubmitted(true);
									setFileInfo([]);
								}}
							/>

							{/* This button will print out item Request */}
							<Buttons
								label="Print Form"
								className="btn btn-maroon"
							/>
						</TableCell>

						<TableCell
							colSpan={2}
							sx={{ color: "white", textAlign: "right" }}
						></TableCell>
						<TableCell
							colSpan={3}
							sx={{
								color: "white",
								fontWeight: "bold",
								textAlign: "right",
							}}
						>
							Total: $
							{processedData
								.reduce(
									(acc, item) =>
										acc +
										(Number(item.calculatedPrice) || 0),
									0
								)
								.toFixed(2)}
						</TableCell>
					</TableRow>
				</tfoot>
			</Table>
		</TableContainer>
	);
}

export default SubmitApprovalTable;