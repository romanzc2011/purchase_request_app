/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";
import { useState } from "react";
import { useDebounce } from 'use-debounce';
import { Box, IconButton, debounce } from "@mui/material";
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import Input from '@mui/material/Input';
import SearchIcon from "@mui/icons-material/Search";

/************************************************************************************ */
/* CONFIG API URL- */
/************************************************************************************ */
const baseURL = import.meta.env.VITE_API_URL;
const API_CALL: string = "/api/getSearchData";
const API_URL = `${baseURL}${API_CALL}`;

const DEBOUNCE_MS = 300;

/* FETCHING APPROVAL DATA FUNCTION for useQuery */
const fetchSearchData = async (query: string) => {
    const URL = `${API_URL}?query=${encodeURIComponent(query)}`
    const response = await fetch(URL, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    if(!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    return response.json();
}

/* SEARCH BAR */
function SearchBar() {
    const [query, setQuery] = useState('');
    const [debouncedQuery] = useDebounce(query, DEBOUNCE_MS);
    const queryResult = useQuery({
        queryKey: ['search-str', debouncedQuery],
        queryFn: async () => {
            if (!debouncedQuery) return [];
            return fetchSearchData(debouncedQuery);
        },
        staleTime: DEBOUNCE_MS,
        placeholderData: keepPreviousData,
    });

    return (
        <Box display="flex" justifyContent="space-between" p={2}>
            {/* SEARCH BAR */}
            <Box sx={{ display: 'flex', backgroundColor: '#363B3F', borderRadius: '3px' }}>
                <Input
                    sx={{ ml: 2, 
                        color: "white", 
                        flex: 1 }} 
                        placeholder="Search"
                        onChange={(e) => {
                            const newValue = e.target.value;
                            setQuery(newValue);
                        }} />
                <IconButton type="button" sx={{ p: 1 }}>
                    <SearchIcon sx={{ color: "white" }} />
                </IconButton>
            </Box>
        </Box>
    );
};

export default SearchBar;