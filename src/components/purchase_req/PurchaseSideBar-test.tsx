import { Box } from "@mui/material";
import { useState } from "react";
import { Sidebar, Menu, MenuItem, SubMenu } from "react-pro-sidebar";
import BKSeal from "../../assets/seal_no_border.png";
import HomeIcon from "@mui/icons-material/Home";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import { useNavigate } from "react-router-dom";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ApprovalIcon from "@mui/icons-material/Approval";

interface PurchaseSideBarProps {
    isOpen: boolean;
    toggleSidebar: () => void;
    ACCESS_GROUP: boolean;
    CUE_GROUP: boolean;
    IT_GROUP: boolean;
}

const PurchaseSideBar = ({ isOpen, toggleSidebar, ACCESS_GROUP, CUE_GROUP, IT_GROUP }: PurchaseSideBarProps) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [toggled, setToggled] = useState(false);
    const navigate = useNavigate();
    
    return (
        <Box
            sx={{
                "& .pro-sidebar-inner": {
                    background: "linear-gradient(to top, #2c2c2c, #800000) !important",
                },
                "& .pro-icon-wrapper": {
                    backgroundColor: "transparent !important",
                },
                "& .pro-inner-item": {
                    padding: "5px 35px 5px 20px !important",
                    color: "white !important", // set desired text color
                },
                "& .pro-sub-menu-content": {
                    background: "linear-gradient(to top, #2c2c2c, #800000) !important",
                }
            }}
        >
            <Box style={{ display: 'flex', height: '100vh' }}>
                <Sidebar
                    collapsed={isCollapsed}
                    toggled={toggled}
                    onBackdropClick={() => setToggled(false)}
                    breakPoint="md"
                    backgroundColor="#800000"
                    rootStyles={{
                        background: "linear-gradient(to bottom, #2c2c2c, #800000)"
                    }}
                >
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <Menu
                            menuItemStyles={{
                                button: {
                                    backgroundColor: "linear-gradient(to bottom, #2c2c2c, #800000)",
                                    '&:hover': {
                                        backgroundColor: '#ffd700'
                                    }
                                },
                                SubMenuExpandIcon: {
                                    color: "white",
                                }
                            }}
                        >
                            <MenuItem
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                icon={isCollapsed ? <MenuOutlinedIcon /> : undefined}
                            >
                                {!isCollapsed && (
                                    <Box
                                        display="flex"
                                        justifyContent="space-between"
                                        alignItems="center"
                                        ml="15px"
                                    >
                                        <Typography variant="h6">
                                            Purchase Request System
                                        </Typography>
                                        <IconButton onClick={() => setIsCollapsed(!isCollapsed)}>
                                            <MenuOutlinedIcon />
                                        </IconButton>
                                    </Box>
                                )}
                            </MenuItem>

                            {!isCollapsed && (
                                <Box mb="25px">
                                    <Box display="flex" justifyContent="center" alignItems="center">
                                        <img
                                            src={BKSeal}
                                            style={{ width: "100px", height: "100px" }}
                                        />
                                    </Box>
                                </Box>
                            )}

                            <Box paddingLeft={isCollapsed ? undefined : "10%"}>
                                {/*************************************************************************/}
                                {/* DASHBOARD */}
                                {/*************************************************************************/}
                                <MenuItem
                                    style={{
                                        color: "white"
                                    }}
                                    icon={<HomeIcon />}
                                    onClick={() => navigate('/')}
                                >
                                    <Typography>Dashboard</Typography>
                                </MenuItem>

                                {/*************************************************************************/}
                                {/* CREATE REQUEST */}
                                {/*************************************************************************/}
                                <MenuItem
                                    style={{
                                        color: "white",
                                        backgroundColor: "#800000",
                                        margin: "10px 0",
                                        borderRadius: "4px",
                                        fontWeight: "bold"
                                    }}
                                    icon={<AddCircleOutlineIcon />}
                                    onClick={() => navigate('/create-request')}
                                >
                                    <Typography>CREATE REQUEST</Typography>
                                </MenuItem>

                                {/*************************************************************************/}
                                {/* APPROVALS */}
                                {/*************************************************************************/}
                                <MenuItem
                                    disabled={!IT_GROUP || !CUE_GROUP}
                                    style={{
                                        color: "white",
                                        backgroundColor: "#800000",
                                        margin: "10px 0",
                                        borderRadius: "4px",
                                        fontWeight: "bold"
                                    }}
                                    icon={<ApprovalIcon />}
                                    onClick={() => navigate('/approvals')}
                                >
                                    <Typography>APPROVALS</Typography>
                                </MenuItem>
                            </Box>
                        </Menu>
                    </div>
                </Sidebar>
            </Box>
        </Box>
    )
}

export default PurchaseSideBar;
