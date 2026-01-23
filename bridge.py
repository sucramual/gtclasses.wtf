import argparse
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TERM_CODE_TO_SEMESTER = {
    "02": "Spring",
    "05": "Summer",
    "08": "Fall",
}


def safe_get(values: List[Any], idx: Optional[int]) -> Optional[Any]:
    if idx is None or not isinstance(idx, int):
        return None
    if idx < 0 or idx >= len(values):
        return None
    return values[idx]


def format_time_value(value: str) -> str:
    value = value.strip()
    if not value.isdigit():
        return ""
    value = value.zfill(4)
    return f"{value[:2]}:{value[2:]}"


def split_period(period: Optional[str]) -> Tuple[str, str]:
    if not period or period == "TBA":
        return "", ""
    match = re.match(r"^(\d{3,4})\s*-\s*(\d{3,4})$", period)
    if not match:
        return "", ""
    return format_time_value(match.group(1)), format_time_value(match.group(2))


def split_date_range(date_range: Optional[str]) -> Tuple[str, str]:
    if not date_range or date_range == "TBA":
        return "", ""
    parts = [part.strip() for part in date_range.split(" - ")]
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1]


def infer_semester_year(path: Path) -> Tuple[str, int]:
    match = re.match(r"^(\d{4})(\d{2})$", path.stem)
    if not match:
        raise ValueError(
            f"Could not infer term from file name: {path.name}. "
            "Use --semester and --year."
        )
    year = int(match.group(1))
    term_code = match.group(2)
    semester = TERM_CODE_TO_SEMESTER.get(term_code)
    if not semester:
        raise ValueError(
            f"Unsupported term code '{term_code}' in {path.name}. "
            "Use --semester and --year."
        )
    return f"{semester} {year}", year


def collect_instructors(meetings_raw: Iterable[List[Any]]) -> List[Dict[str, str]]:
    seen = set()
    instructors: List[Dict[str, str]] = []
    for meeting in meetings_raw:
        names = meeting[4] if len(meeting) > 4 and meeting[4] else []
        for name in names:
            cleaned = name.replace(" (P)", "")
            if cleaned not in seen:
                instructors.append({"name": cleaned, "email": ""})
                seen.add(cleaned)
    return instructors


def parse_level(restrictions: List[Dict[str, Any]]) -> str:
    for restriction in restrictions:
        if restriction.get("category") != "Level":
            continue
        for value in restriction.get("values", []):
            name = value.get("name", "")
            if "Graduate" in name:
                return "Graduate"
            if "Undergraduate" in name:
                return "Undergrad"
    return ""


def parse_component(caches: Dict[str, Any], sec_data: List[Any]) -> str:
    schedule_types = caches.get("scheduleTypes", [])
    schedule_type = safe_get(schedule_types, sec_data[3] if len(sec_data) > 3 else None)
    if not schedule_type:
        return ""
    return str(schedule_type).rstrip("*")


def normalize_campus(campus: str) -> str:
    campus = campus.replace("Georgia Tech-", "")
    campus = campus.replace("*", "")
    return campus.strip()


def parse_campus(
    caches: Dict[str, Any], sec_data: List[Any], restrictions: List[Dict[str, Any]]
) -> str:
    campuses = caches.get("campuses", [])
    campus = safe_get(campuses, sec_data[4] if len(sec_data) > 4 else None)
    if campus:
        return normalize_campus(str(campus))
    for restriction in restrictions:
        if restriction.get("category") == "Campus":
            values = restriction.get("values", [])
            if values:
                return normalize_campus(str(values[0].get("name", "")))
    return "Atlanta"


