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
import { useTheme } from "@mui/material/styles";
import BKSeal from "../../assets/seal_no_border.png";
import CheckCircleSharpIcon from "@mui/icons-material/CheckCircleSharp";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import { Link } from "react-router-dom";
import MenuIcon from "@mui/icons-material/Menu";

interface PurchaseSideBarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
  ACCESS_GROUP: boolean;
  CUE_GROUP: boolean;
  IT_GROUP: boolean;
}

const drawerWidth = 195;
const appBarHeight = 90;
const collapseWidth = 60;

const PurchaseSideBar: React.FC<PurchaseSideBarProps> = ({
  isOpen,
  toggleSidebar,
  CUE_GROUP,
  IT_GROUP,
}) => {
const theme = useTheme();

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
                    PRAS - PURCHASE REQUEST APPROVAL SYSTEM
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
          zIndex: theme.zIndex.drawer + 1,
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
            {/************************************************************************/}
            {/* PURCHASES */}
            {/************************************************************************/}
            <ListItem divider sx={{ borderBottom: "2px solid #800000" }}>
              <ListItemButton
                component={Link}
                to="/purchase-request"
                sx={{
                  justifyContent: isOpen ? "flex-start" : "center",
                  width: "100%",
                }}
                aria-label="Purchase Requests"
              >
                <ListItemIcon
                  sx={{
                    color: "white",
                    minWidth: isOpen ? "35px" : "0",
                    justifyContent: isOpen ? "flex-start" : "center",
                  }}
                >
                  <Inventory2Icon />
                </ListItemIcon>
                {isOpen && (
                  <ListItemText
                    primary="CREATE REQUEST"
                    slotProps={{
                      primary: {
                        sx: {
                          fontSize: ".9rem",
                          whiteSpace: "nowrap", // Prevents text wrapping
                        },
                      },
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>

            {/************************************************************************/}
            {/* APPROVALS */}
            {/************************************************************************/}
            <ListItem divider sx={{ borderBottom: "2px solid #800000" }}>
              <ListItemButton
                component={Link}
                to="/approvals-table"
                disabled={ !IT_GROUP || !CUE_GROUP }  // Disable if the user is not part of IT or CUE group
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