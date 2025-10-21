export interface ThemeColors {
  name: string;
  description: string;
  cssClass: string;
  colors: {
    primary: string;
    accent: string;
    accentSecondary: string;
    destructive: string;
  };
  category: 'warm' | 'cool' | 'neutral' | 'high-contrast';
}

export const themes: ThemeColors[] = [
  {
    name: 'Cozy Pastel',
    description: 'Warm, welcoming lavender and peach tones',
    cssClass: 'theme-pastel',
    colors: {
      primary: '#8a6fc2',
      accent: '#f7b7a3',
      accentSecondary: '#c4e3cb',
      destructive: '#e67a8f'
    },
    category: 'warm'
  },
  {
    name: 'Ocean Blue',
    description: 'Professional, trustworthy blue palette',
    cssClass: 'theme-ocean',
    colors: {
      primary: '#3b82f6',
      accent: '#0ea5e9',
      accentSecondary: '#06b6d4',
      destructive: '#ef4444'
    },
    category: 'cool'
  },
  {
    name: 'Forest Green',
    description: 'Calming, nature-inspired greens',
    cssClass: 'theme-forest',
    colors: {
      primary: '#22c55e',
      accent: '#84cc16',
      accentSecondary: '#10b981',
      destructive: '#f97316'
    },
    category: 'cool'
  },
  {
    name: 'Sunset Warm',
    description: 'Energetic oranges and warm purples',
    cssClass: 'theme-sunset',
    colors: {
      primary: '#a855f7',
      accent: '#f97316',
      accentSecondary: '#fb923c',
      destructive: '#dc2626'
    },
    category: 'warm'
  },
  {
    name: 'Slate Professional',
    description: 'Modern, minimal grayscale with blue accents',
    cssClass: 'theme-slate',
    colors: {
      primary: '#475569',
      accent: '#64748b',
      accentSecondary: '#94a3b8',
      destructive: '#dc2626'
    },
    category: 'neutral'
  },
  {
    name: 'High Contrast',
    description: 'Maximum accessibility with bold colors',
    cssClass: 'theme-high-contrast',
    colors: {
      primary: '#000000',
      accent: '#0066cc',
      accentSecondary: '#008800',
      destructive: '#cc0000'
    },
    category: 'high-contrast'
  },
  {
    name: 'Cherry Blossom',
    description: 'Soft pinks and purples',
    cssClass: 'theme-cherry',
    colors: {
      primary: '#ec4899',
      accent: '#f472b6',
      accentSecondary: '#d946ef',
      destructive: '#dc2626'
    },
    category: 'warm'
  },
  {
    name: 'Arctic',
    description: 'Cool blues and icy tones',
    cssClass: 'theme-arctic',
    colors: {
      primary: '#0891b2',
      accent: '#06b6d4',
      accentSecondary: '#67e8f9',
      destructive: '#dc2626'
    },
    category: 'cool'
  }
];

export const defaultTheme = themes[0];

export function applyTheme(themeName: string, isDark: boolean = false): void {
  const theme = themes.find(t => t.name === themeName) || defaultTheme;
  const root = document.documentElement;
  // Remove all theme classes
  themes.forEach(t => root.classList.remove(t.cssClass));
  root.classList.add(theme.cssClass);
  // Toggle dark class
  root.classList.toggle('dark', isDark);
  // Save
  localStorage.setItem('accesstest-theme', themeName);
  localStorage.setItem('accesstest-dark-mode', isDark.toString());
}

export function getStoredTheme(): { themeName: string; isDark: boolean } {
  const themeName = localStorage.getItem('accesstest-theme') || defaultTheme.name;
  const isDark = localStorage.getItem('accesstest-dark-mode') === 'true';
  return { themeName, isDark };
}

export function getThemeByName(name: string) {
  return themes.find(t => t.name === name);
}

