import React, { useState } from 'react';
import { Box } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';

interface LayoutProps {
    children: React.ReactNode;
    CUE_GROUP: boolean;
    IT_GROUP: boolean;
}

const Layout: React.FC<LayoutProps> = ({
    children,
    CUE_GROUP,
    IT_GROUP
}) => {
    const [isSidebarOpen] = useState(true);

    const drawerWidth = 195;
    const collapseWidth = 60;
    const appBarHeight = 90;

    return (
        <Box sx={{ display: 'flex', position: 'relative', zIndex: 1200 }}>
            <Header />

            <Sidebar
                isOpen={isSidebarOpen}
                CUE_GROUP={CUE_GROUP}
                IT_GROUP={IT_GROUP}
            />

            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    width: `calc(100% - ${isSidebarOpen ? drawerWidth : collapseWidth}px)`,
                    marginLeft: `${isSidebarOpen ? drawerWidth : collapseWidth}px`,
                    marginTop: `${appBarHeight}px`,
                    transition: 'margin 0.3s ease',
                    position: 'relative',
                    zIndex: 1,
                    height: `calc(100vh - ${appBarHeight}px)`,
                    display: 'flex',
                    flexDirection: 'column',
                    pl: 10
                }}
            >
                {children}
            </Box>
        </Box>
    );
};

export default Layout; 