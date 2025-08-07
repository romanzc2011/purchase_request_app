
// Function to get BOC options for dropdown with headers
export const getBOCOptions = (fund: string) => {
    if (fund === "51140X") {
        return Object.entries(BOC_MAPPING_51140X).map(([key, value]) => ({
            value: key,
            label: value,
            disabled: value.includes('===') // Make headers non-selectable
        }));
    } else if (fund === "51140E") {
        return Object.entries(BOC_MAPPING_51140E).map(([key, value]) => ({
            value: key,
            label: value,
            disabled: value.includes('===') // Make headers non-selectable
        }));
    } else if (fund === "092000") {
        return Object.entries(BOC_MAPPING_092000).map(([key, value]) => ({
            value: key,
            label: value,
            disabled: value.includes('===') // Make headers non-selectable    
        }));
    }
}

// ******************************************************
// 51140X BOC Mapping
// ******************************************************
const BOC_MAPPING_51140X: Record<string, string> = {
    // 2000 Series
    "2000": "=== 2000 Series ===",
    "2120": "2120 - Temporary Duty Travel - Employees",
    "2125": "2125 - Training-Related Travel - Employees",
    "2331": "2331 - Local Telephone Services",
    "2332": "2332 - Commercial Long Distance Telecom Services",
    "2333": "2333 - Telephone and Data Communication Services",
    "2335": "2335 - Lease and Rental of Dedicated Communication Lines",
    "2337": "2337 - Wireless Communication Services",
    "2338": "2338 - Lease and Rental of Multifunctional Copiers and Printers",
    "2339": "2339 - IT Equipment Rental",
    "2504": "2504 - Stand-Alone Internet Access",
    "2512": "2512 - Maintenance and Installation of Telecommunication Equipment and Cabling",
    "2513": "2513 - Equipment Repair and Maintenance",
    "2514": "2514 - Infrastructure Equipment Repair and Maintenance",
    "2543": "2543 - Training Services and Enrollments",
    "2559": "2559 - Contractual Services Not Otherwise Classified",
    "2571": "2571 - Computer Hosting Services",
    "2603": "2603 - Training-Related Supplies",
    "2606": "2606 - IT Office Supplies",
    // 3000 Series
    "3000": "=== 3000 Series ===",
    "3102": "3102 - Large-Scale IT Equipment",
    "3103": "3103 - Small-Scale IT Equipment",
    "3104": "3104 - Telecommunications Equipment",
    "3105": "3105 - Data Communications Equipment",
    "3107": "3107 - Audio Recording Equipment",
    "3108": "3108 - Network or Stand-Alone Printers",
    "3109": "3109 - Multifunctional Equipment",
    "3110": "3110 - Network or Stand-Alone Scanners",
    "3112": "3112 - Commercial Off-the-Shelf (COTS) Software",
    "3141": "3141 - Audio Technology - Sound Systems",
    "3159": "3159 - Video Technology - Video Systems"
};

// ******************************************************
// 51140E BOC Mapping
// ******************************************************
const BOC_MAPPING_51140E: Record<string, string> = {
    // 2000 Series
    "2000": "=== 2000 Series ===",
    "2120": "2120 - Temporary Duty Travel - Employees",
    "2125": "2125 - Training-Related Travel - Employees",
    "2338": "2338 - Lease and Rental of Multifunctional Copiers and Printers",
    "2504": "2504 - Stand-Alone Internet Access",
    "2513": "2513 - Equipment Repair and Maintenance",
    "2514": "2514 - Maintenance of Infrastructure Equipment",
    "2543": "2543 - Training Services and Enrollments",
    "2559": "2559 - Contractual Services Not Otherwise Classified",
    "2603": "2603 - Training-Related Supplies",
    "2606": "2606 - IT Office Supplies",
    // 3000 Series
    "3000": "=== 3000 Series ===",
    "3102": "3102 - Large-Scale IT Equipment",
    "3103": "3103 - Small-Scale IT Equipment",
    "3105": "3105 - Data Communications Equipment",
    "3107": "3107 - Audio Recording Equipment",
    "3108": "3108 - Network or Stand-Alone Printers",
    "3109": "3109 - Multifunctional Equipment",
    "3110": "3110 - Network or Stand-Alone Scanners",
    "3111": "3111 - Furniture and Fixtures",
    "3112": "3112 - Commercial Off-the-Shelf (COTS) Software"
};

