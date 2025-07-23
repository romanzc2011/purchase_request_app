import { SxProps, Theme } from "@mui/material";

// Define style objects outside of the component
export const cellRowStyles: SxProps<Theme> = {
	"& .MuiDataGrid-cell": {
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		color: "white !important",
		fontSize: "0.95rem !important"
	},
	'& .MuiDataGrid-cellCheckbox': {
		minWidth: 48,
		display: 'flex',
		alignItems: 'center',
	},
	"& .MuiDataGrid-row": {
		backgroundColor: "#2c2c2c"
	},
	"& .MuiDataGrid-row:hover": {
		backgroundColor: "#444 !important",
	},
	"& .MuiDataGrid-row.Mui-selected": {
		backgroundColor: "#014519 !important",
		color: "#fff",
	},
	"& .MuiDataGrid-row.Mui-selected:hover": {
		backgroundColor: "#014519 !important",
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

// Header for Groups in Approval Table
export const groupHeaderStyles: SxProps<Theme> = {
	"& .MuiDataGrid-columnHeader": {
		backgroundColor: "#3c3c3c !important",
		fontWeight: "bold",
		fontSize: "1.05rem !important", // Increased font size for column headers
		borderBottom: "2px solid #800000"
	},
	// Style for group header rows in the DataGrid body
	"& .group-header-row .MuiDataGrid-cell": {
		backgroundColor: "#3c3c3c !important",
		fontWeight: "bold",
		fontSize: "1.05rem !important",
		borderBottom: "2px solid #800000",
		color: "#fff",
		letterSpacing: "0.05px",
		paddingRight: 2,
	}
};

// Table-specific header styles (for regular MUI Table components)
export const tableHeaderStyles: SxProps<Theme> = {
	background: "linear-gradient(to top, #2c2c2c, #800000) !important",
	color: "white",
	"& .MuiTableCell-root": {
		fontWeight: "bold",
		fontSize: "1.1rem",
		paddingRight: 2,
		color: "white",
		position: "relative",
		border: "none",
		"&::after": {
			content: '""',
			position: "absolute",
			top: "15px",
			right: 0,
			paddingTop: "15px",
			width: "1px",
			height: "50%",
			backgroundColor: "#FFFFFF",
		}
	},
	"& .MuiTableCell-root:last-child::after": {
		display: "none"
	}
};