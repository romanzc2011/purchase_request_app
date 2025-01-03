import React, { useState } from "react";
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemText,
  AppBar,
  Toolbar,
  Typography,
  CssBaseline,
  ListItemButton,
  ListItemIcon,
  IconButton,
} from "@mui/material";
import BKSeal from "../../../assets/seal_no_border.png";
import CheckCircleSharpIcon from '@mui/icons-material/CheckCircleSharp';
import MenuIcon from "@mui/icons-material/Menu";

const drawerWidth = 195;
const appBarHeight = 100;

export default function PurchaseSideBar() {
  const [open, setOpen] = useState(true); // State to toggle Drawer

  const toggleDrawer = () => {
    setOpen(!open); // Toggle open
  };

  return (
    <Box sx={{ display: "flex" }}>
      {/* HEADER */}
      <AppBar
        position="fixed"
        sx={{
          ml: `${drawerWidth}px`,
          background: "linear-gradient(to top, #2c2c2c, #800000)",
          boxShadow: "none",
        }}
      >
        <Toolbar>
          {/* TOGGLE BUTTON */}
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
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
                <h3 style={{ fontWeight: "bold", margin: 0 }}>
                  <div>UNITED STATES BANKRUPTCY COURT</div>
                  WESTERN DISTRICT OF LOUISIANA
                  <br />
                  <span style={{ fontSize: "1.2rem" }}>
                    PURCHASE REQUEST FORM
                  </span>
                </h3>
              </Box>
            </Box>
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Side Nav Bar */}
      <Drawer
        variant="permanent"
        open={open}
        sx={{
          width: open ? drawerWidth : 60,
          top: `${appBarHeight}px`,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: open ? drawerWidth : 60,
            boxSizing: "border-box",
            top: `${appBarHeight}px`,
            height: `calc(100% - ${appBarHeight})`,
            background: "linear-gradient(to bottom, #2c2c2c, #800000)", // Gradient background
            color: "white", // Text color for contrast
            transition: "width 0.3s ease",
          },
        }}
      >
        <Toolbar />
        <Box>
          <List>
            {/* LIST BUTTON DIVIDER **************************************************************** */}
            <ListItem divider sx={{ borderBottom: "2px solid #800000" }}>
              <ListItemButton
                sx={{ justifyContent: open ? "flex-start" : "center" }} // Center icon when collapsed
              >
                <ListItemIcon
                  sx={{
                    color: "green",
                    minWidth: open ? "40px" : "0",
                    justifyContent: open ? "flex-start" : "center",
                  }}
                >
                  <CheckCircleSharpIcon />
                </ListItemIcon>
                {/* Show text only when open */}
                {open && <ListItemText primary="REQUESTS" />}
              </ListItemButton>
            </ListItem>
            {/* LIST BUTTON DIVIDER **************************************************************** */}
          </List>
        </Box>
      </Drawer>
    </Box>
  );
}