// ******************************************************
// 092000 BOC Mapping
// ******************************************************
const BOC_MAPPING_092000: Record<string, string> = {
    // 1000 Series
    "1000": "=== 1000 Series ===",
    "1100": "1100 - Personnel Compensation (Salaries)",
    "1157": "1157 - Cash Awards and Bonuses",
    "1158": "1158 - Reservist Differential",
    "1226": "1226 - Transit Subsidy",
    "1303": "1303 - Severance Pay",
    "1304": "1304 - Voluntary Separation Incentive Payments (Buyouts)",

    // 2000 Series
    "2000": "=== 2000 Series ===",
    "2120": "2120 - Temporary Duty Travel - Employees",
    "2125": "2125 - Training-Related Travel - Employees",
    "2203": "2203 - Moving and Relocation of Court Property",
    "2209": "2209 - Courier, Delivery and Miscellaneous Transportation of Things",
    "2320": "2320 - Non-GSA Space, Land, or Structure Rental",
    "2341": "2341 - Overtime Utilities",
    "2342": "2342 - Leased Parking",
    "2343": "2343 - Postage - Stamps, Metered and Online",
    "2345": "2345 - Postage Meter Rental and Lease",
    "2359": "2359 - Rental Services Not Otherwise Classified",
    "2380": "2380 - Emergency and Transitional Housing",
    "2403": "2403 - Printing - Forms, Stationery, Publications, and Other",
    "2502": "2502 - Contractual Services Related to Filling the Master Jury Wheel",
    "2503": "2503 - Computer Assisted Legal Research (CALR)",
    "2510": "2510 - Cyclical Facilities Maintenance",
    "2511": "2511 - Tenant Improvements - Circuit Rent Budget Program",
    "2513": "2513 - Equipment Repair and Maintenance",
    "2515": "2515 - Tenant Alterations",
    "2517": "2517 - Other Reimbursable Services from GSA",
    "2518": "2518 - Furniture Repair and Maintenance",
    "2521": "2521 - Court-Annexed Arbitration",
    "2526": "2526 - Post-Conviction Substance Abuse Treatment and Testing",
    "2527": "2527 - Pretrial Alternatives to Detention",
    "2529": "2529 - Expert or Consultant Services",
    "2530": "2530 - Post-Conviction Mental Health Treatment and Testing",
    "2531": "2531 - Contract Court Reporters",
    "2533": "2533 - Part-Time Magistrate Judges' Staff Expenses",
    "2534": "2534 - Part-time Magistrate Judges' Miscellaneous Office Expenses",
    "2535": "2535 - Temporary Help Services - Employment Agency",
    "2536": "2536 - Post-Conviction Location Monitoring",
    "2542": "2542 - Health Services",
    "2543": "2543 - Training Services and Enrollment",
    "2544": "2544 - Publication of Notices and Advertising",
    "2548": "2548 - Sex Offender Treatment and Monitoring",
    "2559": "2559 - Contractual Services Not Otherwise Classified",
    "2580": "2580 - Emergency and Transitional Support Services",
    "2601": "2601 - General Office Supplies",
    "2602": "2602 - Employee Recognition Supplies and Expenses",
    "2603": "2603 - Training-Related Supplies",
    "2610": "2610 - Uniform Items",

    // 3000 Series
    "3000": "=== 3000 Series ===",
    "3101": "3101 - General Office Equipment",
    "3107": "3107 - Audio Recording Equipment",
    "3111": "3111 - Furniture and Fixtures",
    "3113": "3113 - Mailing Equipment",
    "3121": "3121 - Legal Resources: New Print and Digital Purchases",
    "3122": "3122 - Legal Resources: Print and Digital Continuations",
    "3130": "3130 - Law Enforcement Equipment"
};