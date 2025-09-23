from dataclasses import dataclass
from typing import Dict

@dataclass
class BocMapping51140X:
    """BOC Mapping for 51140X fund code"""
    
    # 2000 Series
    boc_2120: str = "2120 - Temporary Duty Travel - Employees"
    boc_2125: str = "2125 - Training-Related Travel - Employees"
    boc_2331: str = "2331 - Local Telephone Services"
    boc_2332: str = "2332 - Commercial Long Distance Telecom Services"
    boc_2333: str = "2333 - Telephone and Data Communication Services"
    boc_2335: str = "2335 - Lease and Rental of Dedicated Communication Lines"
    boc_2337: str = "2337 - Wireless Communication Services"
    boc_2338: str = "2338 - Lease and Rental of Multifunctional Copiers and Printers"
    boc_2339: str = "2339 - IT Equipment Rental"
    boc_2504: str = "2504 - Stand-Alone Internet Access"
    boc_2512: str = "2512 - Maintenance and Installation of Telecommunication Equipment and Cabling"
    boc_2513: str = "2513 - Equipment Repair and Maintenance"
    boc_2514: str = "2514 - Infrastructure Equipment Repair and Maintenance"
    boc_2543: str = "2543 - Training Services and Enrollments"
    boc_2559: str = "2559 - Contractual Services Not Otherwise Classified"
    boc_2571: str = "2571 - Computer Hosting Services"
    boc_2603: str = "2603 - Training-Related Supplies"
    boc_2606: str = "2606 - IT Office Supplies"
    
    # 3000 Series
    boc_3102: str = "3102 - Large-Scale IT Equipment"
    boc_3103: str = "3103 - Small-Scale IT Equipment"
    boc_3104: str = "3104 - Telecommunications Equipment"
    boc_3105: str = "3105 - Data Communications Equipment"
    boc_3107: str = "3107 - Audio Recording Equipment"
    boc_3108: str = "3108 - Network or Stand-Alone Printers"
    boc_3109: str = "3109 - Multifunctional Equipment"
    boc_3110: str = "3110 - Network or Stand-Alone Scanners"
    boc_3112: str = "3112 - Commercial Off-the-Shelf (COTS) Software"
    boc_3141: str = "3141 - Audio Technology - Sound Systems"
    boc_3159: str = "3159 - Video Technology - Video Systems"
    
    def get_mapping_dict(self) -> Dict[str, str]:
        """Return the BOC mapping as a dictionary"""
        return {
            "2120": self.boc_2120,
            "2125": self.boc_2125,
            "2331": self.boc_2331,
            "2332": self.boc_2332,
            "2333": self.boc_2333,
            "2335": self.boc_2335,
            "2337": self.boc_2337,
            "2338": self.boc_2338,
            "2339": self.boc_2339,
            "2504": self.boc_2504,
            "2512": self.boc_2512,
            "2513": self.boc_2513,
            "2514": self.boc_2514,
            "2543": self.boc_2543,
            "2559": self.boc_2559,
            "2571": self.boc_2571,
            "2603": self.boc_2603,
            "2606": self.boc_2606,
            "3102": self.boc_3102,
            "3103": self.boc_3103,
            "3104": self.boc_3104,
            "3105": self.boc_3105,
            "3107": self.boc_3107,
            "3108": self.boc_3108,
            "3109": self.boc_3109,
            "3110": self.boc_3110,
            "3112": self.boc_3112,
            "3141": self.boc_3141,
            "3159": self.boc_3159
        }


