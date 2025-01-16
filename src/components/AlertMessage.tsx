import { SxProps, Theme } from '@mui/material';
import Alert, { AlertColor } from '@mui/material/Alert';
import Stack from '@mui/material/Stack';

type AlertMessageProps = {
  alertText: string;
  severity: AlertColor;
  sx?: SxProps<Theme>
};

const AlertMessage = ({ alertText, severity, sx }: AlertMessageProps): JSX.Element => {
  return (
    <Stack sx={sx} spacing={2}>
      <Alert severity={severity}>{alertText}</Alert>
    </Stack>
  );
};

export default AlertMessage;
