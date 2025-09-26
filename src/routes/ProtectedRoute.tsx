import { Navigate } from "react-router-dom";
import { useUser } from "../purchase_req/hooks/useUser";
import { useEffect, useRef } from "react";
import { RQ1WarningToast } from "../purchase_req/components/approval_table/ui/custom_toast/CustomToast";

interface ProtectedRouteProps {
    isLoggedIn: boolean;
    children: JSX.Element;
}

function ProtectedRoute({ isLoggedIn, children }: ProtectedRouteProps) {
    const user = useUser();
    const hasShownError = useRef(false);

    console.log("GROUP: ", user?.groups);
    console.log("ACCESS_GROUP check:", user?.groups.includes("ACCESS_GROUP"));
    console.log("IT_GROUP check:", user?.groups.includes("IT_GROUP"));
    console.log("CUE_GROUP check:", user?.groups.includes("CUE_GROUP"));
    console.log("Group logic test: ", !(user?.groups.includes("ACCESS_GROUP") || user?.groups.includes("IT_GROUP") || user?.groups.includes("CUE_GROUP")));

    // Check if user has approval table access
    const hasAccess = user?.groups.includes("ACCESS_GROUP") || user?.groups.includes("IT_GROUP") || user?.groups.includes("CUE_GROUP");

    // Show error message only once when access is denied
    useEffect(() => {
        if (!hasAccess && !hasShownError.current && user?.username) {
            console.log("NO APPROVAL ACCESS for: ", user?.username)
            const username = user?.username || "User";
            RQ1WarningToast(`${username}, you don't have permission to access the Approvals table. Redirecting to Create Request...`, "approval-access-denied");
            hasShownError.current = true;
        }
    }, [hasAccess, user?.username]);

    if (!isLoggedIn) {
        return <Navigate to="/login" replace />;
    }

    if (!hasAccess) {
        return <Navigate to="/purchase_request" replace />;
    }

    console.log("APPROVAL ACCESS GRANTED for: ", user?.username)
    return children;
};

export default ProtectedRoute;