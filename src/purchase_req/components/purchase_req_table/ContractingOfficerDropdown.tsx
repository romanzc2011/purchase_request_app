import { FormControl, InputLabel, Select, MenuItem, Typography, Box } from '@mui/material';
import { useState, useEffect } from 'react';
import { ContractingOfficer } from '../../types/approvalTypes';
import Buttons from './Buttons';
import { toast } from "react-toastify";
import { computeAPIURL } from "../../utils/misc_utils";

type Props = {
    value: number | "";
    requestID?: string;
    onChange: (id: number | "") => void;
    onClickOK: (requestId: string, officerId: number, username: string) => void;
}

// ------------------------------------------------------------
// CONTRACTING OFFICER DROPDOWN COMPONENT
// ------------------------------------------------------------
function ContractingOfficerDropdown({ value, requestID, onChange, onClickOK }: Props) {
    const [officers, setContractingOfficers] = useState<ContractingOfficer[]>([]);

    // Fetch contracting officers from PRAS backend
    const fetchContractingOfficers = async () => {
        try {
            const response = await fetch(computeAPIURL("/api/get_contracting_officer"), {
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
                    sx={{
                        color: 'white',
                        '& .MuiOutlinedInput-root .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'white',
                            borderWidth: '2px',
                        },
                        '& .MuiOutlinedInput-root:hover .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'white',
                            borderWidth: '2px',
                        },
                        '& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'white',
                            borderWidth: '2px',
                        },
                        '& .MuiSvgIcon-root': {
                            color: 'white',
                        },
                    }}
                    MenuProps={{
                        PaperProps: {
                            sx: {
                                backgroundColor: '#2c2c2c',
                                color: 'white',
                                '& .MuiMenuItem-root': {
                                    color: 'white',
                                    '&:hover': {
                                        backgroundColor: '#404040',
                                    },
                                },
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
                        console.log("Calling onClickOK with:", requestID, selectedOfficer.id, selectedOfficer.username);
                        onClickOK(requestID || "", selectedOfficer.id, selectedOfficer.username);
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