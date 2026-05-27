"""ISO-2 to ISO-3 mapping for WID country codes.

WID stores ``country`` as ISO-3166-1 alpha-2. The release uses ISO-3166-1
alpha-3 in ``geo_id`` because alpha-3 is the dominant standard in
inequality / macro panel datasets (IMF, World Bank, Penn World Tables).

We embed a static table to avoid a runtime dependency on pycountry and
to keep the build deterministic offline. WID also uses a handful of
non-standard codes (regional aggregates such as ``WO`` for the world,
``XA`` for Africa) -- those are mapped to project-internal codes
prefixed with ``WID-`` so they can be filtered out of the country-level
release.
"""

from __future__ import annotations

# ISO 3166-1 alpha-2 -> (alpha-3, English name)
# This table covers all sovereign states + commonly-used dependencies
# that appear in WID.
ISO2_TO_ISO3: dict[str, tuple[str, str]] = {
    "AD": ("AND", "Andorra"), "AE": ("ARE", "United Arab Emirates"),
    "AF": ("AFG", "Afghanistan"), "AG": ("ATG", "Antigua and Barbuda"),
    "AI": ("AIA", "Anguilla"), "AL": ("ALB", "Albania"),
    "AM": ("ARM", "Armenia"), "AO": ("AGO", "Angola"),
    "AQ": ("ATA", "Antarctica"), "AR": ("ARG", "Argentina"),
    "AS": ("ASM", "American Samoa"), "AT": ("AUT", "Austria"),
    "AU": ("AUS", "Australia"), "AW": ("ABW", "Aruba"),
    "AX": ("ALA", "Aland Islands"), "AZ": ("AZE", "Azerbaijan"),
    "BA": ("BIH", "Bosnia and Herzegovina"), "BB": ("BRB", "Barbados"),
    "BD": ("BGD", "Bangladesh"), "BE": ("BEL", "Belgium"),
    "BF": ("BFA", "Burkina Faso"), "BG": ("BGR", "Bulgaria"),
    "BH": ("BHR", "Bahrain"), "BI": ("BDI", "Burundi"),
    "BJ": ("BEN", "Benin"), "BL": ("BLM", "Saint Barthelemy"),
    "BM": ("BMU", "Bermuda"), "BN": ("BRN", "Brunei Darussalam"),
    "BO": ("BOL", "Bolivia"), "BQ": ("BES", "Bonaire, Sint Eustatius and Saba"),
    "BR": ("BRA", "Brazil"), "BS": ("BHS", "Bahamas"),
    "BT": ("BTN", "Bhutan"), "BV": ("BVT", "Bouvet Island"),
    "BW": ("BWA", "Botswana"), "BY": ("BLR", "Belarus"),
    "BZ": ("BLZ", "Belize"), "CA": ("CAN", "Canada"),
    "CC": ("CCK", "Cocos Islands"), "CD": ("COD", "Congo, Democratic Republic"),
    "CF": ("CAF", "Central African Republic"), "CG": ("COG", "Congo"),
    "CH": ("CHE", "Switzerland"), "CI": ("CIV", "Cote d'Ivoire"),
    "CK": ("COK", "Cook Islands"), "CL": ("CHL", "Chile"),
    "CM": ("CMR", "Cameroon"), "CN": ("CHN", "China"),
    "CO": ("COL", "Colombia"), "CR": ("CRI", "Costa Rica"),
    "CU": ("CUB", "Cuba"), "CV": ("CPV", "Cabo Verde"),
    "CW": ("CUW", "Curacao"), "CX": ("CXR", "Christmas Island"),
    "CY": ("CYP", "Cyprus"), "CZ": ("CZE", "Czechia"),
    "DE": ("DEU", "Germany"), "DJ": ("DJI", "Djibouti"),
    "DK": ("DNK", "Denmark"), "DM": ("DMA", "Dominica"),
    "DO": ("DOM", "Dominican Republic"), "DZ": ("DZA", "Algeria"),
    "EC": ("ECU", "Ecuador"), "EE": ("EST", "Estonia"),
    "EG": ("EGY", "Egypt"), "EH": ("ESH", "Western Sahara"),
    "ER": ("ERI", "Eritrea"), "ES": ("ESP", "Spain"),
    "ET": ("ETH", "Ethiopia"), "FI": ("FIN", "Finland"),
    "FJ": ("FJI", "Fiji"), "FK": ("FLK", "Falkland Islands"),
    "FM": ("FSM", "Micronesia"), "FO": ("FRO", "Faroe Islands"),
    "FR": ("FRA", "France"), "GA": ("GAB", "Gabon"),
    "GB": ("GBR", "United Kingdom"), "GD": ("GRD", "Grenada"),
    "GE": ("GEO", "Georgia"), "GF": ("GUF", "French Guiana"),
    "GG": ("GGY", "Guernsey"), "GH": ("GHA", "Ghana"),
    "GI": ("GIB", "Gibraltar"), "GL": ("GRL", "Greenland"),
    "GM": ("GMB", "Gambia"), "GN": ("GIN", "Guinea"),
    "GP": ("GLP", "Guadeloupe"), "GQ": ("GNQ", "Equatorial Guinea"),
    "GR": ("GRC", "Greece"), "GT": ("GTM", "Guatemala"),
    "GU": ("GUM", "Guam"), "GW": ("GNB", "Guinea-Bissau"),
    "GY": ("GUY", "Guyana"), "HK": ("HKG", "Hong Kong"),
    "HN": ("HND", "Honduras"), "HR": ("HRV", "Croatia"),
    "HT": ("HTI", "Haiti"), "HU": ("HUN", "Hungary"),
    "ID": ("IDN", "Indonesia"), "IE": ("IRL", "Ireland"),
    "IL": ("ISR", "Israel"), "IM": ("IMN", "Isle of Man"),
    "IN": ("IND", "India"), "IO": ("IOT", "British Indian Ocean Territory"),
    "IQ": ("IRQ", "Iraq"), "IR": ("IRN", "Iran"),
    "IS": ("ISL", "Iceland"), "IT": ("ITA", "Italy"),
    "JE": ("JEY", "Jersey"), "JM": ("JAM", "Jamaica"),
    "JO": ("JOR", "Jordan"), "JP": ("JPN", "Japan"),
    "KE": ("KEN", "Kenya"), "KG": ("KGZ", "Kyrgyzstan"),
    "KH": ("KHM", "Cambodia"), "KI": ("KIR", "Kiribati"),
    "KM": ("COM", "Comoros"), "KN": ("KNA", "Saint Kitts and Nevis"),
    "KP": ("PRK", "Korea (DPRK)"), "KR": ("KOR", "Korea"),
    "KW": ("KWT", "Kuwait"), "KY": ("CYM", "Cayman Islands"),
    "KZ": ("KAZ", "Kazakhstan"), "LA": ("LAO", "Lao PDR"),
    "LB": ("LBN", "Lebanon"), "LC": ("LCA", "Saint Lucia"),
    "LI": ("LIE", "Liechtenstein"), "LK": ("LKA", "Sri Lanka"),
    "LR": ("LBR", "Liberia"), "LS": ("LSO", "Lesotho"),
    "LT": ("LTU", "Lithuania"), "LU": ("LUX", "Luxembourg"),
    "LV": ("LVA", "Latvia"), "LY": ("LBY", "Libya"),
    "MA": ("MAR", "Morocco"), "MC": ("MCO", "Monaco"),
    "MD": ("MDA", "Moldova"), "ME": ("MNE", "Montenegro"),
    "MF": ("MAF", "Saint Martin (French)"), "MG": ("MDG", "Madagascar"),
    "MH": ("MHL", "Marshall Islands"), "MK": ("MKD", "North Macedonia"),
    "ML": ("MLI", "Mali"), "MM": ("MMR", "Myanmar"),
    "MN": ("MNG", "Mongolia"), "MO": ("MAC", "Macao"),
    "MP": ("MNP", "Northern Mariana Islands"), "MQ": ("MTQ", "Martinique"),
    "MR": ("MRT", "Mauritania"), "MS": ("MSR", "Montserrat"),
    "MT": ("MLT", "Malta"), "MU": ("MUS", "Mauritius"),
    "MV": ("MDV", "Maldives"), "MW": ("MWI", "Malawi"),
    "MX": ("MEX", "Mexico"), "MY": ("MYS", "Malaysia"),
    "MZ": ("MOZ", "Mozambique"), "NA": ("NAM", "Namibia"),
    "NC": ("NCL", "New Caledonia"), "NE": ("NER", "Niger"),
    "NF": ("NFK", "Norfolk Island"), "NG": ("NGA", "Nigeria"),
    "NI": ("NIC", "Nicaragua"), "NL": ("NLD", "Netherlands"),
    "NO": ("NOR", "Norway"), "NP": ("NPL", "Nepal"),
    "NR": ("NRU", "Nauru"), "NU": ("NIU", "Niue"),
    "NZ": ("NZL", "New Zealand"), "OM": ("OMN", "Oman"),
    "PA": ("PAN", "Panama"), "PE": ("PER", "Peru"),
    "PF": ("PYF", "French Polynesia"), "PG": ("PNG", "Papua New Guinea"),
    "PH": ("PHL", "Philippines"), "PK": ("PAK", "Pakistan"),
    "PL": ("POL", "Poland"), "PM": ("SPM", "Saint Pierre and Miquelon"),
    "PN": ("PCN", "Pitcairn"), "PR": ("PRI", "Puerto Rico"),
    "PS": ("PSE", "Palestine"), "PT": ("PRT", "Portugal"),
    "PW": ("PLW", "Palau"), "PY": ("PRY", "Paraguay"),
    "QA": ("QAT", "Qatar"), "RE": ("REU", "Reunion"),
    "RO": ("ROU", "Romania"), "RS": ("SRB", "Serbia"),
    "RU": ("RUS", "Russian Federation"), "RW": ("RWA", "Rwanda"),
    "SA": ("SAU", "Saudi Arabia"), "SB": ("SLB", "Solomon Islands"),
    "SC": ("SYC", "Seychelles"), "SD": ("SDN", "Sudan"),
    "SE": ("SWE", "Sweden"), "SG": ("SGP", "Singapore"),
    "SH": ("SHN", "Saint Helena"), "SI": ("SVN", "Slovenia"),
    "SJ": ("SJM", "Svalbard and Jan Mayen"), "SK": ("SVK", "Slovakia"),
    "SL": ("SLE", "Sierra Leone"), "SM": ("SMR", "San Marino"),
    "SN": ("SEN", "Senegal"), "SO": ("SOM", "Somalia"),
    "SR": ("SUR", "Suriname"), "SS": ("SSD", "South Sudan"),
    "ST": ("STP", "Sao Tome and Principe"), "SV": ("SLV", "El Salvador"),
    "SX": ("SXM", "Sint Maarten (Dutch)"), "SY": ("SYR", "Syrian Arab Republic"),
    "SZ": ("SWZ", "Eswatini"), "TC": ("TCA", "Turks and Caicos Islands"),
    "TD": ("TCD", "Chad"), "TF": ("ATF", "French Southern Territories"),
    "TG": ("TGO", "Togo"), "TH": ("THA", "Thailand"),
    "TJ": ("TJK", "Tajikistan"), "TK": ("TKL", "Tokelau"),
    "TL": ("TLS", "Timor-Leste"), "TM": ("TKM", "Turkmenistan"),
    "TN": ("TUN", "Tunisia"), "TO": ("TON", "Tonga"),
    "TR": ("TUR", "Turkiye"), "TT": ("TTO", "Trinidad and Tobago"),
    "TV": ("TUV", "Tuvalu"), "TW": ("TWN", "Taiwan"),
    "TZ": ("TZA", "Tanzania"), "UA": ("UKR", "Ukraine"),
    "UG": ("UGA", "Uganda"), "UM": ("UMI", "US Minor Outlying Islands"),
    "US": ("USA", "United States"), "UY": ("URY", "Uruguay"),
    "UZ": ("UZB", "Uzbekistan"), "VA": ("VAT", "Holy See"),
    "VC": ("VCT", "Saint Vincent and the Grenadines"),
    "VE": ("VEN", "Venezuela"), "VG": ("VGB", "British Virgin Islands"),
    "VI": ("VIR", "US Virgin Islands"), "VN": ("VNM", "Viet Nam"),
    "VU": ("VUT", "Vanuatu"), "WF": ("WLF", "Wallis and Futuna"),
    "WS": ("WSM", "Samoa"), "XK": ("XKX", "Kosovo"),
    "YE": ("YEM", "Yemen"), "YT": ("MYT", "Mayotte"),
    "ZA": ("ZAF", "South Africa"), "ZM": ("ZMB", "Zambia"),
    "ZW": ("ZWE", "Zimbabwe"),
}

