from utils.constants import DEFAULT_SECTION_NAMES

section_aliases = {
    "治療内容": "【治療経過】",
    "病名": "【主病名】",
    "紹介理由": "【紹介目的】",
    "症状": "【症状経過】",
    "処方": "【現在の処方】",
    "薬剤": "【現在の処方】",
    "その他": "【備考】",
    "補足": "【備考】",
    "メモ": "【備考】",
}


def format_output_summary(summary_text):
    processed_text = (
        summary_text.replace('*', '')
        .replace('＊', '')
    )
    return processed_text


def parse_output_summary(summary_text):
    sections = {section: "" for section in DEFAULT_SECTION_NAMES}
    lines = summary_text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        found_section = False

        for section in DEFAULT_SECTION_NAMES:
            if line == section or (line.startswith(section) and len(line.replace(section, "").strip()) < 100):
                current_section = section
                content = line.replace(section, "").strip()
                if content:
                    sections[current_section] = content
                found_section = True
                break

        if not found_section:
            for alias, target_section in section_aliases.items():
                if line.startswith(alias) or line == alias:
                    current_section = target_section
                    content = line.replace(alias, "").replace(":", "").replace("：", "").strip()
                    if content:
                        sections[current_section] = content
                    found_section = True
                    break

        if current_section and line and not found_section:
            if sections[current_section]:
                sections[current_section] += "\n" + line
            else:
                sections[current_section] = line

    return sections
