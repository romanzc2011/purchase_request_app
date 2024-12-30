interface FundPickerProps {
    onSelectFund: (fund: string) => void;
    value: string;
}
const FundPicker = ({ value, onSelectFund }: FundPickerProps) => {
  return (
    <select value={value} className='form-select' onChange={(e) => onSelectFund(e.target.value)}>
        <option value={"092000"}>092000</option>
        <option value={"51140E"}>51140E</option>
        <option value={"51140X"}>51140X</option>
    </select>
  )
}

export default FundPicker