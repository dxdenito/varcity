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
  UserCog,
  Users,
  Wallet,
  Workflow,
} from 'lucide-react'

const SETTINGS_ITEMS = [
  { label: 'Organization', to: '/settings/organization', icon: Network,     perm: ['settings.university.view', 'settings.general.view'], },
  {
    label: 'General Settings',
    to: '/settings/general',
    icon: SlidersHorizontal,
    perm: 'settings.university.view',
  },
]

const ADMIN_ITEMS = [
  { label: 'Users', to: '/admin/users', icon: UserCog, perm: 'iam.user.view' },
]

// Entries without "to" are placeholders for modules that are not built yet.
// "perm" hides an entry from users who cannot view it at any scope.
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
  { label: 'System Administration', icon: ShieldCheck, to: '/admin', children: ADMIN_ITEMS },
]

export function visibleItems(items, canAnywhere) {
  const allowed = (item) => !item.perm || [].concat(item.perm).some(canAnywhere)

  return items
    .map((item) =>
      item.children ? { ...item, children: item.children.filter(allowed) } : item,
    )
    .filter((item) => (item.children ? item.children.length > 0 : allowed(item)))
}