@dataclass
class BocMapping51140E:
    """BOC Mapping for 51140E fund code"""
    
    # 2000 Series
    boc_2120: str = "2120 - Temporary Duty Travel - Employees"
    boc_2125: str = "2125 - Training-Related Travel - Employees"
    boc_2338: str = "2338 - Lease and Rental of Multifunctional Copiers and Printers"
    boc_2504: str = "2504 - Stand-Alone Internet Access"
    boc_2513: str = "2513 - Equipment Repair and Maintenance"
    boc_2514: str = "2514 - Maintenance of Infrastructure Equipment"
    boc_2543: str = "2543 - Training Services and Enrollments"
    boc_2559: str = "2559 - Contractual Services Not Otherwise Classified"
    boc_2603: str = "2603 - Training-Related Supplies"
    boc_2606: str = "2606 - IT Office Supplies"
    
    # 3000 Series
    boc_3102: str = "3102 - Large-Scale IT Equipment"
    boc_3103: str = "3103 - Small-Scale IT Equipment"
    boc_3105: str = "3105 - Data Communications Equipment"
    boc_3107: str = "3107 - Audio Recording Equipment"
    boc_3108: str = "3108 - Network or Stand-Alone Printers"
    boc_3109: str = "3109 - Multifunctional Equipment"
    boc_3110: str = "3110 - Network or Stand-Alone Scanners"
    boc_3111: str = "3111 - Furniture and Fixtures"
    boc_3112: str = "3112 - Commercial Off-the-Shelf (COTS) Software"
    
    def get_mapping_dict(self) -> Dict[str, str]:
        """Return the BOC mapping as a dictionary"""
        return {
            "2120": self.boc_2120,
            "2125": self.boc_2125,
            "2338": self.boc_2338,
            "2504": self.boc_2504,
            "2513": self.boc_2513,
            "2514": self.boc_2514,
            "2543": self.boc_2543,
            "2559": self.boc_2559,
            "2603": self.boc_2603,
            "2606": self.boc_2606,
            "3102": self.boc_3102,
            "3103": self.boc_3103,
            "3105": self.boc_3105,
            "3107": self.boc_3107,
            "3108": self.boc_3108,
            "3109": self.boc_3109,
            "3110": self.boc_3110,
            "3111": self.boc_3111,
            "3112": self.boc_3112
        }


