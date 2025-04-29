import React, { useState } from 'react';
import { Box } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
  ACCESS_GROUP: boolean;
  CUE_GROUP: boolean;
  IT_GROUP: boolean;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, 
  ACCESS_GROUP, 
  CUE_GROUP, 
  IT_GROUP 
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };
  
  const drawerWidth = 195;
  const collapseWidth = 60;
  const appBarHeight = 90;
  
  return (
    <Box sx={{ display: 'flex', position: 'relative', zIndex: 1200 }}>
      <Header isSidebarOpen={isSidebarOpen} />
      
      <Sidebar 
        isOpen={isSidebarOpen}
        toggleSidebar={toggleSidebar}
        ACCESS_GROUP={ACCESS_GROUP}
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