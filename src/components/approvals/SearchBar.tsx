/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useEffect } from "react";
import { useState } from "react";
import { useDebounce } from 'use-debounce';
import { Box, IconButton, debounce } from "@mui/material";
import { useQuery, keepPreviousData, useQueryClient, QueryClient } from '@tanstack/react-query';
import Input from '@mui/material/Input';
import SearchIcon from "@mui/icons-material/Search";
import { FormValues } from "../../types/formTypes";

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
const fetchSearchData = async (query: string, queryColumn?: string) => {
    let url = `${API_URL}?query=${encodeURIComponent(query)}`;
    if(queryColumn) {
        url += `&queryColumn=${encodeURIComponent(queryColumn)}`;
    }

    const response = await fetch(url, {
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
/* Using debouncing, which waits so many ms to get continuous data */
function SearchBar({ setSearchQuery }: SearchBarProps) {
    const [query, setQuery] = useState('');
    const [debouncedQuery] = useDebounce(query, DEBOUNCE_MS);

    useEffect(() => {
        setSearchQuery(debouncedQuery);
    }, [debouncedQuery, setSearchQuery]);

    const queryResult = useQuery({
        queryKey: ['search-str', debouncedQuery],
        queryFn: async () => {
            if (!debouncedQuery) return [];

            // Heuristic to determine the queryColumn based on the search term
            // const searchTerm: string = debouncedQuery.trim();
            let queryColumn: string | undefined;

            // // Searching for fund and boc
            // if(/^\d+$/.test(searchTerm)) {
            //     // Test the first character to determine if it's BOC or Fund
            //     const firstChar: string = searchTerm[0];
            //     if(firstChar === '5' || firstChar === '0') {
            //         queryColumn = "fund";
            //     } else if(firstChar === '3') {
            //         queryColumn = "budgetObjCode";
            //     }
            // }
            console.log("QUERY_RESULT: ", queryResult.data);
            setSearchQuery(debouncedQuery);

            return fetchSearchData(debouncedQuery, queryColumn);
        },
        staleTime: DEBOUNCE_MS,
        placeholderData: keepPreviousData,
    });

    return (
        <Box display="flex" justifyContent="space-between" p={2}>
            {/* SEARCH BAR */}
            <Box sx={{ display: 'flex', width: '25%', backgroundColor: '#363B3F', borderRadius: '3px' }}>
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