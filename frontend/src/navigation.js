import {
  BookOpen,
  Briefcase,
  Building2,
  ClipboardList,
  Contact,
  FileCheck,
  GraduationCap,
  Landmark,
  LayoutDashboard,
  Network,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  TrendingUp,
  Users,
  Wallet,
  Workflow,
} from 'lucide-react'

const SETTINGS_ITEMS = [
  { label: 'Organization', to: '/settings/organization', icon: Network },
  { label: 'University', to: '/settings/university', icon: Landmark },
  { label: 'General Settings', to: '/settings/general', icon: SlidersHorizontal },
]

// Entries without "to" are placeholders for modules that are not built yet.
export const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
  { label: 'Institutional Directory', icon: Contact },
  { label: 'Academic Management', icon: GraduationCap },
  { label: 'Admissions', icon: ClipboardList },
  { label: 'Student Management', icon: Users },
  { label: 'Staff Management', icon: Briefcase },
  { label: 'Finance', icon: Wallet },
  { label: 'Examinations', icon: FileCheck },
  { label: 'Library', icon: BookOpen },
  { label: 'Hostel Management', icon: Building2 },
  { label: 'Workflow', icon: Workflow },
  { label: 'Reports & Analytics', icon: TrendingUp },
  { label: 'Settings', icon: Settings, to: '/settings', children: SETTINGS_ITEMS },
  { label: 'System Administration', icon: ShieldCheck },
]