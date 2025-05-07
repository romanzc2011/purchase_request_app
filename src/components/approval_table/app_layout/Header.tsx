import React from "react";
import {
    AppBar,
    Toolbar,
    Typography,
    Box,
} from "@mui/material";
import BKSeal from "../../../assets/seal_no_border.png";

interface HeaderProps {
    isSidebarOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ isSidebarOpen }) => {
    const drawerWidth = 195;
    const collapseWidth = 60;

    return (
        <AppBar
            position="fixed"
            sx={{
                ml: isSidebarOpen ? `${drawerWidth}px` : `${collapseWidth}px`,
                background: "linear-gradient(to top, #2c2c2c, #800000)",
                transition: "margin 0.3s ease",
                boxShadow: "none",
                width: "100%",
                zIndex: 1300
            }}
        >
            <Toolbar>
                <Typography variant="h6" noWrap>
                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            background: "linear-gradient(to top, #2c2c2c, #800000)",
                        }}
                    >
                        <img
                            src={BKSeal}
                            style={{ marginRight: "20px", height: "95px" }}
                            alt="Seal"
                        />
                        <Box>
                            <h3
                                style={{ fontWeight: "bold", margin: 0, textAlign: "center" }}
                            >
                                <div>UNITED STATES BANKRUPTCY COURT</div>
                                WESTERN DISTRICT OF LOUISIANA
                                <br />
                                <Box
                                    sx={{
                                        display: "flex",
                                        justifyContent: "center",
                                        fontSize: "1.2rem",
                                    }}
                                >
                                    PRAS - PURCHASE REQUEST APPROVAL SYSTEM
                                </Box>
                            </h3>
                        </Box>
                    </Box>
                </Typography>
            </Toolbar>
        </AppBar>
    );
};

export default Header;
