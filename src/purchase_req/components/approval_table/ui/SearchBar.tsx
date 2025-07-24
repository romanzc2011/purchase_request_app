/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useEffect, useCallback } from "react";
import { useState } from "react";
import { useDebounce } from 'use-debounce';
import { Box, IconButton, debounce } from "@mui/material";
import { useQuery, keepPreviousData, useQueryClient, QueryClient } from '@tanstack/react-query';
import Input from '@mui/material/Input';
import SearchIcon from "@mui/icons-material/Search";
import { FormValues } from "../../../types/formTypes";

interface SearchBarProps {
	setSearchQuery: (query: string) => void;
}

// @todo: 
// Add functionality where the search bar appends a '-' after 4 chars
/************************************************************************************ */
/* CONFIG API URL- */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/getSearchData";
const API_URL = `${baseURL}${API_CALL}`;
const DEBOUNCE_MS = 100;

/* FETCHING APPROVAL DATA FUNCTION for useQuery */
export async function fetchSearchData(query: string) {
	const url = `${API_URL}/search?query=${encodeURIComponent(query)}`;
	const response = await fetch(url, {
		headers: {
			'Authorization': `Bearer ${localStorage.getItem('access_token')}`
		}
	});
	if (!response.ok) {
		throw new Error('Response was not ok');
	}

	const data = await response.json();
	console.log("Search DATA:", data)
	return data;
}

/* SEARCH BAR */
/* Using debouncing, which waits so many ms to get continuous data */
const SearchBar = React.memo(({ setSearchQuery }: SearchBarProps) => {
	const [query, setQuery] = useState('');
	const [debouncedQuery] = useDebounce(query, DEBOUNCE_MS);

	useEffect(() => {
		setSearchQuery(debouncedQuery);
	}, [debouncedQuery, setSearchQuery]);

	useQuery({
		queryKey: ['search-str', debouncedQuery],
		queryFn: async () => {
			if (!debouncedQuery) return [];
			setSearchQuery(debouncedQuery);
			return fetchSearchData(debouncedQuery);
		},
		staleTime: DEBOUNCE_MS,
		placeholderData: keepPreviousData,
	});

	// Optimize onChange handler
	const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
		const newValue = e.target.value;
		setQuery(newValue);
	}, []);

	return (
		<Box display="flex" justifyContent="space-between" p={2}>
			{/* SEARCH BAR */}
			<Box sx={{ display: 'flex', width: '25%', backgroundColor: '#363B3F', borderRadius: '3px' }}>
				<Input
					sx={{
						ml: 2,
						color: "white",
						flex: 1
					}}
					placeholder="Search"
					onChange={handleInputChange} />
				<IconButton type="button" sx={{ p: 1 }}>
					<SearchIcon sx={{ color: "white" }} />
				</IconButton>
			</Box>
		</Box>
	);
});

SearchBar.displayName = 'SearchBar';

export default SearchBar;