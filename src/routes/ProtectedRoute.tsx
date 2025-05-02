import { Navigate } from "react-router-dom";

interface ProtectedRouteProps {
  isLoggedIn: boolean;
  children: JSX.Element;
}

function ProtectedRoute({ isLoggedIn, children}: ProtectedRouteProps) {
  if(!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export default ProtectedRoute;