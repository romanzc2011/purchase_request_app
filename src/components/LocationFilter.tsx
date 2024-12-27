import React from 'react'

interface LocationProps {
    onSelectLocation: (location: string) => void;
}
const LocationFilter = ({ onSelectLocation }: LocationProps) => {
  return (
    <select className='form-select' onChange={(e) => onSelectLocation(e.target.value)}>
        <option id={'ALEX/C'} value={"ALEX/C"}>ALEX/C</option>
        <option id={'ALEX/J'} value={"ALEX/J"}>ALEX/J</option>
        <option id={'LAFY/C'} value={"LAFY/C"}>LAFY/C</option>
        <option id={'LAFY/J'} value={"LAFY/J"}>LAFY/J</option>
        <option id={'LKCH/C'} value={"LKCH/C"}>LKCH/C</option>
        <option id={'LKCC/J'} value={"LKCC/J"}>LKCC/J</option>
        <option id={'MONR/C'} value={"MONR/C"}>MONR/C</option>
        <option id={'MONR/J'} value={"MONR/J"}>MONR/J</option>
        <option id={'SHVT/C'} value={"SHVT/C"}>SHVT/C</option>
        <option id={'SHVT/J'} value={"SHVT/J"}>SHVT/J</option>
    </select>
  )
}

export default LocationFilter