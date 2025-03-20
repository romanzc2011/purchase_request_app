import React from "react";
import { TextField, Typography, Box, IconButton } from "@mui/material";
import { useQuery } from '@tanstack/react-query';
import InputBase from '@mui/material/InputBase';
import SearchIcon from "@mui/icons-material/Search";

function SearchBar() {
    return (
        <Box display="flex" justifyContent="space-between" p={2}>
            {/* SEARCH BAR */}
            <Box sx={{ display: 'flex', backgroundColor: '#212528', borderRadius: '3px' }}>
                <InputBase sx={{ ml: 2, color: "white", flex: 1 }} placeholder="Search" />
                <IconButton type="button" sx={{ p: 1 }}>
                    <SearchIcon sx={{ color: "white" }} />
                </IconButton>
            </Box>
        </Box>
    );
};

export default SearchBar;