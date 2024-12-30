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
  CssBaseline,
  ListItemButton,
  ListItemIcon,
} from "@mui/material";
import BKSeal from "../assets/seal_no_border.png";
import VerifiedIcon from "@mui/icons-material/Verified";

const drawerWidth = 240;
const appBarHeight = 101;

export default function PurchaseSideBar() {
  return (
    <Box sx={{ display: "flex" }}>
      {/* HEADER */}
      <AppBar
        position="fixed"
        sx={{
          ml: `${drawerWidth}px`,
          background: "linear-gradient(to top, #2c2c2c, #800000)",
        }}
      >
        <Toolbar>
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
        sx={{
          width: drawerWidth,
          top: `${appBarHeight}px`,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: drawerWidth,
            boxSizing: "border-box",
            top: `${appBarHeight}px`,
            height: `calc(100% - ${appBarHeight})`,
            background: "linear-gradient(to bottom, #2c2c2c, #800000)", // Gradient background
            color: "white", // Text color for contrast
          },
        }}
      >
        <Toolbar />
        <Box>
          <List>
            {/* LIST BUTTON DIVIDER **************************************************************** */}
            <ListItem divider sx={{ borderBottom: "2px solid #800000" }}>
              <ListItemButton>
                <ListItemIcon sx={{ color: "white" }}>
                  <VerifiedIcon />
                </ListItemIcon>
                <ListItemText primary="REQUESTS" />
              </ListItemButton>
            </ListItem>
            {/* LIST BUTTON DIVIDER **************************************************************** */}
          </List>
        </Box>
      </Drawer>
    </Box>
  );
}
