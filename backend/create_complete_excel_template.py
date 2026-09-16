"""
Generate a complete Excel import template with realistic demo data.
This file matches the exact structure expected by ImportService.parse_excel_file()

10 sheets:
  1. Universities
  2. Campuses
  3. Programs
  4. University_Programs
  5. Tracks
  6. Semesters
  7. TeachingUnits
  8. Courses
  9. Prerequisites
  10. ClassSchedules
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os

def style_header(ws, headers, color="4472C4"):
    """Apply professional styling to the header row"""
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Auto-size columns
    for col_idx in range(1, len(headers) + 1):
        max_len = len(str(headers[col_idx - 1]))
        for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
            for cell in row:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 40)


def add_data_rows(ws, data, start_row=2):
    """Add data rows with alternating colors"""
    light_fill = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for row_idx, row_data in enumerate(data, start_row):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            if row_idx % 2 == 0:
                cell.fill = light_fill


def create_template():
    wb = openpyxl.Workbook()
    
    # ============================================================
    # 1. UNIVERSITIES
    # ============================================================
    ws = wb.active
    ws.title = "Universities"
    headers = ["name", "name_de", "country", "description", "description_de"]
    style_header(ws, headers, "1F4E79")
    
    universities = [
        ("Hochschule für Technik Stuttgart", "Hochschule für Technik Stuttgart", "Germany",
         "University of Applied Sciences Stuttgart – leading technical university in Baden-Württemberg",
         "Hochschule für Technik Stuttgart – führende technische Hochschule in Baden-Württemberg"),
        ("Université de Strasbourg", "Universität Straßburg", "France",
         "One of the largest universities in France, member of the League of European Research Universities",
         "Eine der größten Universitäten Frankreichs, Mitglied der Liga Europäischer Forschungsuniversitäten"),
    ]
    add_data_rows(ws, universities)
    
    # ============================================================
    # 2. CAMPUSES
    # ============================================================
    ws = wb.create_sheet("Campuses")
    headers = ["university_name", "name", "name_de", "location", "description", "description_de"]
    style_header(ws, headers, "2E75B6")
    
    campuses = [
        ("Hochschule für Technik Stuttgart", "Campus Stadtmitte", "Campus Stadtmitte",
         "Schellingstraße 24, 70174 Stuttgart",
         "Main campus in the city center", "Hauptcampus in der Stadtmitte"),
        ("Hochschule für Technik Stuttgart", "Campus Bau", "Campus Bau",
         "Schellingstraße 24a, 70174 Stuttgart",
         "Building and Architecture campus", "Campus für Bau und Architektur"),
        ("Université de Strasbourg", "Campus Esplanade", "Campus Esplanade",
         "4 Rue Blaise Pascal, 67000 Strasbourg",
         "Main Science and Engineering campus", "Haupt-Campus für Wissenschaft und Ingenieurwesen"),
    ]
    add_data_rows(ws, campuses)
    
    # ============================================================
    # 3. PROGRAMS
    # ============================================================
    ws = wb.create_sheet("Programs")
    headers = ["name", "name_de", "code", "description", "description_de"]
    style_header(ws, headers, "548235")
    
    programs = [
        ("Computer Science", "Informatik", "CS",
         "Bachelor and Master programs in Computer Science covering software engineering, AI, and systems",
         "Bachelor- und Masterstudiengänge in Informatik mit Schwerpunkt Software Engineering, KI und Systeme"),
        ("Business Informatics", "Wirtschaftsinformatik", "BI",
         "Interdisciplinary program combining IT and business management",
         "Interdisziplinärer Studiengang, der IT und Betriebswirtschaft verbindet"),
    ]
    add_data_rows(ws, programs)
    
    # ============================================================
    # 4. UNIVERSITY_PROGRAMS
    # ============================================================
    ws = wb.create_sheet("University_Programs")
    headers = ["university_name", "program_name"]
    style_header(ws, headers, "BF8F00")
    
    links = [
        ("Hochschule für Technik Stuttgart", "Computer Science"),
        ("Hochschule für Technik Stuttgart", "Business Informatics"),
        ("Université de Strasbourg", "Computer Science"),
    ]
    add_data_rows(ws, links)
    
    # ============================================================
    # 5. TRACKS (Filières / Schwerpunkte)
    # ============================================================
    ws = wb.create_sheet("Tracks")
    headers = ["program_name", "name", "name_de", "level", "total_ects_required",
               "description", "description_de", "graduation_conditions"]
    style_header(ws, headers, "843C0B")
    
    tracks = [
        ("Computer Science", "Software Engineering", "Software Engineering", "bachelor", 180,
         "Focus on modern software development, DevOps, and cloud computing",
         "Schwerpunkt auf moderner Softwareentwicklung, DevOps und Cloud Computing",
         "Minimum 180 ECTS, all mandatory modules passed, bachelor thesis with grade >= 4.0"),
        ("Computer Science", "Artificial Intelligence", "Künstliche Intelligenz", "master", 120,
         "Advanced studies in Machine Learning, NLP and Computer Vision",
         "Vertiefte Studien in Machine Learning, NLP und Computer Vision",
         "Minimum 120 ECTS, master thesis with grade >= 4.0, research seminar passed"),
        ("Business Informatics", "Digital Transformation", "Digitale Transformation", "bachelor", 180,
         "Focus on digital business models, ERP systems, and data analytics",
         "Schwerpunkt auf digitale Geschäftsmodelle, ERP-Systeme und Datenanalyse",
         "Minimum 180 ECTS, internship report, bachelor thesis"),
    ]
    add_data_rows(ws, tracks)
    
    # ============================================================
    # 6. SEMESTERS
    # ============================================================
    ws = wb.create_sheet("Semesters")
    headers = ["track_name", "name", "name_de", "semester_number", "ects_required",
               "description", "description_de"]
    style_header(ws, headers, "7030A0")
    
    semesters = [
        # Software Engineering (Bachelor - 6 semesters)
        ("Software Engineering", "SE Semester 1", "SE Semester 1", 1, 30,
         "Foundations: Programming, Math, Algorithms", "Grundlagen: Programmierung, Mathematik, Algorithmen"),
        ("Software Engineering", "SE Semester 2", "SE Semester 2", 2, 30,
         "Core: Databases, Web Development, OOP", "Kern: Datenbanken, Webentwicklung, OOP"),
        ("Software Engineering", "SE Semester 3", "SE Semester 3", 3, 30,
         "Advanced: Software Architecture, Testing, DevOps", "Fortgeschritten: Softwarearchitektur, Testing, DevOps"),
        ("Software Engineering", "SE Semester 4", "SE Semester 4", 4, 30,
         "Specialization: Cloud, Security, Mobile", "Spezialisierung: Cloud, Sicherheit, Mobile"),
        
        # Artificial Intelligence (Master - 4 semesters)
        ("Artificial Intelligence", "AI Semester 1", "KI Semester 1", 1, 30,
         "Foundations: Statistical Learning, Deep Learning", "Grundlagen: Statistisches Lernen, Deep Learning"),
        ("Artificial Intelligence", "AI Semester 2", "KI Semester 2", 2, 30,
         "Core: NLP, Computer Vision, Reinforcement Learning", "Kern: NLP, Computer Vision, Reinforcement Learning"),
        
        # Digital Transformation (Bachelor)
        ("Digital Transformation", "DT Semester 1", "DT Semester 1", 1, 30,
         "Foundations: Business, IT Basics, Math", "Grundlagen: BWL, IT-Grundlagen, Mathematik"),
        ("Digital Transformation", "DT Semester 2", "DT Semester 2", 2, 30,
         "Core: ERP, Databases, Data Analytics", "Kern: ERP, Datenbanken, Datenanalyse"),
    ]
    add_data_rows(ws, semesters)
    
    # ============================================================
    # 7. TEACHING UNITS (UE / Modulgruppen)
    # ============================================================
    ws = wb.create_sheet("TeachingUnits")
    headers = ["semester_name", "name", "name_de", "code", "ects_required",
               "description", "description_de"]
    style_header(ws, headers, "C55A11")
    
    teaching_units = [
        # SE Semester 1
        ("SE Semester 1", "Programming Fundamentals", "Programmierung Grundlagen", "UE-SE1-PROG", 12,
         "Introduction to programming and algorithms", "Einführung in Programmierung und Algorithmen"),
        ("SE Semester 1", "Mathematics for CS", "Mathematik für Informatik", "UE-SE1-MATH", 10,
         "Discrete math, linear algebra, calculus", "Diskrete Mathematik, Lineare Algebra, Analysis"),
        ("SE Semester 1", "General Education 1", "Allgemeinbildung 1", "UE-SE1-GEN", 8,
         "English, project management, soft skills", "Englisch, Projektmanagement, Soft Skills"),
        
        # SE Semester 2
        ("SE Semester 2", "Web and Database Systems", "Web- und Datenbanksysteme", "UE-SE2-WEB", 14,
         "Web technologies and database design", "Webtechnologien und Datenbankdesign"),
        ("SE Semester 2", "Object-Oriented Design", "Objektorientiertes Design", "UE-SE2-OOD", 10,
         "OOP patterns and design principles", "OOP-Muster und Designprinzipien"),
        ("SE Semester 2", "Operating Systems", "Betriebssysteme", "UE-SE2-OS", 6,
         "OS concepts and system programming", "BS-Konzepte und Systemprogrammierung"),
        
        # SE Semester 3
        ("SE Semester 3", "Software Architecture", "Softwarearchitektur", "UE-SE3-ARCH", 14,
         "Design patterns, microservices, clean architecture", "Entwurfsmuster, Microservices, Clean Architecture"),
        ("SE Semester 3", "Quality Assurance", "Qualitätssicherung", "UE-SE3-QA", 10,
         "Testing strategies, CI/CD, code quality", "Teststrategien, CI/CD, Codequalität"),
        
        # SE Semester 4
        ("SE Semester 4", "Cloud & DevOps", "Cloud & DevOps", "UE-SE4-CLOUD", 16,
         "Cloud platforms, containers, infrastructure as code", "Cloud-Plattformen, Container, Infrastructure as Code"),
        ("SE Semester 4", "Security Fundamentals", "Sicherheitsgrundlagen", "UE-SE4-SEC", 8,
         "Application security, cryptography, OWASP", "Anwendungssicherheit, Kryptographie, OWASP"),
        
        # AI Semester 1
        ("AI Semester 1", "Machine Learning", "Maschinelles Lernen", "UE-AI1-ML", 16,
         "Supervised, unsupervised, and semi-supervised learning", "Überwachtes, unüberwachtes und semi-überwachtes Lernen"),
        ("AI Semester 1", "Deep Learning", "Deep Learning", "UE-AI1-DL", 14,
         "Neural networks, CNNs, RNNs, Transformers", "Neuronale Netze, CNNs, RNNs, Transformer"),
        
        # AI Semester 2
        ("AI Semester 2", "Natural Language Processing", "Natürliche Sprachverarbeitung", "UE-AI2-NLP", 16,
         "Text processing, language models, chatbots", "Textverarbeitung, Sprachmodelle, Chatbots"),
        ("AI Semester 2", "Computer Vision", "Computer Vision", "UE-AI2-CV", 14,
         "Image recognition, object detection, video analysis", "Bilderkennung, Objekterkennung, Videoanalyse"),
        
        # DT Semester 1
        ("DT Semester 1", "Business Administration", "Betriebswirtschaftslehre", "UE-DT1-BWL", 14,
         "Management, marketing, accounting fundamentals", "Management, Marketing, Rechnungswesen Grundlagen"),
        ("DT Semester 1", "IT Fundamentals", "IT-Grundlagen", "UE-DT1-IT", 10,
         "Computer architecture, networks, programming basics", "Rechnerarchitektur, Netzwerke, Programmierung Grundlagen"),
        
        # DT Semester 2
        ("DT Semester 2", "Enterprise Systems", "Unternehmenssysteme", "UE-DT2-ERP", 16,
         "ERP systems, business process management", "ERP-Systeme, Geschäftsprozessmanagement"),
        ("DT Semester 2", "Data Analytics", "Datenanalyse", "UE-DT2-DATA", 14,
         "Statistics, data visualization, business intelligence", "Statistik, Datenvisualisierung, Business Intelligence"),
    ]
    add_data_rows(ws, teaching_units)
    
    # ============================================================
    # 8. COURSES
    # ============================================================
    ws = wb.create_sheet("Courses")
    headers = ["semester_name", "teaching_unit_name", "name", "name_de", "code",
               "ects_credits", "coefficient", "difficulty_level", "description", "description_de"]
    style_header(ws, headers, "C00000")
    
    courses = [
        # SE Semester 1 — Programming Fundamentals
        ("SE Semester 1", "Programming Fundamentals", "Introduction to Python", "Einführung in Python", "CS101",
         6, 2.0, 2, "Python basics, data types, control flow, functions", "Python Grundlagen, Datentypen, Kontrollfluss, Funktionen"),
        ("SE Semester 1", "Programming Fundamentals", "Algorithms and Data Structures", "Algorithmen und Datenstrukturen", "CS102",
         6, 3.0, 3, "Sorting, searching, trees, graphs, complexity analysis", "Sortieren, Suchen, Bäume, Graphen, Komplexitätsanalyse"),
        
        # SE Semester 1 — Mathematics for CS
        ("SE Semester 1", "Mathematics for CS", "Discrete Mathematics", "Diskrete Mathematik", "MA101",
         5, 2.0, 3, "Logic, sets, combinatorics, graph theory", "Logik, Mengen, Kombinatorik, Graphentheorie"),
        ("SE Semester 1", "Mathematics for CS", "Linear Algebra", "Lineare Algebra", "MA102",
         5, 2.0, 3, "Matrices, vectors, eigenvalues, linear transformations", "Matrizen, Vektoren, Eigenwerte, lineare Transformationen"),
        
        # SE Semester 1 — General Education
        ("SE Semester 1", "General Education 1", "Academic English", "Wissenschaftliches Englisch", "GEN101",
         4, 1.0, 1, "Technical writing and presentation skills", "Technisches Schreiben und Präsentationstechniken"),
        ("SE Semester 1", "General Education 1", "Project Management Basics", "Projektmanagement Grundlagen", "GEN102",
         4, 1.0, 2, "Agile, Scrum, Kanban fundamentals", "Agile, Scrum, Kanban Grundlagen"),
        
        # SE Semester 2 — Web and Database Systems
        ("SE Semester 2", "Web and Database Systems", "Web Development", "Webentwicklung", "CS201",
         6, 2.0, 2, "HTML, CSS, JavaScript, React fundamentals", "HTML, CSS, JavaScript, React Grundlagen"),
        ("SE Semester 2", "Web and Database Systems", "Database Design", "Datenbankdesign", "CS202",
         5, 2.5, 3, "SQL, normalization, ER modeling, PostgreSQL", "SQL, Normalisierung, ER-Modellierung, PostgreSQL"),
        ("SE Semester 2", "Web and Database Systems", "REST API Development", "REST API Entwicklung", "CS203",
         3, 1.5, 3, "RESTful services, FastAPI, authentication", "RESTful Services, FastAPI, Authentifizierung"),
        
        # SE Semester 2 — OOP
        ("SE Semester 2", "Object-Oriented Design", "Java Programming", "Java Programmierung", "CS204",
         5, 2.0, 3, "OOP concepts, inheritance, polymorphism, generics", "OOP-Konzepte, Vererbung, Polymorphismus, Generics"),
        ("SE Semester 2", "Object-Oriented Design", "Design Patterns", "Entwurfsmuster", "CS205",
         5, 2.5, 4, "GoF patterns, SOLID principles, refactoring", "GoF-Muster, SOLID-Prinzipien, Refactoring"),
        
        # SE Semester 2 — OS
        ("SE Semester 2", "Operating Systems", "Systems Programming", "Systemprogrammierung", "CS206",
         6, 2.0, 4, "Processes, threads, memory management, file systems", "Prozesse, Threads, Speicherverwaltung, Dateisysteme"),
        
        # SE Semester 3 — Software Architecture
        ("SE Semester 3", "Software Architecture", "Microservices Architecture", "Microservices-Architektur", "CS301",
         7, 3.0, 4, "Service decomposition, API gateways, event-driven design", "Service-Zerlegung, API-Gateways, ereignisgesteuerte Architektur"),
        ("SE Semester 3", "Software Architecture", "Clean Architecture", "Clean Architecture", "CS302",
         7, 3.0, 4, "Hexagonal architecture, DDD, CQRS patterns", "Hexagonale Architektur, DDD, CQRS-Muster"),
        
        # SE Semester 3 — QA
        ("SE Semester 3", "Quality Assurance", "Software Testing", "Software-Testing", "CS303",
         5, 2.0, 3, "Unit, integration, E2E testing, TDD, BDD", "Unit-, Integrations-, E2E-Tests, TDD, BDD"),
        ("SE Semester 3", "Quality Assurance", "CI/CD Pipelines", "CI/CD Pipelines", "CS304",
         5, 2.0, 3, "GitHub Actions, Jenkins, Docker, automated deployment", "GitHub Actions, Jenkins, Docker, automatisierte Bereitstellung"),
        
        # SE Semester 4 — Cloud & DevOps
        ("SE Semester 4", "Cloud & DevOps", "Cloud Computing", "Cloud Computing", "CS401",
         6, 2.5, 4, "AWS/Azure/GCP fundamentals, serverless, IaC with Terraform", "AWS/Azure/GCP Grundlagen, Serverless, IaC mit Terraform"),
        ("SE Semester 4", "Cloud & DevOps", "Container Orchestration", "Container-Orchestrierung", "CS402",
         5, 2.5, 4, "Docker, Kubernetes, Helm charts, monitoring", "Docker, Kubernetes, Helm Charts, Monitoring"),
        ("SE Semester 4", "Cloud & DevOps", "Infrastructure as Code", "Infrastructure as Code", "CS403",
         5, 2.0, 3, "Terraform, Ansible, GitOps workflows", "Terraform, Ansible, GitOps Workflows"),
        
        # SE Semester 4 — Security
        ("SE Semester 4", "Security Fundamentals", "Application Security", "Anwendungssicherheit", "CS404",
         4, 2.0, 3, "OWASP Top 10, secure coding, penetration testing", "OWASP Top 10, Sicheres Programmieren, Penetrationstests"),
        ("SE Semester 4", "Security Fundamentals", "Cryptography", "Kryptographie", "CS405",
         4, 2.0, 4, "Symmetric/asymmetric encryption, PKI, TLS, hashing", "Symmetrische/asymmetrische Verschlüsselung, PKI, TLS, Hashing"),
        
        # AI Semester 1 — Machine Learning
        ("AI Semester 1", "Machine Learning", "Statistical Learning", "Statistisches Lernen", "AI101",
         6, 3.0, 4, "Regression, classification, SVM, ensemble methods", "Regression, Klassifikation, SVM, Ensemble-Methoden"),
        ("AI Semester 1", "Machine Learning", "Probabilistic Models", "Probabilistische Modelle", "AI102",
         5, 2.5, 5, "Bayesian networks, HMMs, graphical models", "Bayes'sche Netze, HMMs, grafische Modelle"),
        ("AI Semester 1", "Machine Learning", "ML Engineering", "ML Engineering", "AI103",
         5, 2.0, 3, "MLOps, model deployment, experiment tracking", "MLOps, Modell-Deployment, Experiment-Tracking"),
        
        # AI Semester 1 — Deep Learning
        ("AI Semester 1", "Deep Learning", "Neural Networks", "Neuronale Netze", "AI104",
         7, 3.0, 4, "Feedforward, CNNs, RNNs, LSTMs, attention mechanisms", "Feedforward, CNNs, RNNs, LSTMs, Aufmerksamkeitsmechanismen"),
        ("AI Semester 1", "Deep Learning", "Transformer Architectures", "Transformer-Architekturen", "AI105",
         7, 3.0, 5, "Self-attention, BERT, GPT, Vision Transformers", "Self-Attention, BERT, GPT, Vision Transformers"),
        
        # AI Semester 2 — NLP
        ("AI Semester 2", "Natural Language Processing", "Text Processing", "Textverarbeitung", "AI201",
         6, 2.5, 4, "Tokenization, embeddings, sentiment analysis", "Tokenisierung, Embeddings, Sentiment-Analyse"),
        ("AI Semester 2", "Natural Language Processing", "Large Language Models", "Große Sprachmodelle", "AI202",
         5, 3.0, 5, "Fine-tuning, RLHF, RAG, prompt engineering", "Feinabstimmung, RLHF, RAG, Prompt Engineering"),
        ("AI Semester 2", "Natural Language Processing", "Conversational AI", "Konversationelle KI", "AI203",
         5, 2.0, 4, "Chatbot design, dialogue systems, voice assistants", "Chatbot-Design, Dialogsysteme, Sprachassistenten"),
        
        # AI Semester 2 — Computer Vision
        ("AI Semester 2", "Computer Vision", "Image Recognition", "Bilderkennung", "AI204",
         7, 3.0, 4, "Classification, segmentation, GANs, diffusion models", "Klassifikation, Segmentierung, GANs, Diffusionsmodelle"),
        ("AI Semester 2", "Computer Vision", "3D Vision and Video", "3D Vision und Video", "AI205",
         7, 3.0, 5, "Depth estimation, 3D reconstruction, video understanding", "Tiefenschätzung, 3D-Rekonstruktion, Videoverständnis"),
        
        # DT Semester 1
        ("DT Semester 1", "Business Administration", "Management Fundamentals", "Management Grundlagen", "DT101",
         5, 2.0, 2, "Organizational theory, leadership, strategy", "Organisationstheorie, Führung, Strategie"),
        ("DT Semester 1", "Business Administration", "Marketing and Sales", "Marketing und Vertrieb", "DT102",
         5, 1.5, 2, "Digital marketing, CRM, market analysis", "Digitales Marketing, CRM, Marktanalyse"),
        ("DT Semester 1", "Business Administration", "Financial Accounting", "Finanzbuchhaltung", "DT103",
         4, 2.0, 3, "Balance sheet, P&L, cost accounting", "Bilanz, GuV, Kostenrechnung"),
        ("DT Semester 1", "IT Fundamentals", "Programming Basics", "Programmierung Grundlagen", "DT104",
         5, 2.0, 2, "Python basics for business applications", "Python Grundlagen für Geschäftsanwendungen"),
        ("DT Semester 1", "IT Fundamentals", "Computer Networks", "Rechnernetze", "DT105",
         5, 1.5, 2, "TCP/IP, DNS, HTTP, network security basics", "TCP/IP, DNS, HTTP, Netzwerksicherheit Grundlagen"),
        
        # DT Semester 2
        ("DT Semester 2", "Enterprise Systems", "ERP Systems (SAP)", "ERP-Systeme (SAP)", "DT201",
         6, 2.5, 3, "SAP S/4HANA modules, configuration, customizing", "SAP S/4HANA Module, Konfiguration, Customizing"),
        ("DT Semester 2", "Enterprise Systems", "Business Process Modeling", "Geschäftsprozessmodellierung", "DT202",
         5, 2.0, 3, "BPMN 2.0, process mining, automation", "BPMN 2.0, Process Mining, Automatisierung"),
        ("DT Semester 2", "Enterprise Systems", "Digital Business Models", "Digitale Geschäftsmodelle", "DT203",
         5, 2.0, 3, "Platform economy, subscription models, marketplace design", "Plattformökonomie, Abomodelle, Marktplatzdesign"),
        ("DT Semester 2", "Data Analytics", "Business Intelligence", "Business Intelligence", "DT204",
         7, 2.5, 3, "Data warehousing, OLAP, dashboard design, Power BI", "Data Warehousing, OLAP, Dashboard-Design, Power BI"),
        ("DT Semester 2", "Data Analytics", "Statistics for Business", "Statistik für Wirtschaft", "DT205",
         7, 2.0, 3, "Descriptive and inferential statistics, hypothesis testing", "Deskriptive und schließende Statistik, Hypothesentests"),
    ]
    add_data_rows(ws, courses)
    
    # ============================================================
    # 9. PREREQUISITES
    # ============================================================
    ws = wb.create_sheet("Prerequisites")
    headers = ["course_name", "prerequisite_name"]
    style_header(ws, headers, "404040")
    
    prerequisites = [
        # SE track prerequisites
        ("Algorithms and Data Structures", "Introduction to Python"),
        ("Web Development", "Introduction to Python"),
        ("Database Design", "Introduction to Python"),
        ("REST API Development", "Web Development"),
        ("REST API Development", "Database Design"),
        ("Java Programming", "Introduction to Python"),
        ("Design Patterns", "Java Programming"),
        ("Systems Programming", "Algorithms and Data Structures"),
        ("Microservices Architecture", "Design Patterns"),
        ("Microservices Architecture", "REST API Development"),
        ("Clean Architecture", "Design Patterns"),
        ("Software Testing", "Java Programming"),
        ("CI/CD Pipelines", "Software Testing"),
        ("Cloud Computing", "Microservices Architecture"),
        ("Container Orchestration", "Cloud Computing"),
        ("Infrastructure as Code", "Cloud Computing"),
        ("Application Security", "Web Development"),
        ("Cryptography", "Discrete Mathematics"),
        
        # AI track prerequisites
        ("Statistical Learning", "Linear Algebra"),
        ("Probabilistic Models", "Statistical Learning"),
        ("ML Engineering", "Statistical Learning"),
        ("Neural Networks", "Statistical Learning"),
        ("Neural Networks", "Linear Algebra"),
        ("Transformer Architectures", "Neural Networks"),
        ("Text Processing", "Neural Networks"),
        ("Large Language Models", "Transformer Architectures"),
        ("Conversational AI", "Text Processing"),
        ("Image Recognition", "Neural Networks"),
        ("3D Vision and Video", "Image Recognition"),
        
        # DT track prerequisites
        ("ERP Systems (SAP)", "Programming Basics"),
        ("Business Process Modeling", "Management Fundamentals"),
        ("Digital Business Models", "Marketing and Sales"),
        ("Business Intelligence", "Programming Basics"),
        ("Statistics for Business", "Financial Accounting"),
    ]
    add_data_rows(ws, prerequisites)
    
    # ============================================================
    # 10. CLASS SCHEDULES (Emploi du temps)
    # ============================================================
    ws = wb.create_sheet("ClassSchedules")
    headers = ["program_name", "track_name", "semester_number", "course_code", "course_name",
               "day_of_week", "start_time", "end_time", "session_type", "room_location",
               "group_name", "is_fixed"]
    style_header(ws, headers, "006600")
    
    schedules = [
        # SE Semester 1 schedules
        ("Computer Science", "Software Engineering", 1, "CS101", "Introduction to Python",
         "Monday", "08:30", "10:00", "CM", "Amphi A", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 1, "CS101", "Introduction to Python (TD)",
         "Monday", "10:15", "11:45", "TD", "Salle 101", "Groupe 1", "false"),
        ("Computer Science", "Software Engineering", 1, "CS101", "Introduction to Python (TD)",
         "Monday", "10:15", "11:45", "TD", "Salle 102", "Groupe 2", "false"),
        ("Computer Science", "Software Engineering", 1, "CS101", "Introduction to Python (TP)",
         "Wednesday", "14:00", "15:30", "TP", "Lab Info 1", "Groupe 1", "false"),
        ("Computer Science", "Software Engineering", 1, "CS102", "Algorithms and Data Structures",
         "Tuesday", "08:30", "10:00", "CM", "Amphi B", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 1, "CS102", "Algorithms and Data Structures (TD)",
         "Tuesday", "10:15", "11:45", "TD", "Salle 201", "Groupe 1", "false"),
        ("Computer Science", "Software Engineering", 1, "MA101", "Discrete Mathematics",
         "Wednesday", "08:30", "10:00", "CM", "Amphi A", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 1, "MA102", "Linear Algebra",
         "Thursday", "08:30", "10:00", "CM", "Amphi A", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 1, "MA102", "Linear Algebra (TD)",
         "Thursday", "10:15", "11:45", "TD", "Salle 103", "Groupe 1", "false"),
        ("Computer Science", "Software Engineering", 1, "GEN101", "Academic English",
         "Friday", "08:30", "10:00", "TD", "Salle 301", "Groupe 1", "false"),
        ("Computer Science", "Software Engineering", 1, "GEN102", "Project Management Basics",
         "Friday", "10:15", "11:45", "CM", "Salle 302", "Promotion", "true"),
        
        # SE Semester 2 schedules
        ("Computer Science", "Software Engineering", 2, "CS201", "Web Development",
         "Monday", "08:30", "10:00", "CM", "Amphi C", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 2, "CS201", "Web Development (TP)",
         "Monday", "14:00", "16:00", "TP", "Lab Info 2", "Groupe 1", "false"),
        ("Computer Science", "Software Engineering", 2, "CS202", "Database Design",
         "Tuesday", "08:30", "10:00", "CM", "Amphi B", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 2, "CS204", "Java Programming",
         "Wednesday", "08:30", "10:00", "CM", "Amphi A", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 2, "CS205", "Design Patterns",
         "Thursday", "08:30", "10:00", "CM", "Amphi B", "Promotion", "true"),
        ("Computer Science", "Software Engineering", 2, "CS206", "Systems Programming",
         "Friday", "08:30", "10:00", "CM", "Amphi C", "Promotion", "true"),
        
        # AI Semester 1 schedules
        ("Computer Science", "Artificial Intelligence", 1, "AI101", "Statistical Learning",
         "Monday", "09:00", "11:00", "CM", "Amphi A", "Promotion", "true"),
        ("Computer Science", "Artificial Intelligence", 1, "AI102", "Probabilistic Models",
         "Tuesday", "09:00", "11:00", "CM", "Amphi B", "Promotion", "true"),
        ("Computer Science", "Artificial Intelligence", 1, "AI103", "ML Engineering",
         "Wednesday", "14:00", "16:00", "TP", "Lab GPU", "Groupe 1", "false"),
        ("Computer Science", "Artificial Intelligence", 1, "AI104", "Neural Networks",
         "Thursday", "09:00", "11:00", "CM", "Amphi A", "Promotion", "true"),
        ("Computer Science", "Artificial Intelligence", 1, "AI105", "Transformer Architectures",
         "Friday", "09:00", "11:00", "CM", "Amphi A", "Promotion", "true"),
        
        # DT Semester 1 schedules
        ("Business Informatics", "Digital Transformation", 1, "DT101", "Management Fundamentals",
         "Monday", "08:30", "10:00", "CM", "Salle B01", "Promotion", "true"),
        ("Business Informatics", "Digital Transformation", 1, "DT102", "Marketing and Sales",
         "Tuesday", "08:30", "10:00", "CM", "Salle B02", "Promotion", "true"),
        ("Business Informatics", "Digital Transformation", 1, "DT103", "Financial Accounting",
         "Wednesday", "08:30", "10:00", "CM", "Salle B01", "Promotion", "true"),
        ("Business Informatics", "Digital Transformation", 1, "DT104", "Programming Basics",
         "Thursday", "08:30", "10:00", "CM", "Salle B03", "Promotion", "true"),
        ("Business Informatics", "Digital Transformation", 1, "DT104", "Programming Basics (TP)",
         "Thursday", "14:00", "16:00", "TP", "Lab Info 3", "Groupe 1", "false"),
        ("Business Informatics", "Digital Transformation", 1, "DT105", "Computer Networks",
         "Friday", "08:30", "10:00", "CM", "Salle B01", "Promotion", "true"),
    ]
    add_data_rows(ws, schedules)
    
    # ============================================================
    # SAVE
    # ============================================================
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "modele_import_complet_10_onglets.xlsx")
    wb.save(output_path)
    print(f"✅ Excel template created successfully!")
    print(f"📁 Path: {output_path}")
    print(f"\n📊 Summary:")
    print(f"   Universities:      {len(universities)} records")
    print(f"   Campuses:          {len(campuses)} records")
    print(f"   Programs:          {len(programs)} records")
    print(f"   University_Programs: {len(links)} records")
    print(f"   Tracks:            {len(tracks)} records")
    print(f"   Semesters:         {len(semesters)} records")
    print(f"   TeachingUnits:     {len(teaching_units)} records")
    print(f"   Courses:           {len(courses)} records")
    print(f"   Prerequisites:     {len(prerequisites)} records")
    print(f"   ClassSchedules:    {len(schedules)} records")
    print(f"   ─────────────────────────────────")
    total = (len(universities) + len(campuses) + len(programs) + len(links) + 
             len(tracks) + len(semesters) + len(teaching_units) + len(courses) + 
             len(prerequisites) + len(schedules))
    print(f"   TOTAL:             {total} records")
    
    return output_path


if __name__ == "__main__":
    create_template()
