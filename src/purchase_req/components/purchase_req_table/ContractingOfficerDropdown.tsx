import { FormControl, InputLabel, Select, MenuItem, Typography, Box } from '@mui/material';
import { useState, useEffect } from 'react';
import { ContractingOfficer } from '../../types/approvalTypes';
import Buttons from './Buttons';
import { toast } from "react-toastify";

type Props = {
	value: number | "";
	onChange: (id: number | "") => void;
	onClickOK: (officerId: number, username: string) => void;
}

/* API URLs */
const API_URL_CONTRACTING_OFFICER = `${import.meta.env.VITE_API_URL}/api/get_contracting_officer`;

// ------------------------------------------------------------
// CONTRACTING OFFICER DROPDOWN COMPONENT
// ------------------------------------------------------------
function ContractingOfficerDropdown({ value, onChange, onClickOK }: Props) {
	const [officers, setContractingOfficers] = useState<ContractingOfficer[]>([]);
	const [selectedCO, setSelectedCO] = useState<number | "">("");

	// Fetch contracting officers from PRAS backend
	const fetchContractingOfficers = async () => {
		try {
			const response = await fetch(API_URL_CONTRACTING_OFFICER, {
				method: 'GET',
				headers: {
					"Authorization": `Bearer ${localStorage.getItem('access_token')}`
				}
			});
			if (!response.ok) {
				throw new Error('Failed to fetch contracting officers');
			}
			const data: ContractingOfficer[] = await response.json();
			setContractingOfficers(data);

			console.log(data);
		} catch (error) {
			console.error('Error fetching contracting officers:', error);
		}
	}

	// Fetch contracting officers from PRAS backend on component mount
	useEffect(() => {
		fetchContractingOfficers();
	}, []);

	return (
		<Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
			<Typography sx={{ color: 'white' }}>
				CONTRACTING OFFICER:
			</Typography>
			<FormControl sx={{ minWidth: 250 }} size="small">
				<InputLabel id="contracting-officer-select-label" sx={{ color: 'white' }}>Select Contracting Officer</InputLabel>
				<Select
					labelId="contracting-officer-select-label"
					id="contracting-officer-select"
					value={value}
					label="Select Option"
					onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
					sx={{ color: 'white' }}
					MenuProps={{
						PaperProps: {
							sx: {
								backgroundColor: '#2c2c2c',
								color: 'white'
							}
						}
					}}
				>
					<MenuItem value="" sx={{ color: 'white' }}>
						<em>None</em>
					</MenuItem>
					{officers.map((officer) => (
						<MenuItem key={officer.id} value={officer.id} sx={{ color: 'white' }}>
							{officer.username}
						</MenuItem>
					))}
				</Select>
			</FormControl>
			<Buttons
				className="btn btn-maroon assign-button"
				label={"OK"}
				onClick={() => {
					console.log("Current value:", value);
					console.log("Available officers:", officers);

					// Find the selected officer to get both ID and username
					const selectedOfficer = officers.find(officer => officer.id === value);
					console.log("Selected officer:", selectedOfficer);

					if (selectedOfficer && selectedOfficer.id !== undefined) {
						console.log("Calling onClickOK with:", selectedOfficer.id, selectedOfficer.username);
						onClickOK(selectedOfficer.id, selectedOfficer.username);
					} else {
						console.log("No officer selected or officer not found");
						toast.error("Please select a contracting officer");
					}
				}}
			/>
		</Box>

	)
}
export default ContractingOfficerDropdown;