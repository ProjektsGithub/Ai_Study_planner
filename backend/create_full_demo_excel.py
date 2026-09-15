"""
Generate 100% complete demo Excel template with ALL 10 curriculum and timetable sheets.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pathlib import Path

def generate_full_demo():
    wb = openpyxl.Workbook()
    default_sheet = wb.active

    # Styling
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    sheets_data = {
        "Universities": {
            "headers": ["Name", "Name_DE", "Country", "Description", "Description_DE"],
            "rows": [
                ["Technical University of Munich", "Technische Universität München", "Germany", "Top ranking European technical university", "Technische Exzellenzuniversität"]
            ]
        },
        "Campuses": {
            "headers": ["University_Name", "Name", "Name_DE", "Location", "Description", "Description_DE"],
            "rows": [
                ["Technical University of Munich", "Garching Campus", "Campus Garching", "Garching bei München", "Main Science & CS Campus", "Hauptcampus für Informatik"]
            ]
        },
        "Programs": {
            "headers": ["Name", "Name_DE", "Code", "Description", "Description_DE"],
            "rows": [
                ["Licence Informatique & IA", "Informatik Bachelor", "INFO-IA", "Bachelor in Computer Science & Artificial Intelligence", "Bachelor-Studiengang Informatik"],
                ["Master Data Science", "Data Science Master", "DS-MAST", "Master in Data Science & Machine Learning", "Master-Studiengang Data Science"]
            ]
        },
        "University_Programs": {
            "headers": ["University_Name", "Program_Name"],
            "rows": [
                ["Technical University of Munich", "Licence Informatique & IA"],
                ["Technical University of Munich", "Master Data Science"]
            ]
        },
        "Tracks": {
            "headers": ["Program_Name", "Name", "Name_DE", "Level", "Total_ECTS_Required", "Description", "Description_DE", "Graduation_Conditions"],
            "rows": [
                ["Licence Informatique & IA", "Software Engineering Track", "Softwaretechnik", "bachelor", 18, "Track focused on software development & AI", "Schwerpunkt Softwareentwicklung", "Pass all mandatory courses & thesis"]
            ]
        },
        "Semesters": {
            "headers": ["Track_Name", "Name", "Name_DE", "Semester_Number", "ECTS_Required", "Description", "Description_DE"],
            "rows": [
                ["Software Engineering Track", "Semester 1", "1. Semester", 1, 30, "Foundational CS & Math semester", "Grundlagen Semester 1"]
            ]
        },
        "TeachingUnits": {
            "headers": ["Semester_Name", "Name", "Name_DE", "Code", "ECTS_Required", "Description", "Description_DE"],
            "rows": [
                ["Semester 1", "UE Core Computer Science", "UE Informatik Grundlagen", "UE-INFO1", 18, "Core computer science fundamentals", "Informatik Kernmodul"]
            ]
        },
        "Courses": {
            "headers": ["Semester_Name", "Teaching_Unit_Name", "Name", "Name_DE", "Code", "ECTS_Credits", "Coefficient", "Difficulty_Level", "Description", "Description_DE"],
            "rows": [
                ["Semester 1", "UE Core Computer Science", "Algorithmique & Structures de Donnees", "Algorithmen & Datenstrukturen", "INF101", 6, 2.0, 3, "Algorithms & Data Structures", "Grundlegende Algorithmen"],
                ["Semester 1", "UE Core Computer Science", "Architecture des Ordinateurs", "Rechnerarchitektur", "INF102", 6, 2.0, 4, "Computer Architecture & Assembly", "Rechnerarchitektur und Assembler"],
                ["Semester 1", "UE Core Computer Science", "Bases de Donnees Relationnelles", "Datenbanksysteme", "INF103", 6, 2.0, 3, "Relational Databases & SQL", "Relationale Datenbanken & SQL"]
            ]
        },
        "Prerequisites": {
            "headers": ["Course_Name", "Prerequisite_Name"],
            "rows": [
                ["Bases de Donnees Relationnelles", "Algorithmique & Structures de Donnees"]
            ]
        },
        "ClassSchedules": {
            "headers": ["Program_Name", "Track_Name", "Semester_Number", "Course_Code", "Course_Name", "Day_Of_Week", "Start_Time", "End_Time", "Session_Type", "Room_Location", "Group_Name", "Is_Fixed"],
            "rows": [
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF101", "Algorithmique & Structures de Donnees", "Monday", "08:30", "10:30", "CM", "Amphi Alan Turing", "Promotion (Fixe)", "TRUE"],
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF101", "Algorithmique & Structures de Donnees", "Tuesday", "10:30", "12:30", "TD", "Salle TD 204", "Groupe 1", "FALSE"],
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF101", "Algorithmique & Structures de Donnees", "Thursday", "14:00", "16:00", "TD", "Salle TD 205", "Groupe 2", "FALSE"],
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF102", "Architecture des Ordinateurs", "Tuesday", "08:30", "10:30", "CM", "Amphi Neumann", "Promotion (Fixe)", "TRUE"],
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF103", "Bases de Donnees Relationnelles", "Wednesday", "08:30", "10:30", "CM", "Amphi Turing", "Promotion (Fixe)", "TRUE"],
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF103", "Bases de Donnees Relationnelles", "Wednesday", "14:00", "16:00", "TP", "Labo Info 1", "Groupe 1", "FALSE"],
                ["Licence Informatique & IA", "Software Engineering Track", 1, "INF103", "Bases de Donnees Relationnelles", "Friday", "14:00", "16:00", "TP", "Labo Info 2", "Groupe 2", "FALSE"]
            ]
        }
    }

    for sheet_name, content in sheets_data.items():
        ws = wb.create_sheet(title=sheet_name)
        ws.append(content["headers"])
        for row in content["rows"]:
            ws.append(row)

        for col_idx, col in enumerate(ws.columns, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[1].height = 26

            max_len = max(len(str(c.value or '')) for c in col)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = max(max_len + 4, 14)

            for row_idx in range(2, ws.max_row + 1):
                c = ws.cell(row=row_idx, column=col_idx)
                c.border = thin_border
                c.alignment = Alignment(vertical="center")

    wb.remove(default_sheet)

    output_path = Path("uploads") / "modele_import_complet_10_onglets.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"Fichier modele complet genere avec succes : {output_path.absolute()}")

if __name__ == "__main__":
    generate_full_demo()
