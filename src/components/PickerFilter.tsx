import React from 'react'

interface PickerFileterProps {
    onSelectCategory: (category: string) => void;
}
const PickerFileter = ({ onSelectCategory }: PickerFileterProps) => {
  return (
    <select className='form-select' onChange={(e) => onSelectCategory(e.target.value)}>
        <option id={'generalOfficeEq'} value={"generalOfficeEq"}>3101 - General Office Equipment</option>
        <option id={'audioRecording'} value={"audioRecordingEq"}>3107 - Audio Recording Equipment</option>
        <option id={'furnitureFix'} value={"furnitureFix"}>3111 - Furniture and Fixtures</option>
        <option id={'mailingEq'} value={"mailingEq"}>3113 - Mailing Equipment</option>
        <option id={'newPrintDigi'}  value={"newPrintDigi"}>3121 - Legal Resources - New Print and Digital Purchases</option>
        <option id={'printDigiCont'} value={"printDigiCont"}>3122 - Legal Resources - Print and Digital Continuations</option>
        <option id={'lawEnforceEq'} value={"lawEnforceEq"}>3130 - Law Enforcement Equipment</option>
    </select>
  )
}

export default PickerFileter