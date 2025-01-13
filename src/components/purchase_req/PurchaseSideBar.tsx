import React from "react";
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemText,
  AppBar,
  Toolbar,
  Typography,
  ListItemButton,
  ListItemIcon,
  IconButton,
} from "@mui/material";
import BKSeal from "../../assets/seal_no_border.png";
import CheckCircleSharpIcon from "@mui/icons-material/CheckCircleSharp";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import { Link } from "react-router-dom";
import MenuIcon from "@mui/icons-material/Menu";

interface PurchaseSideBarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
}

/**************************************************************************/
/* Request data from approval table */
const fetchRequestData = () => {
  fetch("http://127.0.0.1:5000/getApprovalData", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP error: ${res.status}`);
      }
      return res.json(); // Parse  JSON response
    })
    .then((data) => {
      console.log("GET RESPONSE: ", data);
    })
    .catch((err) => console.error("Error catching data: ", err));
};

const drawerWidth = 195;
const appBarHeight = 90;
const collapseWidth = 60;

const PurchaseSideBar: React.FC<PurchaseSideBarProps> = ({
  isOpen,
  toggleSidebar,
}) => {
  return (
    <Box sx={{ display: "flex" }}>
      {/* HEADER */}
      <AppBar
        position="fixed"
        sx={{
          ml: isOpen ? `${drawerWidth}px` : `${collapseWidth}px`,
          background: "linear-gradient(to top, #2c2c2c, #800000)",
          transition: "margin 0.3s ease",
          boxShadow: "none",
        }}
      >
        <Toolbar>
          {/* TOGGLE BUTTON */}
          <IconButton
            edge="start"
            color="inherit"
            aria-label="toggle sidebar"
            onClick={toggleSidebar}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
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
                    PURCHASE REQUEST
                  </Box>
                </h3>
              </Box>
            </Box>
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Side Nav Bar */}
      <Drawer
        variant="permanent"
        sx={{
          width: isOpen ? drawerWidth : collapseWidth,
          position: "fixed", // Fix the Drawer to the left side
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: isOpen ? drawerWidth : collapseWidth,
            boxSizing: "border-box",
            height: `calc(100vh - ${appBarHeight}px)`,
            marginTop: `${appBarHeight}px`, // Proper alignment below the header
            background: "linear-gradient(to bottom, #2c2c2c, #800000)", // Gradient background
            color: "white", // Text color for contrast
            transition: "width 0.3s ease",
          },
        }}
      >
        <Toolbar />
        <Box>
          <List>
            {/* PURCHASE REQUESTS */}
            <ListItem divider sx={{ borderBottom: "2px solid #800000" }}>
              <ListItemButton
                component={Link}
                to="/purchase-request"
                sx={{
                  justifyContent: isOpen ? "flex-start" : "center",
                }}
                aria-label="Purchase Requests"
              >
                <ListItemIcon
                  sx={{
                    color: "white",
                    minWidth: isOpen ? "40px" : "0",
                    justifyContent: isOpen ? "flex-start" : "center",
                  }}
                >
                  <Inventory2Icon />
                </ListItemIcon>
                {isOpen && <ListItemText primary="PURCHASES" />}
              </ListItemButton>
            </ListItem>
            {/* REQUESTS */}
            <ListItem divider sx={{ borderBottom: "2px solid #800000" }}>
              <ListItemButton
                onClick={() => {
                  fetchRequestData();
                }}
                component={Link}
                to="/approvals-table"
                sx={{ justifyContent: isOpen ? "flex-start" : "center" }}
                aria-label="Approvals Table"
              >
                <ListItemIcon
                  sx={{
                    color: "white",
                    minWidth: isOpen ? "40px" : "0",
                    justifyContent: isOpen ? "flex-start" : "center",
                  }}
                >
                  <CheckCircleSharpIcon />
                </ListItemIcon>
                {isOpen && <ListItemText primary="APPROVALS" />}
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>
    </Box>
  );
};

export default PurchaseSideBar;
