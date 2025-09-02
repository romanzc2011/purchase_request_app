import { Box } from "@mui/material";
import { useState } from "react";
import { Sidebar as ProSidebar, Menu, MenuItem } from "react-pro-sidebar";
import MenuIcon from "@mui/icons-material/Menu";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import { useNavigate } from "react-router-dom";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ApprovalIcon from "@mui/icons-material/Approval";

interface SidebarProps {
    isOpen: boolean;
    toggleSidebar: () => void;
    CUE_GROUP: boolean;
    IT_GROUP: boolean;
}

const Sidebar = ({ isOpen, CUE_GROUP, IT_GROUP }: Omit<SidebarProps, 'toggleSidebar' | 'ACCESS_GROUP'>) => {
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
                },
                position: "fixed",
                top: "90px",
                left: 0,
                zIndex: 1200,
                height: "calc(100vh - 90px)",
                width: isOpen ? "195px" : "60px",
                transition: "width 0.3s ease"
            }}
        >
            <ProSidebar
                collapsed={isCollapsed}
                toggled={toggled}
                onBackdropClick={() => setToggled(false)}
                breakPoint="md"
                backgroundColor="linear-gradient(to top, #2c2c2c, #800000)"
                rootStyles={{
                    background: "linear-gradient(to bottom, #2c2c2c, #800000)",
                    height: '100%',
                    position: 'fixed',
                    overflow: 'hidden'
                }}
            >
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <Menu
                        menuItemStyles={{
                            button: {
                                backgroundColor: "linear-gradient(to bottom, #2c2c2c, #800000)",
                                '&:hover': {
                                    backgroundColor: '#800000'
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
                                    <MenuIcon />
                                    <IconButton onClick={() => setIsCollapsed(!isCollapsed)} />

                                </Box>
                            )}
                        </MenuItem>


                        <Box paddingLeft={isCollapsed ? undefined : "10%"}>
                            {/*************************************************************************/}
                            {/* CREATE REQUEST */}
                            {/*************************************************************************/}
                            <MenuItem

                                icon={<AddCircleOutlineIcon />}
                                onClick={() => navigate('/create-request')}
                            >
                                <Typography>CREATE REQUEST</Typography>
                            </MenuItem>

                            {/*************************************************************************/}
                            {/* APPROVALS */}
                            {/*************************************************************************/}
                            <MenuItem
                                disabled={IT_GROUP || CUE_GROUP}
                                icon={<ApprovalIcon />}
                                onClick={() => navigate('/approvals')}
                            >
                                <Typography>APPROVALS</Typography>
                            </MenuItem>
                        </Box>
                    </Menu>
                </div>
            </ProSidebar>
        </Box>
    )
}

export default Sidebar; 