@dataclass
class BocMapping092000:
    """BOC Mapping for 092000 fund code"""
    
    # 1000 Series
    boc_1100: str = "1100 - Personnel Compensation (Salaries)"
    boc_1157: str = "1157 - Cash Awards and Bonuses"
    boc_1158: str = "1158 - Reservist Differential"
    boc_1226: str = "1226 - Transit Subsidy"
    boc_1303: str = "1303 - Severance Pay"
    boc_1304: str = "1304 - Voluntary Separation Incentive Payments (Buyouts)"
    
    # 2000 Series
    boc_2120: str = "2120 - Temporary Duty Travel - Employees"
    boc_2125: str = "2125 - Training-Related Travel - Employees"
    boc_2203: str = "2203 - Moving and Relocation of Court Property"
    boc_2209: str = "2209 - Courier, Delivery and Miscellaneous Transportation of Things"
    boc_2320: str = "2320 - Non-GSA Space, Land, or Structure Rental"
    boc_2341: str = "2341 - Overtime Utilities"
    boc_2342: str = "2342 - Leased Parking"
    boc_2343: str = "2343 - Postage - Stamps, Metered and Online"
    boc_2345: str = "2345 - Postage Meter Rental and Lease"
    boc_2359: str = "2359 - Rental Services Not Otherwise Classified"
    boc_2380: str = "2380 - Emergency and Transitional Housing"
    boc_2403: str = "2403 - Printing - Forms, Stationery, Publications, and Other"
    boc_2502: str = "2502 - Contractual Services Related to Filling the Master Jury Wheel"
    boc_2503: str = "2503 - Computer Assisted Legal Research (CALR)"
    boc_2510: str = "2510 - Cyclical Facilities Maintenance"
    boc_2511: str = "2511 - Tenant Improvements - Circuit Rent Budget Program"
    boc_2513: str = "2513 - Equipment Repair and Maintenance"
    boc_2515: str = "2515 - Tenant Alterations"
    boc_2517: str = "2517 - Other Reimbursable Services from GSA"
    boc_2518: str = "2518 - Furniture Repair and Maintenance"
    boc_2521: str = "2521 - Court-Annexed Arbitration"
    boc_2526: str = "2526 - Post-Conviction Substance Abuse Treatment and Testing"
    boc_2527: str = "2527 - Pretrial Alternatives to Detention"
    boc_2529: str = "2529 - Expert or Consultant Services"
    boc_2530: str = "2530 - Post-Conviction Mental Health Treatment and Testing"
    boc_2531: str = "2531 - Contract Court Reporters"
    boc_2533: str = "2533 - Part-Time Magistrate Judges' Staff Expenses"
    boc_2534: str = "2534 - Part-time Magistrate Judges' Miscellaneous Office Expenses"
    boc_2535: str = "2535 - Temporary Help Services - Employment Agency"
    boc_2536: str = "2536 - Post-Conviction Location Monitoring"
    boc_2542: str = "2542 - Health Services"
    boc_2543: str = "2543 - Training Services and Enrollment"
    boc_2544: str = "2544 - Publication of Notices and Advertising"
    boc_2548: str = "2548 - Sex Offender Treatment and Monitoring"
    boc_2559: str = "2559 - Contractual Services Not Otherwise Classified"
    boc_2580: str = "2580 - Emergency and Transitional Support Services"
    boc_2601: str = "2601 - General Office Supplies"
    boc_2602: str = "2602 - Employee Recognition Supplies and Expenses"
    boc_2603: str = "2603 - Training-Related Supplies"
    boc_2610: str = "2610 - Uniform Items"
    
    # 3000 Series
    boc_3101: str = "3101 - General Office Equipment"
    boc_3107: str = "3107 - Audio Recording Equipment"
    boc_3111: str = "3111 - Furniture and Fixtures"
    boc_3113: str = "3113 - Mailing Equipment"
    boc_3121: str = "3121 - Legal Resources: New Print and Digital Purchases"
    boc_3122: str = "3122 - Legal Resources: Print and Digital Continuations"
    boc_3130: str = "3130 - Law Enforcement Equipment"
    
    def get_mapping_dict(self) -> Dict[str, str]:
        """Return the BOC mapping as a dictionary"""
        return {
            "1100": self.boc_1100,
            "1157": self.boc_1157,
            "1158": self.boc_1158,
            "1226": self.boc_1226,
            "1303": self.boc_1303,
            "1304": self.boc_1304,
            "2120": self.boc_2120,
            "2125": self.boc_2125,
            "2203": self.boc_2203,
            "2209": self.boc_2209,
            "2320": self.boc_2320,
            "2341": self.boc_2341,
            "2342": self.boc_2342,
            "2343": self.boc_2343,
            "2345": self.boc_2345,
            "2359": self.boc_2359,
            "2380": self.boc_2380,
            "2403": self.boc_2403,
            "2502": self.boc_2502,
            "2503": self.boc_2503,
            "2510": self.boc_2510,
            "2511": self.boc_2511,
            "2513": self.boc_2513,
            "2515": self.boc_2515,
            "2517": self.boc_2517,
            "2518": self.boc_2518,
            "2521": self.boc_2521,
            "2526": self.boc_2526,
            "2527": self.boc_2527,
            "2529": self.boc_2529,
            "2530": self.boc_2530,
            "2531": self.boc_2531,
            "2533": self.boc_2533,
            "2534": self.boc_2534,
            "2535": self.boc_2535,
            "2536": self.boc_2536,
            "2542": self.boc_2542,
            "2543": self.boc_2543,
            "2544": self.boc_2544,
            "2548": self.boc_2548,
            "2559": self.boc_2559,
            "2580": self.boc_2580,
            "2601": self.boc_2601,
            "2602": self.boc_2602,
            "2603": self.boc_2603,
            "2610": self.boc_2610,
            "3101": self.boc_3101,
            "3107": self.boc_3107,
            "3111": self.boc_3111,
            "3113": self.boc_3113,
            "3121": self.boc_3121,
            "3122": self.boc_3122,
            "3130": self.boc_3130
        }