def load_term(path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with open(path, "r") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and "courses" in data:
        return data["courses"], data.get("caches", {})
    return data, {}


def output_path_for_input(input_path: str, output_dir: Optional[str]) -> str:
    input_file = Path(input_path)
    name = f"courses-{input_file.stem}-.json"
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        return str(out_dir / name)
    return str(input_file.with_name(name))


def convert_gt_to_wtf(
    input_path: str, output_path: str, semester_name: str, year: int
) -> None:
    courses, caches = load_term(input_path)

    periods = caches.get("periods", [])
    date_ranges = caches.get("dateRanges", [])

    results = []

    for course_key, data in courses.items():
        subject, cat_num = course_key.split(" ", 1)
        course_title = data[0]
        sections_dict = data[1]
        description = html.unescape(data[3]) if data[3] else ""
        prereqs = str(data[2])

        for sec_id, sec_data in sections_dict.items():
            crn = sec_data[0]
            meetings_raw = sec_data[1] if len(sec_data) > 1 and sec_data[1] else []
            credits = sec_data[2] if len(sec_data) > 2 else 0

            restriction_data = sec_data[8] if len(sec_data) > 8 else {}
            restrictions = restriction_data.get("restrictions", [])

            campus = parse_campus(caches, sec_data, restrictions)
            component = parse_component(caches, sec_data)
            level = parse_level(restrictions)

            section_title = sec_data[7] if len(sec_data) > 7 else None
            title = html.unescape(section_title or course_title)

            instructors = collect_instructors(meetings_raw)

            patterns = []
            for meeting in meetings_raw:
                days = meeting[1] if len(meeting) > 1 and meeting[1] else ""
                period_index = meeting[0] if len(meeting) > 0 else None
                period = (
                    safe_get(periods, period_index)
                    if isinstance(period_index, int)
                    else None
                )
                start_time, end_time = split_period(period)

                date_range_index = meeting[5] if len(meeting) > 5 else None
                date_range = (
                    safe_get(date_ranges, date_range_index)
                    if isinstance(date_range_index, int)
                    else None
                )
                start_date, end_date = split_date_range(date_range)

                patterns.append(
                    {
                        "startTime": start_time,
                        "endTime": end_time,
                        "startDate": start_date,
                        "endDate": end_date,
                        "meetsOnMonday": "M" in days,
                        "meetsOnTuesday": "T" in days,
                        "meetsOnWednesday": "W" in days,
                        "meetsOnThursday": "R" in days,
                        "meetsOnFriday": "F" in days,
                        "meetsOnSaturday": "S" in days,
                        "meetsOnSunday": "U" in days,
                    }
                )

            try:
                external_id = int(crn)
            except (TypeError, ValueError):
                external_id = 0

            obj = {
                "id": f"{course_key.replace(' ', '-')}-{sec_id}",
                "externalId": external_id,
                "qGuideId": 0,
                "title": title,
                "subject": subject,
                "subjectDescription": "",
                "catalogNumber": cat_num,
                "level": level,
                "academicGroup": "",
                "semester": semester_name,
                "academicYear": year,
                "classSection": sec_id,
                "component": component,
                "description": description,
                "instructors": instructors,
                "meetingPatterns": patterns,
                "genEdArea": [],
                "divisionalDist": [],
                "crn": crn,
                "credits": credits,
                "campus": campus,
                "prereqText": prereqs,
            }
            results.append(obj)

    with open(output_path, "w") as handle:
        json.dump(results, handle, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert GT crawler output to classes.wtf format."
    )
    parser.add_argument("inputs", nargs="+", help="Term JSON file(s) to convert")
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (defaults to input file location)",
    )
    parser.add_argument("--semester", default=None, help="Override semester name")
    parser.add_argument("--year", type=int, default=None, help="Override year")
    args = parser.parse_args()

    if (args.semester is None) != (args.year is None):
        parser.error("Provide both --semester and --year or neither.")

    for input_path in args.inputs:
        if args.semester is not None:
            semester_name, year = args.semester, args.year
        else:
            semester_name, year = infer_semester_year(Path(input_path))
        output_path = output_path_for_input(input_path, args.out_dir)
        convert_gt_to_wtf(input_path, output_path, semester_name, year)


if __name__ == "__main__":
    main()
