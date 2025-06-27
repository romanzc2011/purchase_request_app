import { FormControl, InputLabel, Select, MenuItem, Typography, Box } from '@mui/material';
import { useState, useEffect } from 'react';
import { ContractingOfficer } from '../../../types/approvalTypes';
import Buttons from '../../purchase_req_table/Buttons';

type Props = {
	value: string;
	onChange: (username: string) => void;
	onClickOK: () => void;
}

/* API URLs */
const API_URL_CONTRACTING_OFFICER = `${import.meta.env.VITE_API_URL}/api/get_contracting_officer`;

// ------------------------------------------------------------
// CONTRACTING OFFICER DROPDOWN COMPONENT
// ------------------------------------------------------------
function ContractingOfficerDropdown({ value, onChange, onClickOK }: Props) {
	const [officers, setContractingOfficers] = useState<ContractingOfficer[]>([]);

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
					onChange={(e) => onChange(e.target.value)}
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
						<MenuItem key={officer.id} value={officer.username} sx={{ color: 'white' }}>
							{officer.username}
						</MenuItem>
					))}
				</Select>
			</FormControl>
			<Buttons
				className="btn btn-maroon assign-button"
				label={"OK"}
				onClick={() => {
					onClickOK();
				}}
			/>
		</Box>

	)
}
export default ContractingOfficerDropdown;