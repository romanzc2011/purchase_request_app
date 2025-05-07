import { SxProps, Theme } from "@mui/material";

// Define style objects outside of the component
export const cellRowStyles: SxProps<Theme> = {
    "& .MuiDataGrid-cell": {
        color: "white",
        background: "#2c2c2c",
        fontSize: "0.95rem" // Increased font size for cells
    },
    "& .MuiDataGrid-row": {
        background: "#2c2c2c"
    },
    // Exclude Item Description column from font size increase
    "& .MuiDataGrid-cell[data-field='itemDescription']": {
        fontSize: "0.875rem !important" // Keep original font size for Item Description
    },
    // Shrink font size of requester column
    "& div[data-field='requester']": {
        fontSize: "0.85rem !important"
    }
};

export const headerStyles: SxProps<Theme> = {
    "& .MuiDataGrid-columnHeaders, .MuiDataGrid-columnHeader": {
        background: "linear-gradient(to top, #2c2c2c, #800000) !important",
        color: "white",
    },
    "& .MuiDataGrid-columnHeaderTitle": {
        fontWeight: "bold",
        fontSize: "1.1rem" // Increased font size for column headers
    },
};

export const footerStyles: SxProps<Theme> = {
    "& .MuiDataGrid-footerContainer": {
        backgroundColor: "#2c2c2c",
        borderTop: "1px solid rgba(255,255,255,0.2)",
    },
};

export const paginationStyles: SxProps<Theme> = {
    "& .MuiTablePagination-root": {
        color: "white",
        fontSize: "0.95rem" // Increased font size for pagination
    },
    "& .MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows": {
        color: "white",
        fontSize: "0.95rem" // Increased font size for pagination labels
    },
};