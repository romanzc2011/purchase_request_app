import React from 'react'

interface FundPickerProps {
    onSelectFund: (fund: string) => void;
}
const FundPicker = ({ onSelectFund }: FundPickerProps) => {
  return (
    <select className='form-select' onChange={(e) => onSelectFund(e.target.value)}>
        <option value={"092000"}>092000</option>
        <option value={"51140E"}>51140E</option>
        <option value={"51140X"}>51140X</option>
    </select>
  )
}

export default FundPicker