# WID regional aggregates (kept out of the country-level release).
WID_AGGREGATE_PREFIXES = {"WO", "XA", "XB", "XC", "XF", "XL", "XM",
                          "XN", "XO", "XR", "XS", "OA", "OB", "OC",
                          "OD", "OE", "QB", "QD", "QE", "QF", "QJ",
                          "QK", "QL", "QM", "QN", "QO", "QP", "QS",
                          "QT", "QU", "QV", "QW", "QX", "QY", "QZ"}


# Reverse lookup: ISO-3 -> (ISO-3, name), built once at import time.
_ISO3_TO_ISO3: dict[str, tuple[str, str]] = {
    v[0]: v for v in ISO2_TO_ISO3.values()
}

# Country-name -> (ISO-3, name) for sources that store full names
# (e.g. LWS stores "United States", "Germany").  Lower-cased for matching.
_NAME_TO_ISO3: dict[str, tuple[str, str]] = {
    v[1].lower(): v for v in ISO2_TO_ISO3.values()
}
# Extra aliases covering variant spellings that appear in LWS / OECD
_NAME_ALIASES: dict[str, tuple[str, str]] = {
    "united states":          ("USA", "United States"),
    "united states of america": ("USA", "United States"),
    "germany":                ("DEU", "Germany"),
    "united kingdom":         ("GBR", "United Kingdom"),
    "great britain":          ("GBR", "United Kingdom"),
    "uk":                     ("GBR", "United Kingdom"),
    "south korea":            ("KOR", "Korea"),
    "republic of korea":      ("KOR", "Korea"),
    "korea, republic of":     ("KOR", "Korea"),
    "slovak republic":        ("SVK", "Slovakia"),
    "czechia":                ("CZE", "Czechia"),
    "czech republic":         ("CZE", "Czechia"),
    "russia":                 ("RUS", "Russian Federation"),
    "taiwan":                 ("TWN", "Taiwan"),
    "iran":                   ("IRN", "Iran"),
    "syria":                  ("SYR", "Syrian Arab Republic"),
    "bolivia":                ("BOL", "Bolivia"),
    "tanzania":               ("TZA", "Tanzania"),
    "moldova":                ("MDA", "Moldova"),
    "north korea":            ("PRK", "Korea (DPRK)"),
    "vietnam":                ("VNM", "Viet Nam"),
    "viet nam":               ("VNM", "Viet Nam"),
    "laos":                   ("LAO", "Lao PDR"),
    "congo":                  ("COG", "Congo"),
    "dr congo":               ("COD", "Congo, Democratic Republic"),
    "democratic republic of the congo": ("COD", "Congo, Democratic Republic"),
}


def name_to_iso3(name: str) -> tuple[str, str] | None:
    """Return (ISO-3, English name) from a country's English name, or None."""
    if not isinstance(name, str):
        return None
    key = name.strip().lower()
    return _NAME_ALIASES.get(key) or _NAME_TO_ISO3.get(key)


def to_iso3(code: str) -> tuple[str, str] | None:
    """Return (ISO-3, English name) or None for unmappable / aggregate codes.

    Accepts:
    * ISO-3166-1 alpha-2 (WID source codes, e.g. "US")
    * ISO-3166-1 alpha-3 (OECD/LWS country codes, e.g. "USA")
    * Full English country names (LWS ``countries`` column, e.g. "United States")
    """
    if not isinstance(code, str):
        return None
    c = code.strip()
    cu = c.upper()
    if cu in WID_AGGREGATE_PREFIXES:
        return None
    if len(cu) == 3:
        return _ISO3_TO_ISO3.get(cu)
    if len(cu) == 2:
        return ISO2_TO_ISO3.get(cu)
    # Longer string -> try name lookup
    return name_to_iso3(c)
