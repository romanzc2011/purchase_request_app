import { toast, Id } from "react-toastify";

const showProgressToast = (message: string, progress: number): Id => {
	return toast.loading(
		<div>
			<div>{message}</div>
			<div style={{ width: '100%', backgroundColor: '#ddd', borderRadius: '4px', marginTop: '8px' }}>
				<div
					style={{
						width: `${progress}%`,
						height: '4px',
						backgroundColor: '#4caf50',
						borderRadius: '4px',
						transition: 'width 0.3s ease'
					}}
				/>
			</div>
		</div>,
		{
			position: "top-center",
			autoClose: false
		}
	);
};

export default showProgressToast; 