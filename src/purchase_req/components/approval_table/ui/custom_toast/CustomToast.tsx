import { toast } from "react-toastify";

const CloseButton = ({ closeToast }: { closeToast?: () => void }) => (
    <button
        onClick={closeToast}
        style={{
            marginLeft: "12px",
            padding: "4px 10px",
            border: "none",
            borderRadius: "6px",
            backgroundColor: "red",
            color: "white",
            fontWeight: "bold",
            cursor: "pointer",
        }}
    >
        OK
    </button>
);

export function RQ1WarningToast(message: string, customId: string) {
    toast.error(message, {
        closeButton: <CloseButton />,
        toastId: customId,
        ariaLabel: "ERROR",
        position: "top-center",
        style: {
            width: "500px"
        },
        autoClose: 10000
    });
}
