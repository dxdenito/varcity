SYSTEM = "System administration"
GENERAL = "General"
EXECUTIVE = "Executive and institutional leadership"
LEADERSHIP = "Academic leadership"
STAFF = "Academic staff"
ACADEMIC_ADMIN = "Academic administration"
EXAMS = "Examinations"
FINANCE = "Finance"
PROCUREMENT = "Procurement and stores"
HR = "Human resources and administration"
STUDENT = "Student services"
SUPPORT = "Library, ICT and institutional support"
COMPLIANCE = "Audit and compliance"

_CATALOGUE = {
    SYSTEM: [
        ("super_admin", "Super Admin", "Full access to everything, including future modules."),
    ],
    GENERAL: [
        ("staff_member", "Staff Member", "Baseline for every staff account: dashboard and read-only basics."),
    ],
    EXECUTIVE: [
        ("chancellor", "Chancellor", "Ceremonial head of the university."),
        ("vice_chancellor", "Vice-Chancellor", "Chief executive and academic head of the university."),
        ("dvc_academic", "Deputy Vice-Chancellor, Academic Affairs", "Oversees academic programmes and standards."),
        ("dvc_admin_finance", "Deputy Vice-Chancellor, Administration and Finance", "Oversees administration, finance and resources."),
        ("dvc_research", "Deputy Vice-Chancellor, Research and Innovation", "Oversees research, grants and innovation."),
        ("dvc_student_affairs", "Deputy Vice-Chancellor, Student Affairs", "Oversees student life, welfare and services."),
        ("campus_principal", "Campus Principal / Director", "Leads a campus and its operations."),
        ("directorate_director", "Directorate Director", "Leads a university directorate."),
        ("university_secretary", "University Secretary", "Secretary to the university's governing organs."),
        ("senate_secretary", "Senate Secretary", "Keeps Senate records and resolutions."),
        ("council_secretary", "Council Secretary", "Keeps Council records and resolutions."),
    ],
    LEADERSHIP: [
        ("dean", "Dean", "Approves academic decisions for a college or faculty."),
        ("cod", "Chair of Department (COD)", "Manages and approves work within a department."),
        ("deputy_dean", "Deputy Dean / Associate Dean", "Supports the Dean in running a school or faculty."),
        ("programme_coordinator", "Programme Coordinator", "Coordinates one or more academic programmes."),
        ("departmental_administrator", "Departmental Administrator", "Handles administrative work in a department."),
        ("school_administrator", "School Administrator", "Handles administrative work in a school."),
        ("faculty_administrator", "Faculty Administrator", "Handles administrative work in a faculty or college."),
        ("examination_coordinator", "Examination Coordinator", "Coordinates examinations for a school or faculty."),
        ("dean_of_postgraduate_studies", "Dean of Postgraduate Studies", "Leads postgraduate programmes and research training."),
        ("institute_director", "Institute or Centre Director", "Leads a research institute or centre."),
    ],
    STAFF: [
        ("lecturer", "Lecturer", "Teaching staff with mostly read access."),
        ("professor", "Professor", "Senior academic with teaching and research duties."),
        ("associate_professor", "Associate Professor", "Academic with teaching and research duties."),
        ("senior_lecturer", "Senior Lecturer", "Senior teaching staff."),
        ("tutorial_fellow", "Tutorial Fellow", "Early-career academic with tutoring duties."),
        ("assistant_lecturer", "Assistant Lecturer", "Junior teaching staff."),
        ("part_time_lecturer", "Part-time Lecturer", "Teaches part-time under contract."),
        ("visiting_lecturer", "Visiting Lecturer", "Teaches for a limited period from another institution."),
        ("teaching_assistant", "Teaching Assistant", "Supports lecturers in class and marking."),
        ("researcher", "Researcher", "Carries out research without a teaching load."),
        ("laboratory_technician", "Laboratory Technician", "Prepares and supervises laboratory work."),
        ("clinical_instructor", "Clinical Instructor", "Supervises students in clinical practice."),
        ("postgraduate_supervisor", "Postgraduate Supervisor", "Supervises postgraduate students' research."),
    ],
    ACADEMIC_ADMIN: [
        ("registrar", "Registrar", "Runs academic records and university-wide academic setup."),
        ("deputy_academic_registrar", "Deputy Academic Registrar", "Supports the Registrar in academic administration."),
        ("academic_records_officer", "Academic Records Officer", "Maintains student academic records."),
        ("admissions_officer", "Admissions Officer", "Processes applications and admissions."),
        ("student_registration_officer", "Student Registration Officer", "Registers students each period."),
        ("graduation_officer", "Graduation Officer", "Coordinates graduation lists and ceremonies."),
        ("timetabling_officer", "Timetabling Officer", "Prepares class and examination timetables."),
        ("transcript_officer", "Transcript Officer", "Prepares and issues transcripts."),
        ("student_clearance_officer", "Student Clearance Officer", "Processes student clearance."),
        ("industrial_attachment_coordinator", "Industrial Attachment Coordinator", "Places and tracks students on attachment."),
        ("kuccps_placement_officer", "KUCCPS Placement Officer", "Handles government-sponsored student placement."),
    ],
    EXAMS: [
        ("examination_officer", "Examination Officer", "Manages examination schedules and submissions."),
        ("chief_examiner", "Chief Examiner", "Oversees the setting and marking of an examination."),
        ("departmental_examination_officer", "Departmental Examination Officer", "Runs examination work in a department."),
        ("school_examination_officer", "School Examination Officer", "Runs examination work in a school."),
        ("marks_entry_officer", "Marks Entry Officer", "Enters marks on behalf of lecturers."),
        ("marks_verification_officer", "Marks Verification Officer", "Checks submitted marks for correctness."),
        ("marks_approval_officer", "Marks Approval Officer", "Approves verified marks."),
        ("moderation_officer", "Moderation Officer", "Moderates marks and grading."),
        ("results_publication_officer", "Results Publication Officer", "Publishes approved results."),
        ("external_examiner", "External Examiner", "Reviews examinations on behalf of another institution."),
        ("invigilator", "Invigilator", "Supervises students during examinations."),
    ],
    FINANCE: [
        ("chief_finance_officer", "Chief Finance Officer", "Leads the finance function."),
        ("finance_manager", "Finance Manager", "Manages finance operations."),
        ("accountant", "Accountant", "Keeps the books and prepares reports."),
        ("student_fees_officer", "Student Fees Officer", "Manages student fee accounts."),
        ("revenue_officer", "Revenue Officer", "Collects and records university revenue."),
        ("accounts_receivable_officer", "Accounts Receivable Officer", "Tracks money owed to the university."),
        ("accounts_payable_officer", "Accounts Payable Officer", "Processes money owed by the university."),
        ("cashier", "Cashier", "Receives payments and issues receipts."),
        ("payroll_officer", "Payroll Officer", "Prepares payroll."),
        ("budget_officer", "Budget Officer", "Prepares and monitors budgets."),
        ("internal_auditor", "Internal Auditor", "Reviews financial controls and records."),
        ("helb_liaison_officer", "HELB Liaison Officer", "Handles higher education loan and bursary matters."),
    ],
    PROCUREMENT: [
        ("procurement_manager", "Procurement Manager", "Leads procurement."),
        ("procurement_officer", "Procurement Officer", "Handles requisitions, quotations and orders."),
        ("stores_officer", "Stores Officer", "Receives and issues stores."),
        ("inventory_officer", "Inventory Officer", "Tracks inventory and assets."),
    ],
    HR: [
        ("hr_manager", "HR Director / Manager", "Leads human resources."),
        ("hr_officer", "HR Officer", "Handles day-to-day HR work."),
        ("recruitment_officer", "Recruitment Officer", "Runs staff recruitment."),
        ("staff_records_officer", "Staff Records Officer", "Maintains staff records."),
        ("payroll_administrator", "Payroll Administrator", "Administers the payroll system."),
        ("administration_officer", "Administration Officer", "General administrative support."),
        ("records_management_officer", "Records Management Officer", "Manages institutional records and archives."),
        ("legal_officer", "Legal Officer", "Provides legal support to the university."),
        ("marketing_communications_officer", "Marketing and Communications Officer", "Handles public communication and marketing."),
        ("partnerships_linkages_officer", "Partnerships and Linkages Officer", "Manages partnerships and linkages."),
    ],
    STUDENT: [
        ("dean_of_students", "Dean of Students", "Leads student affairs."),
        ("hostel_administrator", "Hostel Administrator", "Runs the hostels."),
        ("accommodation_officer", "Accommodation Officer", "Allocates student accommodation."),
        ("medical_centre_administrator", "Medical Centre Administrator", "Administers the medical centre."),
        ("counsellor", "Counsellor", "Provides confidential counselling."),
        ("sports_officer", "Sports Officer", "Organises sports and recreation."),
        ("disability_support_officer", "Disability Support Officer", "Supports students with disabilities."),
        ("student_welfare_officer", "Student Welfare Officer", "Handles student welfare cases."),
        ("alumni_relations_officer", "Alumni Relations Officer", "Maintains links with alumni."),
    ],
    SUPPORT: [
        ("university_librarian", "University Librarian", "Leads the library service."),
        ("librarian", "Librarian", "Serves library users."),
        ("library_administrator", "Library Administrator", "Administers library systems and records."),
        ("ict_director", "ICT Director", "Leads ICT services."),
        ("ict_administrator", "ICT Administrator", "Administers ERP users and ICT services."),
        ("systems_administrator", "Systems Administrator", "Administers servers and systems."),
        ("database_administrator", "Database Administrator", "Administers databases."),
        ("network_administrator", "Network Administrator", "Administers the network."),
        ("helpdesk_officer", "Helpdesk Officer", "Supports users with ICT issues."),
        ("security_administrator", "Security Administrator", "Administers security controls and monitoring."),
        ("fleet_manager", "Fleet Manager", "Manages university vehicles."),
        ("transport_officer", "Transport Officer", "Schedules transport."),
        ("chaplain", "Chaplain", "Provides spiritual support."),
        ("research_grants_officer", "Research Grants Officer", "Administers research grants."),
        ("estates_works_officer", "Estates and Works Officer", "Manages buildings and maintenance."),
    ],
    COMPLIANCE: [
        ("auditor", "Auditor", "Read-only access for audit and review."),
        ("data_protection_officer", "Data Protection Officer", "Oversees data protection and privacy compliance."),
        ("quality_assurance_officer", "Quality Assurance Officer", "Monitors quality and accreditation requirements."),
    ],
}

STARTER_ROLES: dict[str, tuple[str, str, str]] = {}
for _category, _entries in _CATALOGUE.items():
    for _key, _name, _description in _entries:
        if _key in STARTER_ROLES:
            raise ValueError(f"Duplicate user type key: {_key}")
        STARTER_ROLES[_key] = (_name, _description, _category)

if len({value[0].lower() for value in STARTER_ROLES.values()}) != len(STARTER_ROLES):
    raise ValueError("Duplicate user type name in the catalogue")