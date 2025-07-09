import React from "react";
import { Controller, useFormContext } from "react-hook-form";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { useUsernames } from "../../purchase_req_table/useUsernames";
interface RequesterAutocompleteProps {
	name: string;
	label: string;
	freeSolo?: boolean;
	rules?: Record<string, any>;
}

export default function RequesterAutocomplete({
	name,
	label,
	freeSolo = false,
	rules = { required: `${label} is required` }
}: RequesterAutocompleteProps) {
	const { control, formState: { errors } } = useFormContext();
	const [inputValue, setInputValue] = React.useState("");
	const { data: options = [], isLoading, error } = useUsernames(inputValue);

	return (
		<Controller
			control={control}
			name={name}
			rules={rules}
			render={({ field }) => (
				<Autocomplete
					{...field}
					freeSolo={freeSolo}
					options={options}
					onInputChange={(_, newInputValue) => {
						setInputValue(newInputValue);
					}}
					onChange={(_, value) => field.onChange(value)}
					renderInput={(params) => (
						<TextField
							{...params}
							className="form-control"
							variant="outlined"
							size="small"
							error={!!errors[name] || !!error}
							helperText={error?.message || errors[name]?.message as string}
							fullWidth
							sx={{
								backgroundColor: 'white',
								'& .MuiOutlinedInput-root': {
									backgroundColor: 'white'
								}
							}}
							InputProps={{
								...params.InputProps,
								endAdornment: (
									<>
										{isLoading ? "Loading..." : null}
										{params.InputProps.endAdornment}
									</>
								),
							}}
						/>
					)}
				/>
			)}
		/>
	);
}